"""CLI компилятора DL v2.1.

    dl parse <file>                 # показать AST
    dl eval <file>                  # вычислить и напечатать JSON (с валидацией)
    dl compile [file] [-o out]      # вычислить, проверить, записать файл
    dl schema <url> [-o file]       # скачать JSON Schema и сгенерировать .schema

Компиляция учитывает ``settings.dl`` рядом с исходником (``$.builds``:
``source``/``output``/``schema``). Если у сборки задан ``schema`` (URL или
путь), результат проверяется по классу из заголовка документа
(``json( $ ) => Config``) или по ``Config``; несоответствие — ``E011``.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .cache import DiskCache
from .evaluator import (
    Function,
    evaluate,
    evaluate_settings,
    evaluate_settings_file,
)
from .errors import DLError, FormatNotFoundError, ParseError
from .parser import parse
from .schema_gen import (
    download_schema,
    ensure_schema,
    generate_schema,
    load_schema,
    schema_filename,
)
from .report import BuildReporter, reset_reporter, set_reporter
from .resolver import reset_cache, reset_disk_cache, set_disk_cache
from .serializer import FORMATS, normalize_format, serialize
from .validator import validate_or_raise

SETTINGS_NAME = "settings.dl"

_URL_SCHEMES = {"http", "https", "ftp", "file"}


# ---------------------------------------------------------------------------
# Общие помощники
# ---------------------------------------------------------------------------


def _read_ast(path: Path) -> dict:
    return parse(path.read_text(encoding="utf-8"), str(path))


def _require_source(filename: str) -> Path:
    source = Path(filename)
    if not source.is_file():
        raise ParseError(f"E006 ParseError: file not found: {source}")
    return source


def context_for(source: Path) -> dict:
    """Контекст из ``settings.dl`` рядом с исходником (или пустой)."""
    candidate = source.parent / SETTINGS_NAME
    if candidate.is_file():
        return evaluate_settings_file(candidate)
    return {}


def _warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


@contextmanager
def _disk_cache(source: Path, enabled: bool = True) -> Iterator[DiskCache | None]:
    """Дисковый AST-кэш на время сборки: ``<каталог source>/.__cache__``.

    ``enabled=False`` (``--no-cache``) не создаёт и не читает кэш.
    """
    cache = DiskCache(source.parent) if enabled else None
    token = set_disk_cache(cache)
    try:
        yield cache
    finally:
        reset_disk_cache(token)


def _format_for(ast: dict, output: Path | None) -> str:
    """Формат: заголовок документа, иначе расширение output, иначе E005."""
    fmt = normalize_format(ast.get("format"))
    if fmt is None and output is not None and output.suffix:
        fmt = normalize_format(output.suffix)
    if fmt is None:
        raise FormatNotFoundError(
            "E005 FormatNotFoundError: document has no format and no output "
            "extension is available"
        )
    if fmt not in FORMATS:
        raise FormatNotFoundError(
            f"E005 FormatNotFoundError: unknown output format '{fmt}'"
        )
    return fmt


def _evaluate_document(ast: dict, source: Path, context: dict) -> dict:
    value = evaluate(ast, source.parent, context)
    if isinstance(value, Function):
        raise ParseError(
            f"E006 ParseError: {source.name} is a module; "
            "call it with arguments instead of compiling"
        )
    if not isinstance(value, dict):
        raise ParseError(
            f"E006 ParseError: {source.name} did not produce an object"
        )
    return value


# ---------------------------------------------------------------------------
# Схемы и builds
# ---------------------------------------------------------------------------


def is_url(reference: str) -> bool:
    """Похоже ли значение на URL (``https://``, ``file://``, ...)."""
    parsed = urllib.parse.urlparse(reference)
    return parsed.scheme in _URL_SCHEMES


def schema_classes(
    reference: str,
    base_dir: Path,
    force: bool = False,
) -> list[dict]:
    """Получить классы схемы из URL (кэш в ``base_dir``) или локального пути."""
    if is_url(reference):
        path = ensure_schema(reference, base_dir, force=force)
    else:
        path = Path(reference)
        if not path.is_absolute():
            path = base_dir / path
        path = path.resolve()
    return load_schema(path)


def find_build(builds: list[dict], source: Path) -> dict | None:
    """Найти build для исходника (сравнение абсолютных путей)."""
    target = source.resolve()
    for build in builds:
        raw = build.get("source")
        if not isinstance(raw, str):
            continue
        base = Path(build.get("_base_dir", "."))
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = base / candidate
        if candidate.resolve() == target:
            return build
    return None


def _attach_base(builds: list[dict], base_dir: Path) -> list[dict]:
    """Добавить ``_base_dir`` к сборкам (пути заданы относительно settings.dl)."""
    result = []
    for build in builds:
        if not isinstance(build, dict):
            continue
        item = dict(build)
        item["_base_dir"] = str(base_dir)
        result.append(item)
    return result


def _builds_from_context(context: dict, base_dir: Path) -> list[dict]:
    builds = context.get("builds") or []
    return _attach_base(builds, base_dir)


# ---------------------------------------------------------------------------
# Команды
# ---------------------------------------------------------------------------


def cmd_parse(args: argparse.Namespace) -> None:
    source = _require_source(args.filename)
    ast = _read_ast(source)
    print(json.dumps(ast, indent=2, ensure_ascii=False))


def cmd_eval(args: argparse.Namespace) -> None:
    source = _require_source(args.filename)
    use_cache = not getattr(args, "no_cache", False)
    with _disk_cache(source, use_cache):
        reset_cache()
        ast = _read_ast(source)
        context = (
            evaluate_settings(ast, source.parent)
            if source.name == SETTINGS_NAME
            else context_for(source)
        )

        if source.name == SETTINGS_NAME:
            value = context
        else:
            value = evaluate(ast, source.parent, context)

        if isinstance(value, Function):
            raise ParseError(
                f"E006 ParseError: {source.name} is a module; "
                "use dl parse or call it from a document"
            )

        _validate_if_schema(value, ast, source, context)
        print(json.dumps(value, ensure_ascii=False, indent=2))


def _validate_if_schema(
    value: dict,
    ast: dict,
    source: Path,
    context: dict,
) -> None:
    """Проверить значение, если рядом есть build со схемой."""
    settings = source.parent / SETTINGS_NAME
    if not settings.is_file():
        return
    builds = _builds_from_context(context, settings.parent)
    build = find_build(builds, source)
    if build is None or not build.get("schema"):
        return
    classes = schema_classes(
        str(build["schema"]), settings.parent, force=False
    )
    class_name = ast.get("schema") or "Config"
    validate_or_raise(value, class_name, classes)


def _schema_display(
    reference: str,
    base_dir: Path,
    reporter: BuildReporter,
) -> str:
    """Подпись схемы: имя кэш-файла для URL, путь — для локальной ссылки."""
    if is_url(reference):
        return schema_filename(reference)
    path = Path(reference)
    if not path.is_absolute():
        path = base_dir / path
    return reporter.display(path)


def _compile_one(
    source: Path,
    output: Path | None,
    context: dict,
    schema_reference: str | None = None,
    schema_base_dir: Path | None = None,
    progress: bool = True,
) -> Path:
    reporter = BuildReporter(enabled=progress)
    token = set_reporter(reporter)
    try:
        try:
            ast = _read_ast(source)
            fmt = _format_for(ast, output)
        except BaseException:
            reporter.start(source, output)
            raise

        target = output or source.with_suffix(f".{fmt}")
        reporter.start(source, target)

        reporter.file_start(source)
        error: BaseException | None = None
        try:
            value = _evaluate_document(ast, source, context)
        except BaseException as exc:
            error = exc
            raise
        finally:
            reporter.file_end(source, error=error)

        class_name = ast.get("schema") or "Config"
        if schema_reference:
            detail = _schema_display(
                schema_reference,
                schema_base_dir or source.parent,
                reporter,
            )
            reporter.stage("schema", "schema")
            try:
                classes = schema_classes(
                    schema_reference, schema_base_dir or source.parent
                )
            except BaseException as exc:
                reporter.stage_error("schema", str(exc))
                raise
            reporter.stage_done("schema", detail)

            reporter.stage("validate", "validate")
            try:
                validate_or_raise(value, class_name, classes)
            except BaseException as exc:
                reporter.stage_error("validate", str(exc))
                raise
            reporter.stage_done("validate", class_name)

        reporter.stage("write", "write")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(serialize(value, fmt), encoding="utf-8")
        except BaseException as exc:
            reporter.stage_error("write", str(exc))
            raise
        reporter.stage_done("write", reporter.display(target))

        print(f"Compiled: {source} → {target}")
        return target
    except BaseException as exc:
        reporter.fail(str(exc))
        raise
    finally:
        # --no-progress: дерево не печатается вовсе — stderr остаётся пустым
        # (в интерактивном режиме finish() ещё и останавливает Live).
        if progress:
            reporter.finish()
        reset_reporter(token)


def _compile_source(
    source: Path,
    output: Path | None,
    progress: bool,
) -> None:
    """Скомпилировать один файл с учётом его build (output/schema)."""
    context = context_for(source)
    settings = source.parent / SETTINGS_NAME
    build = None
    if settings.is_file():
        build = find_build(
            _builds_from_context(context, settings.parent), source
        )
    if build is not None:
        raw_output = build.get("output")
        if output is None and raw_output:
            output = (settings.parent / raw_output).resolve()
        _compile_one(
            source,
            output,
            context,
            schema_reference=build.get("schema"),
            schema_base_dir=settings.parent,
            progress=progress,
        )
    else:
        _compile_one(source, output, context, progress=progress)


def _compile_builds(settings: Path, progress: bool) -> None:
    """Скомпилировать все сборки из ``settings.dl``."""
    context = evaluate_settings_file(settings)
    builds = _builds_from_context(context, settings.parent)
    if not builds:
        raise ParseError(
            "E006 ParseError: settings.dl has no builds[] entries"
        )
    compiled = 0
    for build in builds:
        raw_source = build.get("source")
        raw_output = build.get("output")
        if not raw_source or not raw_output:
            _warn(
                "build entry without source/output skipped: "
                f"{raw_source!r} -> {raw_output!r}"
            )
            continue
        source = (settings.parent / raw_source).resolve()
        if not source.is_file():
            _warn(f"build source not found, skipped: {source}")
            continue
        target = (settings.parent / raw_output).resolve()
        # Сборки независимы: in-memory кэш не перетекает между ними.
        reset_cache()
        _compile_one(
            source,
            target,
            context,
            schema_reference=build.get("schema"),
            schema_base_dir=settings.parent,
            progress=progress,
        )
        compiled += 1
    if compiled == 0:
        _warn("no build entries were compiled")


def cmd_compile(args: argparse.Namespace) -> None:
    output = Path(args.output) if args.output else None
    progress = not getattr(args, "no_progress", False)
    use_cache = not getattr(args, "no_cache", False)

    if args.filename:
        source = _require_source(args.filename)
        with _disk_cache(source, use_cache):
            reset_cache()
            _compile_source(source, output, progress)
        return

    settings = Path.cwd() / SETTINGS_NAME
    if settings.is_file():
        with _disk_cache(settings, use_cache):
            reset_cache()
            _compile_builds(settings, progress)
        return

    source = Path.cwd() / "configuration.dl"
    if not source.is_file():
        raise ParseError(
            "E006 ParseError: neither settings.dl nor configuration.dl found"
        )
    with _disk_cache(source, use_cache):
        reset_cache()
        _compile_one(source, output, {}, progress=progress)


def cmd_schema(args: argparse.Namespace) -> None:
    destination = (
        Path(args.output)
        if args.output
        else Path.cwd() / schema_filename(args.url)
    )

    if destination.is_file() and not args.force:
        print(
            f"Schema exists: {destination} (use --force to regenerate)",
            file=sys.stderr,
        )
        return

    data = download_schema(args.url)
    notes: list[str] = []
    text = generate_schema(data, args.url, notes)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")

    print(f"Generated: {destination}")
    if notes:
        print("not converted:", file=sys.stderr)
        for note in notes:
            print(f"  - {note}", file=sys.stderr)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dl",
        description=(
            "DL language compiler — parse, evaluate, validate and compile "
            "configuration documents"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile DL file (settings.dl builds or configuration.dl)",
    )
    compile_parser.add_argument(
        "filename", nargs="?", help="DL file to compile"
    )
    compile_parser.add_argument(
        "-o", "--output", help="Output file (format by header or extension)"
    )
    compile_parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Do not print the build tree at all (stderr stays empty)",
    )
    compile_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not read or write the on-disk AST cache (.__cache__)",
    )
    compile_parser.set_defaults(func=cmd_compile)

    parse_parser = subparsers.add_parser(
        "parse", help="Parse DL file (show AST)"
    )
    parse_parser.add_argument("filename", help="DL file to parse")
    parse_parser.set_defaults(func=cmd_parse)

    eval_parser = subparsers.add_parser(
        "eval", help="Evaluate DL file and print JSON (validates if schema is available)"
    )
    eval_parser.add_argument("filename", help="DL file to evaluate")
    eval_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not read or write the on-disk AST cache (.__cache__)",
    )
    eval_parser.set_defaults(func=cmd_eval)

    schema_parser = subparsers.add_parser(
        "schema", help="Download JSON Schema and generate a DL .schema file"
    )
    schema_parser.add_argument("url", help="URL of the JSON Schema")
    schema_parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: <name>.schema in the current directory)",
    )
    schema_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if the output file exists",
    )
    schema_parser.set_defaults(func=cmd_schema)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    try:
        args.func(args)
    except DLError as error:
        print(str(error), file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"E002 ModuleNotFoundError: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
