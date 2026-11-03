"""CLI компилятора DL v2.2.

    dl parse <file>                 # показать AST
    dl eval <file>                  # вычислить и напечатать JSON
    dl build [file]                 # собрать конфигурацию с outputs (Nix-модель)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .cache import DiskCache
from .evaluator import (
    Function,
    call_value,
    evaluate,
    evaluate_settings,
    evaluate_settings_file,
)
from .errors import DLError, FormatNotFoundError, ParseError
from .flake import build_to_files
from .parser import parse
from .report import BuildReporter, reset_reporter, set_reporter
from .resolver import reset_cache, reset_disk_cache, set_disk_cache
from .serializer import FORMATS, normalize_format

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
        if ast.get("kind") == "config":
            # Модульный режим: config-документ вызывается явно
            value = call_value(value, [], None, context, source.parent)
        else:
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
# Builds
# ---------------------------------------------------------------------------


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
            if ast.get("kind") == "config":
                # Модульный режим: config-документ вызывается явно
                value = call_value(value, [], None, context, source.parent)
            else:
                raise ParseError(
                    f"E006 ParseError: {source.name} is a module; "
                    "use dl parse or call it from a document"
                )

        print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_build(args: argparse.Namespace) -> None:
    """Команда `dl build`: Nix-модель с outputs."""
    progress = not getattr(args, "no_progress", False)
    use_cache = not getattr(args, "no_cache", False)

    if args.filename:
        source = _require_source(args.filename)
    else:
        source = Path.cwd() / "configuration.dl"
        if not source.is_file():
            raise ParseError(
                "E006 ParseError: configuration.dl not found"
            )

    with _disk_cache(source, use_cache):
        reset_cache()
        reporter = BuildReporter(enabled=progress)
        token = set_reporter(reporter)
        try:
            reporter.start(source, source.parent / "outputs")
            written = build_to_files(source, source.parent)
            for path in written:
                reporter.stage_done("write", reporter.display(path))
            reporter.finish()
            print(f"Build complete: {len(written)} output(s) written")
        except BaseException as exc:
            reporter.fail(str(exc))
            raise
        finally:
            reset_reporter(token)





# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dl",
        description=(
            "DL language compiler — parse, evaluate and compile "
            "configuration documents"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    build_parser_sub = subparsers.add_parser(
        "build", help="Build configuration with outputs (Nix-like model)"
    )
    build_parser_sub.add_argument(
        "filename", nargs="?", help="configuration.dl file to build"
    )
    build_parser_sub.add_argument(
        "--no-progress",
        action="store_true",
        help="Do not print the build tree at all (stderr stays empty)",
    )
    build_parser_sub.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not read or write the on-disk AST cache (.__cache__)",
    )
    build_parser_sub.set_defaults(func=cmd_build)

    parse_parser = subparsers.add_parser(
        "parse", help="Parse DL file (show AST)"
    )
    parse_parser.add_argument("filename", help="DL file to parse")
    parse_parser.set_defaults(func=cmd_parse)

    eval_parser = subparsers.add_parser(
        "eval", help="Evaluate DL file and print JSON"
    )
    eval_parser.add_argument("filename", help="DL file to evaluate")
    eval_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not read or write the on-disk AST cache (.__cache__)",
    )
    eval_parser.set_defaults(func=cmd_eval)

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
