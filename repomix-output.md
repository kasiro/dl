This file is a merged representation of the entire codebase, combined into a single document by Repomix.
The content has been processed where security check has been disabled.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Security check has been disabled - content may contain sensitive information
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
dl/
  __init__.py
  cache.py
  cli.py
  errors.py
  evaluator.py
  grammar.lark
  merger.py
  parser.py
  report.py
  resolver.py
  serializer.py
  validator.py
examples/
  agents/
    agents.dl
  mcp/
    create-server.dl
    servers.dl
  modules/
    agents.dl
    def.dl
    mcp.dl
    permissions.dl
    providers.dl
    runtime.dl
  providers/
    func/
      createmodel.dl
      makeoptions.dl
    createprovider.dl
    deepseek-proxy.dl
    offprovider.dl
  configuration.dl
  opencode.json
  settings.dl
pyproject.toml
spec.md
TODO.md
```

# Files

## File: examples/providers/func/createmodel.dl
````
( $, name ) => {
    "{name}": {
        name: "{name}";
    }
}
````

## File: examples/providers/func/makeoptions.dl
````
( $, port, host: "localhost" ) => {
    baseURL: "http://{host}:{port}/v1";
}
````

## File: examples/providers/offprovider.dl
````
( $, name, npm, baseurl, options: {}, models ) => {
    npm: npm;
    name: "{name}";
    options: {
        baseURL: baseurl;
        ...options;
    };
    models: models;
}
````

## File: TODO.md
````markdown
# переделать
- в settings.dl в $.builds добавить возможность указывать несколько файлов:
```examples/settings.dl
( $ ) => {
    $.schema: "https://opencode.ai/config.json";
    $.builds: [
        {
            source: "./configuration.dl";
            output: [
              "/home/kasiro/.config/opencode/opencode.json",
              "./opencode.json"
            ]; // пишется в оба.
        }
    ];
    $.npm.openaicomp: "@ai-sdk/openai-compatible";
    $.npm.voidrot: "@voidrot/openai-featherless-compatible";
}
```
- добавить условные операторы if, elif, else, return, циклы, тернарный опреатор. тернаный или:
```examples/providers/models/func/createmodel.dl
// optname? -> ? - необязательная/опциональная переменная
( $, name, optname? ) => {
    {name}: {
        name: {name || optname}; // если optname не передан берём name.
    }
}
```
- добавить нормальный traseback ошибок при ошибках синтаксиса. а то сейчас непонятно.
```examples/modules/providers.dl
( $ ) => {
    // импортируем через for:
    // создаём список:
    let providers_ = $.glob('../providers/*.dl');
    for path in providers_:
        import ../providers/{path.basename()} as {path.basename().noext};
    // let offprovider = import ../providers/offprovider.dl;
    // let deepseek = import ../providers/deepseek-proxy.dl;
    // let createprovider = import ../providers/createprovider.dl;
    // let createmodel = import ../providers/func/createmodel.dl;

    // createprovider(key, {
    // тоже самое что и:
    // localproxy: createprovider(localproxy, {
    provider: {
        createprovider('localproxy', {
            npm: $.npm.openaicomp;
            port: 9625;
            models: {
                createmodel("free-gemini-2.5-pro");
                createmodel("free-minimax-m2.7");
                createmodel("free-claude-haiku-4-5-20251001");
                createmodel("free-gemini-2.5-flash");
                createmodel("free-qwen3.5-plus");
                createmodel("free-qwen3.5-flash");
                createmodel("free-minimax-m2.5");
                createmodel("free-gemini-2.5-flash-lite");
                createmodel("free-gemini-3-flash-preview");
            };
        });
        deepseek('deepseek-proxy', {
            npm: $.npm.voidrot;
            port: 9626;
            models: {
                createmodel("deepseek/deepseek-v4.1-flash");
            };
        });
        createprovider('zen-free', {
            npm: $.npm.openaicomp;
            port: 9877;
            models: {
                createmodel("muse-spark-1.3-contributor-free");
                createmodel("muse-spark-1.2-contributor-free");
                createmodel("mimo-v2.5-free");
                createmodel("mimo-v2.6-flash-free");
                createmodel("ling-3.0-flash-fin-free");
                createmodel("nemotron-3-ultra-free");
                createmodel("nemotron-3.5-lightning-free");
                createmodel("big-pickle");
                createmodel("space-bunny-free");
                createmodel("deepseek-v4.1-flash-free");
            };
        });
        offprovider('anymodel', {
            npm: $.npm.openaicomp;
            baseurl: 'https://anymodel.org/v1';
            options: {
                apiKey: 'sk-dc9d4b7df36ba555-eldltg-e377fcc3';
            };
            models: {
                createmodel("am/gpt-oss-20b");
                createmodel("am/llama-3.2-11b-vision-instruct");
                createmodel("am/laguna-xs-2.1");
                createmodel("am/nemotron-3-nano-omni-30b-a3b-reasoning");
                createmodel("am/nemotron-3-ultra-550b-a55b");

                createmodel("ds/deepseek-v4-flash");
                createmodel("glm/glm-4.7");
                createmodel("glm/glm-5.3-flash");
                createmodel("kmc/k2.6");
                createmodel("xai/grok-4.20-0309-reasoning");
            };
        });
    };
}
```
- нужен многострочный комментарий: ###...### (как в python)
- комментарий на # а не на //
```examples/providers/func/createmodel.dl
( $, name: Option[str | list] ) => {
    if name is str {
        {name}: {
            name: {name};
        }
    } else {
        for el in name {
            {el}: {
                name: {el};
            }
        }
    }
}
```
````

## File: dl/__init__.py
````python
"""DL v2.1 — компилятор конфигураций.

Публичный API:

    parse(source, filename="<input>") -> dict
    evaluate(ast, base_dir, context=None) -> dict | Function
    merge(base, override) -> dict
    serialize(value, format) -> str

Этап 3 (схемы и валидация):

    generate_schema(json_schema, source_url) -> str
    download_schema(url, timeout=30) -> dict
    ensure_schema(url, dest_dir, force=False) -> Path
    load_schema(path) -> list[dict]
    validate(value, class_name, classes, path="") -> list[str]
    validate_or_raise(value, class_name, classes, path="") -> None
"""

from .evaluator import evaluate
from .merger import merge
from .parser import parse
from .schema_gen import (
    download_schema,
    ensure_schema,
    generate_schema,
    load_schema,
)
from .serializer import serialize
from .validator import validate, validate_or_raise

__all__ = [
    "parse",
    "evaluate",
    "merge",
    "serialize",
    "generate_schema",
    "download_schema",
    "ensure_schema",
    "load_schema",
    "validate",
    "validate_or_raise",
]
__version__ = "0.1.0"
````

## File: dl/cli.py
````python
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
````

## File: dl/errors.py
````python
"""Ошибки DL v2.1.

Каждый класс несёт код из спецификации (раздел 9) в атрибуте ``code`` и в
тексте сообщения. Имена классов повторяют раздел 9.1; ``ModuleNotFoundError``
намеренно перекрывает встроенное исключение — это ошибка DL (E002).
"""

from __future__ import annotations


class DLError(Exception):
    """Базовый класс ошибок DL."""

    code = "E000"
    name = "DLError"


class SyntaxError(DLError):  # noqa: A001 - имя из спецификации
    code = "E001"
    name = "SyntaxError"


class ModuleNotFoundError(DLError):  # noqa: A001 - имя из спецификации
    code = "E002"
    name = "ModuleNotFoundError"


class ConflictError(DLError):
    code = "E003"
    name = "ConflictError"


class CircularImportError(DLError):
    code = "E004"
    name = "CircularImportError"


class FormatNotFoundError(DLError):
    code = "E005"
    name = "FormatNotFoundError"


class ParseError(DLError):
    code = "E006"
    name = "ParseError"


class NotOverridableKey(DLError):
    code = "E007"
    name = "NotOverridableKey"


class DLContextError(DLError):
    code = "E008"
    name = "NoContext"


class UnknownParameterError(DLError):
    code = "E009"
    name = "UnknownParameter"


class MissingParameterError(DLError):
    code = "E010"
    name = "MissingParameter"


class TypeMismatchError(DLError):
    code = "E011"
    name = "TypeMismatch"


class SchemaFetchError(DLError):
    code = "E012"
    name = "SchemaFetchError"


class SchemaGenerateError(DLError):
    code = "E013"
    name = "SchemaGenerateError"


class GlobParameterizedModule(DLError):
    code = "E014"
    name = "GlobParameterizedModule"
````

## File: dl/evaluator.py
````python
"""Вычисление AST DL v2.1.

Публичный API:

    evaluate(ast, base_dir, context=None) -> dict | Function | dict-schema
    evaluate_file(path, context=None)
    evaluate_settings(ast, base_dir)
    evaluate_settings_file(path)
    call_value(fn, positional, named, ctx=None, base_dir=None)

Семантика (раздел 5–7 спецификации):

* документ ``config`` вычисляется сразу в словарь;
* документ ``module`` возвращается как :class:`Function` (даже если параметров
  нет — ``()``);
* документ ``schema`` возвращает описание классов для этапа 3;
* ``$`` (контекст) объявляется только параметром ``$``; обращение к ``$`` без
  него — ``E008``;
* контекст передаётся неявно по всей цепочке вызовов;
* блок выполняется сверху вниз: ``let`` — в scope, поля — с ``W001``/``E003``,
  spread и вызовы-инструкции — с переопределением (без конфликта).

Одно уточнение контракта: модуль **без параметров вообще** (``() =>``) при
импорте вызывается сразу — иначе ``models: import ./models/{name}.dl``
возвращал бы функцию, а не словарь моделей. Модули с объявленными параметрами
(в том числе с одним ``$``) остаются значениями-функциями.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import (
    DLContextError,
    GlobParameterizedModule,
    MissingParameterError,
    ParseError,
    UnknownParameterError,
)
from .merger import deep_merge, set_path
from .resolver import resolve_import

# ---------------------------------------------------------------------------
# Значения
# ---------------------------------------------------------------------------


@dataclass
class Function:
    """Модуль с параметрами: сигнатура + тело + каталог для импортов."""

    params: list[dict]
    body: list[dict]
    base_dir: Path
    name: str | None = None

    def __repr__(self) -> str:  # компактно в отчётах/ошибках
        names = ", ".join(param["name"] for param in self.params)
        return f"Function({names})"


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------


def as_path(base_dir: Path | str | None) -> Path:
    """Привести base_dir к абсолютному Path."""
    if base_dir is None:
        return Path.cwd()
    return Path(base_dir).resolve()


def _to_str(value: Any) -> str:
    """Приведение значения к строке для интерполяции."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def interp_segment(segment: str, scope: dict, ctx: dict | None) -> str:
    """Интерполировать сегмент точечного пути (ключ в кавычках: ``"{name}"``)."""
    if "{" not in segment:
        return segment
    from .parser import _split_interpolation

    parts = _split_interpolation(segment)
    if len(parts) == 1 and parts[0][0] == "lit":
        return segment
    chunks: list[str] = []
    for part in parts:
        if part[0] == "lit":
            chunks.append(str(part[1]))
        else:
            ref = part[1]
            assert isinstance(ref, list)
            chunks.append(_to_str(_lookup_ref(ref, scope, ctx)))
    return "".join(chunks)


def _has_context(params: list[dict]) -> bool:
    return any(param["name"] == "$" for param in params)


def _user_params(params: list[dict]) -> list[dict]:
    """Параметры без ``$`` — они участвуют в позиционном/именованном вызове."""
    return [param for param in params if param["name"] != "$"]


def _lookup_ref(path: list[str], scope: dict, ctx: dict | None) -> Any:
    """Разрешить путь ``ref``: ``$`` → контекст, иначе — scope."""
    if path[0] == "$":
        if "$" not in scope:
            raise DLContextError(
                "E008 NoContext: '$' used without context in signature"
            )
        value = scope["$"]
        rest = path[1:]
    else:
        name = path[0]
        if name not in scope:
            raise ParseError(
                f"E006 ParseError: undefined reference '{name}'"
            )
        value = scope[name]
        rest = path[1:]

    for segment in rest:
        if not isinstance(value, dict):
            raise ParseError(
                f"E006 ParseError: cannot access '{segment}' "
                f"in non-object value {value!r}"
            )
        if segment not in value:
            raise ParseError(
                f"E006 ParseError: undefined reference "
                f"'{'.'.join(path)}' (missing '{segment}')"
            )
        value = value[segment]
    return value


# ---------------------------------------------------------------------------
# Вызовы
# ---------------------------------------------------------------------------


def call_value(
    fn: Function,
    positional: list[Any],
    named: dict[str, Any] | None,
    ctx: dict | None = None,
    base_dir: Path | str | None = None,
) -> dict:
    """Вызвать функцию модуля.

    ``positional``/``named`` — уже вычисленные значения аргументов.
    ``$`` в именованных аргументах не передаётся: контекст подставляется
    неявно и распространяется по цепочке вызовов.
    """
    if not isinstance(fn, Function):
        raise ParseError("E006 ParseError: value is not a function")

    params = fn.params or []
    rest = _user_params(params)
    scope: dict[str, Any] = {}

    if _has_context(params):
        if ctx is None:
            ctx = {}
        scope["$"] = ctx

    # Позиционные — по порядку параметров после `$`.
    if len(positional) > len(rest):
        raise UnknownParameterError(
            f"E009 UnknownParameter: too many positional arguments "
            f"({len(positional)} for {len(rest)} parameters)"
        )
    for param, value in zip(rest, positional):
        scope[param["name"]] = value

    # Именованные — по имени.
    if named:
        by_name = {param["name"]: param for param in rest}
        for key, value in named.items():
            if key == "$":
                raise UnknownParameterError(
                    "E009 UnknownParameter: '$' is passed implicitly"
                )
            param = by_name.get(key)
            if param is None:
                raise UnknownParameterError(
                    f"E009 UnknownParameter: unknown parameter '{key}'"
                )
            if key in scope:
                raise ParseError(
                    f"E006 ParseError: parameter '{key}' passed twice"
                )
            scope[key] = value

    # Дефолты и опциональные параметры.
    module_dir = as_path(fn.base_dir or base_dir)
    for param in rest:
        name = param["name"]
        if name in scope:
            continue
        if param["default"] is not None:
            scope[name] = eval_expr(param["default"], scope, ctx, module_dir)
        elif param["optional"]:
            scope[name] = None
        else:
            raise MissingParameterError(
                f"E010 MissingParameter: missing required parameter '{name}'"
            )

    return eval_block(fn.body or [], scope, ctx, module_dir)


# ---------------------------------------------------------------------------
# Блоки и выражения
# ---------------------------------------------------------------------------


def eval_block(
    body: list[dict],
    scope: dict,
    ctx: dict | None,
    base_dir: Path,
) -> dict:
    """Выполнить блок сверху вниз и вернуть объект-результат."""
    result: dict[str, Any] = {}

    for stmt in body:
        kind = stmt["kind"]

        if kind == "let":
            scope[stmt["name"]] = eval_expr(stmt["value"], scope, ctx, base_dir)

        elif kind == "field":
            value = eval_expr(stmt["value"], scope, ctx, base_dir)
            if stmt.get("optional") and value is None:
                continue
            path = stmt["path"]
            if path and path[0] == "$":
                path = ["$", *(interp_segment(s, scope, ctx) for s in path[1:])]
            else:
                path = [interp_segment(segment, scope, ctx) for segment in path]
            if path and path[0] == "$":
                if "$" not in scope:
                    raise DLContextError(
                        "E008 NoContext: '$' used without context in signature"
                    )
                if ctx is None:
                    raise DLContextError(
                        "E008 NoContext: context is not available for writing"
                    )
                set_path(ctx, path[1:], value)
            else:
                set_path(result, path, value)

        elif kind == "spread":
            value = eval_expr(stmt["value"], scope, ctx, base_dir)
            if not isinstance(value, dict):
                raise ParseError(
                    f"E006 ParseError: spread expects an object, "
                    f"got {type(value).__name__}"
                )
            deep_merge(result, value)

        elif kind == "expr":
            value = eval_expr(stmt["value"], scope, ctx, base_dir)
            if not isinstance(value, dict):
                raise ParseError(
                    f"E006 ParseError: expression result must be an object, "
                    f"got {type(value).__name__}"
                )
            deep_merge(result, value)

        else:  # pragma: no cover - защита от расширения AST
            raise ParseError(f"E006 ParseError: unknown statement '{kind}'")

    return result


def eval_expr(
    node: dict,
    scope: dict,
    ctx: dict | None,
    base_dir: Path,
) -> Any:
    """Вычислить выражение."""
    kind = node["kind"]

    if kind == "string":
        chunks: list[str] = []
        for part in node["parts"]:
            if part[0] == "lit":
                chunks.append(part[1])
            else:
                chunks.append(_to_str(_lookup_ref(part[1], scope, ctx)))
        return "".join(chunks)

    if kind in {"int", "float", "bool"}:
        return node["value"]

    if kind == "null":
        return None

    if kind == "array":
        return [eval_expr(item, scope, ctx, base_dir) for item in node["items"]]

    if kind == "object":
        return eval_block(node["body"], scope, ctx, base_dir)

    if kind == "call":
        name = node["name"]
        if name not in scope:
            raise ParseError(f"E006 ParseError: unknown function '{name}'")
        fn = scope[name]
        if not isinstance(fn, Function):
            raise ParseError(
                f"E006 ParseError: '{name}' is not a function "
                f"({type(fn).__name__})"
            )
        positional = [
            eval_expr(arg, scope, ctx, base_dir)
            for arg in node["positional"]
        ]
        named_body = node.get("named")
        named = (
            eval_block(named_body, scope, ctx, base_dir)
            if named_body is not None
            else None
        )
        return call_value(fn, positional, named, ctx, base_dir)

    if kind == "import":
        path = eval_import_path(node, scope, ctx)
        is_glob = node.get("glob", False)
        if is_glob:
            from .resolver import resolve_glob_import
            value = resolve_glob_import(path, base_dir, ctx)
        else:
            value = resolve_import(path, base_dir, ctx)
        # Модуль без параметров вообще (``() =>``) — значение, а не функция:
        # так ``models: import ./models/{name}.dl`` даёт словарь моделей.
        # Модуль с ``$`` остаётся функцией (контекст передаётся при вызове).
        if isinstance(value, Function) and not value.params:
            return call_value(value, [], None, ctx, base_dir)
        return value

    if kind == "ref":
        return _lookup_ref(node["path"], scope, ctx)

    raise ParseError(f"E006 ParseError: unknown expression '{kind}'")


def eval_import_path(
    node: dict,
    scope: dict,
    ctx: dict | None,
) -> str:
    """Собрать путь импорта с интерполяцией ``{expr}``."""
    parts = node.get("parts")
    if not parts:
        return node["path"]
    chunks: list[str] = []
    for part in parts:
        if part[0] == "lit":
            chunks.append(part[1])
        else:
            chunks.append(_to_str(_lookup_ref(part[1], scope, ctx)))
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Документы
# ---------------------------------------------------------------------------


def evaluate(
    ast: dict,
    base_dir: Path | str | None = None,
    context: dict | None = None,
) -> Any:
    """Вычислить документ DL.

    ``config`` → dict, ``module`` → :class:`Function`, ``schema`` → описание
    классов (``{"kind": "schema", "classes": [...]}``).
    """
    directory = as_path(base_dir)
    kind = ast.get("kind")

    if kind == "config":
        params = ast.get("params") or []
        fn = Function(params=params, body=ast.get("body") or [], base_dir=directory)
        return call_value(fn, [], None, context, directory)

    if kind == "module":
        return Function(
            params=ast.get("params") or [],
            body=ast.get("body") or [],
            base_dir=directory,
        )

    if kind == "schema":
        return {"kind": "schema", "classes": list(ast.get("body") or [])}

    raise ParseError(f"E006 ParseError: unknown document kind '{kind}'")


def evaluate_file(path: Path | str, context: dict | None = None) -> Any:
    """Прочитать и вычислить файл DL."""
    from .parser import parse

    source = Path(path)
    ast = parse(source.read_text(encoding="utf-8"), str(source))
    return evaluate(ast, source.parent, context)


def evaluate_settings(ast: dict, base_dir: Path | str | None = None) -> dict:
    """Вычислить ``settings.dl`` и вернуть контекст.

    Модуль вызывается с пустым контекстом; инструкции ``$.x: value`` пишут в
    него, поэтому результатом является сам контекст.
    """
    directory = as_path(base_dir)
    value = evaluate(ast, directory)
    if not isinstance(value, Function):
        raise ParseError(
            "E006 ParseError: settings document must be a module with '$'"
        )
    ctx: dict = {}
    call_value(value, [], None, ctx, directory)
    return ctx


def evaluate_settings_file(path: Path | str) -> dict:
    """Прочитать и вычислить ``settings.dl``."""
    from .parser import parse

    source = Path(path)
    ast = parse(source.read_text(encoding="utf-8"), str(source))
    return evaluate_settings(ast, source.parent)


__all__ = [
    "Function",
    "call_value",
    "eval_block",
    "eval_expr",
    "evaluate",
    "evaluate_file",
    "evaluate_settings",
    "evaluate_settings_file",
]
````

## File: dl/grammar.lark
````
// DL v2.1 — грамматика (LALR)
//
// Структура:
//   1. Документ: config / module / schema
//   2. Параметры
//   3. Блоки и инструкции
//   4. Выражения
//   5. Схема: классы, поля, типы
//   6. Терминалы

start: config_doc
     | module_doc
     | schema_doc

// ─────────────────────────────── 1. Документ ───────────────────────────────

config_doc: FORMAT param_block "=>" schema_name block  -> config_with_schema
          | FORMAT param_block "=>" block              -> config_plain
          | FORMAT "=>" schema_name block              -> config_bare_with_schema
          | FORMAT "=>" block                          -> config_bare

module_doc: param_block "=>" block

schema_doc: "schema" "=>" schema_block

schema_name: IDENT

// ─────────────────────────────── 2. Параметры ──────────────────────────────

param_block: "(" param_list? ")"
param_list: param ("," param)*

param: DOLLAR              -> param_context
     | IDENT               -> param_plain
     | IDENT "?"           -> param_optional
     | IDENT ":" expr      -> param_default

// ───────────────────────── 3. Блоки и инструкции ───────────────────────────
//
// Необязательная `;` перед `}` решена праворекурсивным списком:
//   stmt_list: stmt ";" stmt_list | stmt ";" | stmt
// После `;` смотрится следующий токен: `}` — это завершающая `;`,
// начало инструкции — продолжение списка. Конфликтов нет.

block: "{" "}"
     | "{" stmt_list "}"

stmt_list: stmt ";" stmt_list   -> stmts_more
         | stmt ";"             -> stmts_trailing
         | stmt                 -> stmts_single

stmt: let_stmt
    | spread_stmt
    | field_stmt
    | call_stmt

let_stmt: "let" IDENT "=" expr
spread_stmt: "..." expr

field_stmt: field_path ":" expr       -> field
          | field_path "=" expr       -> field
          | field_path "?" ":" expr   -> field_optional

call_stmt: call

field_path: (DOLLAR | IDENT | STRING) ("." path_seg)*
path_seg: IDENT
        | STRING

// ─────────────────────────────── 4. Выражения ──────────────────────────────

expr: STRING          -> string_lit
    | NUMBER          -> int_lit
    | FLOAT           -> float_lit
    | "true"          -> true_lit
    | "false"         -> false_lit
    | "null"          -> null_lit
    | array
    | object
    | call
    | import_expr
    | ref

// Запятые в массиве необязательны; элементы могут разделяться пробелом.
array: "[" "]"                       -> array_empty
     | "[" expr_list "]"             -> array

expr_list: expr "," expr_list   -> expr_list_more
         | expr expr_list       -> expr_list_space
         | expr ","             -> expr_list_trailing
         | expr                 -> expr_list_single

object: block

// Вызов: позиционные аргументы через запятую; объект последним аргументом
// трактуется как именованные аргументы (разбор — в трансформере).
call: IDENT "(" ")"                     -> call_empty
    | IDENT "(" args ")"                -> call

args: expr "," args     -> args_more
    | expr ","          -> args_trailing
    | expr              -> args_single

import_expr: "import" PATH

ref: ref_path
ref_path: (DOLLAR | IDENT) ("." path_seg)*

// ───────────────────────── 5. Схема: классы и типы ─────────────────────────

schema_block: "{" class_decl* "}"

class_decl: "class" IDENT "{" class_field* "}" ";"?        -> class_plain
          | doc "class" IDENT "{" class_field* "}" ";"?    -> class_doc

class_field: field_name ":" type ["=" expr] ";"?             -> class_field_plain
           | field_name "?" ":" type ["=" expr] ";"?         -> class_field_optional
           | doc field_name ":" type ["=" expr] ";"?         -> class_field_doc_plain
           | doc field_name "?" ":" type ["=" expr] ";"?     -> class_field_doc_optional

obj_field: field_name ":" type ["=" expr] ";"?               -> obj_field_plain
         | field_name "?" ":" type ["=" expr] ";"?           -> obj_field_optional
         | doc field_name ":" type ["=" expr] ";"?           -> obj_field_doc_plain
         | doc field_name "?" ":" type ["=" expr] ";"?       -> obj_field_doc_optional

doc: DOC_COMMENT+

field_name: IDENT
          | STRING

type: type_atom ("|" type_atom)*

type_atom: "string"    -> t_string
         | "integer"   -> t_integer
         | "number"    -> t_number
         | "float"     -> t_float
         | "boolean"   -> t_boolean
         | "null"      -> t_null
         | "any"       -> t_any
         | array_type
         | map_type
         | enum_type
         | object_type
         | named_type

array_type: "[" type "]"
map_type: "map" "<" type ">"

enum_type: "enum" "{" enum_val ("|" enum_val)* "}"
enum_val: STRING   -> enum_string
        | NUMBER   -> enum_number
        | "true"   -> enum_true
        | "false"  -> enum_false
        | "null"   -> enum_null

object_type: "{" obj_field* "}"

named_type: IDENT

// ─────────────────────────────── 6. Терминалы ──────────────────────────────

FORMAT: "json" | "toml" | "yaml"
DOLLAR: "$"

// Путь импорта: ./x.dl, ../x.dl, /abs/x.dl; в сегментах допустима
// интерполяция {expr}. Звёздочка * разрешена только в последнем сегменте
// для glob-импорта (например, ./dir/*.dl). Разбор на части — в трансформере.
PATH: /(?:\.{1,2})?\/[A-Za-z0-9_.\-{}\/@*]*\.dl/

IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
STRING: /"([^"\\]|\\.)*"/ | /'([^'\\]|\\.)*'/
NUMBER: /-?[0-9]+/
FLOAT: /-?[0-9]+\.[0-9]+/

DOC_COMMENT: /\/\/\/[^\n]*/
COMMENT: /\/\/(?!\/)[^\n]*/

%import common.WS
%ignore WS
%ignore COMMENT
````

## File: dl/merger.py
````python
"""Слияние объектов, точечные пути и предупреждения DL v2.1.

Три режима:

* :func:`merge` — строгое слияние (для обычных полей блока): одинаковые
  значения дают ``W001``, разные — ``E003`` (раздел 6.4);
* :func:`deep_merge` — слияние с переопределением (spread и вызовы-инструкции,
  раздел 6.3): конфликтов не порождает;
* :func:`set_path` — запись по точечному пути с созданием промежуточных
  объектов; не-объект на промежуточном сегменте — ``E003`` (раздел 3.4).
"""

from __future__ import annotations

import logging
from typing import Any

from .errors import ConflictError

log = logging.getLogger("dl")


def _copy_value(value: Any) -> Any:
    """Копировать контейнеры, сохраняя прочие значения (например, Function).

    Function неизменяема, а ссылки на объекты из scope не должны разделяться
    между ветками результата: изменение одного словаря не должно задевать
    другой.
    """
    if isinstance(value, dict):
        return {key: _copy_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_value(item) for item in value]
    return value


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else str(key)


def _warn_duplicate(path: str) -> None:
    log.warning("W001 DuplicateKey: %s has same value", path)


def _format_path(path: str) -> str:
    return path or "<root>"


def merge(base: dict, override: dict, path: str = "") -> dict:
    """Строгое рекурсивное слияние.

    Одинаковое значение — ``W001`` и тихое слияние, разное — ``E003``.
    Возвращает новый словарь (``base`` не изменяется).
    """
    result = _copy_value(base)
    for key, value in override.items():
        full = _join(path, key)
        if key not in result:
            result[key] = _copy_value(value)
            continue
        existing = result[key]
        if isinstance(existing, dict) and isinstance(value, dict):
            result[key] = merge(existing, value, full)
        elif existing == value:
            _warn_duplicate(full)
        else:
            raise ConflictError(
                f"E003 ConflictError: conflicting values at {full}: "
                f"{existing!r} vs {value!r}"
            )
    return result


def deep_merge(target: dict, source: dict, path: str = "") -> dict:
    """Слить ``source`` в ``target`` с переопределением (без W001/E003).

    Используется для ``...expr`` и вызовов-инструкций (раздел 6.3).
    """
    for key, value in source.items():
        full = _join(path, key)
        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, dict)
        ):
            deep_merge(target[key], value, full)
        else:
            target[key] = _copy_value(value)
    return target


def set_path(
    target: dict,
    path: list[str],
    value: Any,
    *,
    override: bool = False,
    path_prefix: str = "",
) -> None:
    """Записать ``value`` в ``target`` по точечному пути ``path``.

    Промежуточные объекты создаются неявно; если сегмент уже занят не-объектом
    — ``E003``. На последнем сегменте: ``override=True`` молча переопределяет,
    иначе одинаковое значение даёт ``W001``, разное — ``E003``.
    """
    if not path:
        raise ConflictError("E003 ConflictError: empty field path")

    current = target
    walked = path_prefix
    for segment in path[:-1]:
        walked = _join(walked, segment)
        if segment not in current:
            current[segment] = {}
        elif not isinstance(current[segment], dict):
            raise ConflictError(
                f"E003 ConflictError: {walked} is not an object "
                f"({current[segment]!r})"
            )
        current = current[segment]

    last = path[-1]
    full = _join(path_prefix, last)
    copied = _copy_value(value)

    if last not in current:
        current[last] = copied
        return

    existing = current[last]
    if override:
        current[last] = copied
    elif isinstance(existing, dict) and isinstance(copied, dict):
        current[last] = merge(existing, copied, full)
    elif existing == copied:
        _warn_duplicate(full)
    else:
        raise ConflictError(
            f"E003 ConflictError: conflicting values at {full}: "
            f"{existing!r} vs {copied!r}"
        )


def merge_objects(
    base: dict,
    override: dict,
    path: str = "",
    allow_override: bool = True,
) -> dict:
    """Совместимость со старым API: override → deep_merge, иначе — merge."""
    if allow_override:
        result = _copy_value(base)
        return deep_merge(result, override, path)
    return merge(base, override, path)
````

## File: dl/parser.py
````python
"""Разбор DL v2.1 в AST.

Публичный API:
    parse(source: str, filename: str = "<input>") -> dict

Контракт AST описан в задании (этап 1). Одно расширение контракта:
анонимный объектный тип в схеме (`{ field: type; ... }`) представлен как
``{"kind": "object", "fields": [Field, ...]}`` — в перечне типов задания он
не указан, но examples/config.schema без него не выразить.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from lark import Lark, Token, Transformer

GRAMMAR_PATH = Path(__file__).with_name("grammar.lark")

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    '"': '"',
    "'": "'",
    "\\": "\\",
    "0": "\0",
}

# Интерполяция внутри строки: {name}, {a.b}, {$.npm.x}
_INTERP_RE = re.compile(r"\{([A-Za-z_$][A-Za-z0-9_$.\-]*)\}")


def _unescape(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            out.append(_ESCAPES.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _unquote(token: Token) -> str:
    """Снять кавычки и раскрыть escape-последовательности у STRING."""
    raw = str(token)
    if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
        raw = raw[1:-1]
    return _unescape(raw)


def _split_interpolation(text: str) -> list[tuple[str, str] | tuple[str, list[str]]]:
    """Разбить строку на литералы и интерполяции.

    Результат: [("lit", str) | ("expr", [str]), ...]. Если интерполяций нет,
    возвращается один литерал (возможно пустой).
    """
    parts: list[tuple[str, str] | tuple[str, list[str]]] = []
    pos = 0
    for match in _INTERP_RE.finditer(text):
        if match.start() > pos:
            parts.append(("lit", text[pos : match.start()]))
        parts.append(("expr", match.group(1).split(".")))
        pos = match.end()
    if pos < len(text):
        parts.append(("lit", text[pos:]))
    if not parts:
        parts.append(("lit", ""))
    return parts


def _doc_text(token: Token) -> str:
    text = str(token)
    if text.startswith("///"):
        text = text[3:]
    return text.strip()


def _field(
    name: str,
    typ: dict,
    optional: bool,
    default: dict | None,
    doc: str | None,
) -> dict:
    return {
        "name": name,
        "type": typ,
        "optional": optional,
        "default": default,
        "doc": doc,
    }


def _document(
    kind: str,
    fmt: str | None,
    schema: str | None,
    params: list[dict] | None,
    body: list[dict],
) -> dict:
    return {
        "kind": kind,
        "format": fmt,
        "schema": schema,
        "params": params,
        "body": body,
    }


# ---------------------------------------------------------------------------
# Трансформер
# ---------------------------------------------------------------------------


class DLTransformer(Transformer):
    """Преобразование дерева разбора Lark в AST DL."""

    # ── документ ──────────────────────────────────────────────────────────

    def start(self, items):
        return items[0]

    def config_with_schema(self, items):
        fmt, params, schema, body = items
        return _document("config", fmt.value, schema, params, body)

    def config_plain(self, items):
        fmt, params, body = items
        return _document("config", fmt.value, None, params, body)

    def config_bare_with_schema(self, items):
        fmt, schema, body = items
        return _document("config", fmt.value, schema, None, body)

    def config_bare(self, items):
        fmt, body = items
        return _document("config", fmt.value, None, None, body)

    def module_doc(self, items):
        params, body = items
        return _document("module", None, None, params, body)

    def schema_doc(self, items):
        return _document("schema", None, None, None, items[0])

    def schema_name(self, items):
        return items[0].value

    # ── параметры ─────────────────────────────────────────────────────────

    def param_block(self, items):
        return items[0] if items else []

    def param_list(self, items):
        return list(items)

    def param_context(self, items):
        return {"name": "$", "optional": False, "default": None}

    def param_plain(self, items):
        return {"name": items[0].value, "optional": False, "default": None}

    def param_optional(self, items):
        return {"name": items[0].value, "optional": True, "default": None}

    def param_default(self, items):
        return {"name": items[0].value, "optional": False, "default": items[1]}

    # ── блоки и инструкции ────────────────────────────────────────────────

    def block(self, items):
        return items[0] if items else []

    def stmts_more(self, items):
        return [items[0], *items[1]]

    def stmts_trailing(self, items):
        return [items[0]]

    def stmts_single(self, items):
        return [items[0]]

    def stmt(self, items):
        return items[0]

    def let_stmt(self, items):
        return {"kind": "let", "name": items[0].value, "value": items[1]}

    def spread_stmt(self, items):
        return {"kind": "spread", "value": items[0]}

    def field(self, items):
        return {
            "kind": "field",
            "path": items[0],
            "value": items[1],
            "optional": False,
        }

    def field_optional(self, items):
        return {
            "kind": "field",
            "path": items[0],
            "value": items[1],
            "optional": True,
        }

    def call_stmt(self, items):
        return {"kind": "expr", "value": items[0]}

    def field_path(self, items):
        return [self._segment(items[0]), *items[1:]]

    def path_seg(self, items):
        return self._segment(items[0])

    @staticmethod
    def _segment(token: Token) -> str:
        if token.type == "STRING":
            return _unquote(token)
        return token.value

    # ── выражения ─────────────────────────────────────────────────────────

    def expr(self, items):
        # Обёртка для альтернатив expr без собственного алиаса.
        return items[0]

    def string_lit(self, items):
        return {
            "kind": "string",
            "parts": _split_interpolation(_unquote(items[0])),
        }

    def int_lit(self, items):
        return {"kind": "int", "value": int(items[0].value)}

    def float_lit(self, items):
        return {"kind": "float", "value": float(items[0].value)}

    def true_lit(self, items):
        return {"kind": "bool", "value": True}

    def false_lit(self, items):
        return {"kind": "bool", "value": False}

    def null_lit(self, items):
        return {"kind": "null"}

    def array_empty(self, items):
        return {"kind": "array", "items": []}

    def array(self, items):
        return {"kind": "array", "items": items[0]}

    def expr_list_more(self, items):
        return [items[0], *items[1]]

    def expr_list_space(self, items):
        return [items[0], *items[1]]

    def expr_list_trailing(self, items):
        return [items[0]]

    def expr_list_single(self, items):
        return [items[0]]

    def object(self, items):
        return {"kind": "object", "body": items[0]}

    def call_empty(self, items):
        return {
            "kind": "call",
            "name": items[0].value,
            "positional": [],
            "named": None,
        }

    def call(self, items):
        name = items[0].value
        args = items[1]
        # Объект последним аргументом — это именованные аргументы (5.5).
        if args and args[-1].get("kind") == "object":
            return {
                "kind": "call",
                "name": name,
                "positional": args[:-1],
                "named": args[-1]["body"],
            }
        return {"kind": "call", "name": name, "positional": args, "named": None}

    def args_more(self, items):
        return [items[0], *items[1]]

    def args_trailing(self, items):
        return [items[0]]

    def args_single(self, items):
        return [items[0]]

    def import_expr(self, items):
        path = items[0].value
        parts = None
        is_glob = "*" in path
        if _INTERP_RE.search(path):
            parts = _split_interpolation(path)
        return {"kind": "import", "path": path, "parts": parts, "glob": is_glob}

    def ref(self, items):
        return {"kind": "ref", "path": items[0]}

    def ref_path(self, items):
        return [self._segment(items[0]), *items[1:]]

    # ── схема ─────────────────────────────────────────────────────────────

    def schema_block(self, items):
        return list(items)

    def class_plain(self, items):
        return {
            "kind": "class",
            "name": items[0].value,
            "doc": None,
            "fields": list(items[1:]),
        }

    def class_doc(self, items):
        return {
            "kind": "class",
            "name": items[1].value,
            "doc": items[0],
            "fields": list(items[2:]),
        }

    def doc(self, items):
        return "\n".join(_doc_text(token) for token in items)

    def field_name(self, items):
        return self._segment(items[0])

    def class_field_plain(self, items):
        return _field(items[0], items[1], False, _opt(items, 2), None)

    def class_field_optional(self, items):
        return _field(items[0], items[1], True, _opt(items, 2), None)

    def class_field_doc_plain(self, items):
        return _field(items[1], items[2], False, _opt(items, 3), items[0])

    def class_field_doc_optional(self, items):
        return _field(items[1], items[2], True, _opt(items, 3), items[0])

    def obj_field_plain(self, items):
        return _field(items[0], items[1], False, _opt(items, 2), None)

    def obj_field_optional(self, items):
        return _field(items[0], items[1], True, _opt(items, 2), None)

    def obj_field_doc_plain(self, items):
        return _field(items[1], items[2], False, _opt(items, 3), items[0])

    def obj_field_doc_optional(self, items):
        return _field(items[1], items[2], True, _opt(items, 3), items[0])

    # ── типы ──────────────────────────────────────────────────────────────

    def type(self, items):
        if len(items) == 1:
            return items[0]
        return {"kind": "union", "variants": list(items)}

    def type_atom(self, items):
        return items[0]

    def t_string(self, items):
        return {"kind": "primitive", "name": "string"}

    def t_integer(self, items):
        return {"kind": "primitive", "name": "integer"}

    def t_number(self, items):
        return {"kind": "primitive", "name": "number"}

    def t_float(self, items):
        return {"kind": "primitive", "name": "float"}

    def t_boolean(self, items):
        return {"kind": "primitive", "name": "boolean"}

    def t_null(self, items):
        return {"kind": "primitive", "name": "null"}

    def t_any(self, items):
        return {"kind": "primitive", "name": "any"}

    def array_type(self, items):
        return {"kind": "array", "of": items[0]}

    def map_type(self, items):
        return {"kind": "map", "of": items[0]}

    def enum_type(self, items):
        return {"kind": "enum", "values": list(items)}

    def enum_string(self, items):
        return _unquote(items[0])

    def enum_number(self, items):
        return str(int(items[0].value))

    def enum_true(self, items):
        return "true"

    def enum_false(self, items):
        return "false"

    def enum_null(self, items):
        return "null"

    def object_type(self, items):
        return {"kind": "object", "fields": list(items)}

    def named_type(self, items):
        return {"kind": "named", "name": items[0].value}


def _opt(items: list, index: int):
    return items[index] if len(items) > index else None


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------


def load_grammar() -> str:
    return GRAMMAR_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _get_parser() -> Lark:
    return Lark(load_grammar(), parser="lalr", start="start")


def parse(source: str, filename: str = "<input>") -> dict:
    """Разобрать исходник DL в AST.

    filename используется только для сообщений об ошибках (в текущей версии
    пробрасываются исключения Lark как есть).
    """
    tree = _get_parser().parse(source)
    return DLTransformer().transform(tree)


if __name__ == "__main__":
    print(parse('json => { name: "test"; }'))
````

## File: dl/report.py
````python
"""Отчёт о сборке DL: дерево этапов и файлов в реальном времени.

Дерево рисуется в ``stderr`` (stdout компилятора не меняется). В терминале
используется :class:`rich.live.Live` с частотой 10 кадров в секунду; при
перенаправленном выводе или ``enabled=False`` дерево печатается один раз в
конце, без анимации.

Доступ из глубины компилятора (``Resolver.load``) — через контекстную
переменную::

    from .report import get_reporter

    reporter = get_reporter()
    if reporter is not None:
        reporter.file_start(path)

Один файл (по абсолютному пути) показывается в дереве один раз: повторные
обращения увеличивают счётчик ``uses`` (в подписи — ``×N``), не меняя
вложенность и статус уже завершённого узла. Без установленного репортёра
все обращения — no-op.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.tree import Tree

RUNNING = "running"
OK = "ok"
CACHED = "cached"
ERROR = "error"

_GLYPHS: dict[str, tuple[str, str]] = {
    RUNNING: ("⋯", "yellow"),
    OK: ("✓", "green"),
    CACHED: ("○", "dim"),
    ERROR: ("✗", "red"),
}

REFRESH_PER_SECOND = 10


def _one_line(message: str) -> str:
    """Первая строка сообщения: дерево не должно «разъезжаться»."""
    lines = str(message).strip().splitlines()
    return lines[0] if lines else ""


@dataclass
class _Node:
    """Узел внутренней модели дерева."""

    key: str
    label: str
    status: str = RUNNING
    detail: str = ""
    error: str = ""
    uses: int = 1
    children: list["_Node"] = field(default_factory=list)


class BuildReporter:
    """Модель дерева сборки и её отрисовка через ``rich``."""

    def __init__(
        self,
        console: Console | None = None,
        *,
        enabled: bool = True,
    ) -> None:
        self.console = console if console is not None else Console(stderr=True)
        self.enabled = enabled
        self._root = _Node(key="", label="")
        self._stages: dict[str, _Node] = {}
        # Один файл — один узел: реестр по абсолютному пути.
        self._nodes: dict[str, _Node] = {}
        self._stack: list[_Node] = []
        self._base_dir: Path | None = None
        self._started = False
        self._finished = False
        self._live: Live | None = None

    # ── пути ──────────────────────────────────────────────────────────────

    def display(self, path: str | os.PathLike[str]) -> str:
        """Путь относительно каталога исходника (вне его — с ``../``)."""
        candidate = Path(path)
        if self._base_dir is None:
            return candidate.name
        try:
            return os.path.relpath(candidate.resolve(), self._base_dir)
        except ValueError:  # разные диски (Windows)
            return candidate.name

    @staticmethod
    def _key(path: str | os.PathLike[str]) -> str:
        return str(Path(path).resolve())

    # ── события ───────────────────────────────────────────────────────────

    def start(
        self,
        source: str | os.PathLike[str],
        target: str | os.PathLike[str] | None = None,
    ) -> None:
        """Задать корень дерева: ``source → target``."""
        self._started = True
        self._base_dir = Path(source).resolve().parent
        destination = "?" if target is None else self.display(target)
        self._root.label = f"{self.display(source)} → {destination}"
        if self.enabled and self.console.is_terminal:
            live = Live(
                self._render(),
                console=self.console,
                refresh_per_second=REFRESH_PER_SECOND,
                transient=True,
            )
            live.start()
            self._live = live

    def stage(self, key: str, label: str) -> None:
        """Добавить этап сборки (``parse``, ``schema``, ``validate``, ...)."""
        node = _Node(key=key, label=label, status=RUNNING)
        self._root.children.append(node)
        self._stages[key] = node
        self._refresh()

    def stage_done(self, key: str, detail: str = "") -> None:
        """Отметить этап успешным, при необходимости — с пояснением."""
        node = self._stages.get(key)
        if node is None:
            return
        node.detail = detail
        if node.status != ERROR:
            node.status = OK
        self._refresh()

    def stage_error(self, key: str, message: str) -> None:
        """Отметить этап ошибочным."""
        node = self._stages.get(key)
        if node is None:
            return
        node.status = ERROR
        node.error = str(message)
        self._refresh()

    def file_start(
        self,
        path: str | os.PathLike[str],
        cached: bool = False,
    ) -> None:
        """Открыть файл; вложенность — по стеку открытых файлов.

        Повторный файл не дублируется: у существующего узла растёт ``uses``,
        позиция в дереве и статус не меняются.
        """
        key = self._key(path)
        existing = self._nodes.get(key)
        if existing is not None:
            existing.uses += 1
            self._stack.append(existing)
            self._refresh()
            return

        node = _Node(
            key=key,
            label=self.display(path),
            status=CACHED if cached else RUNNING,
        )
        self._nodes[key] = node
        parent = self._stack[-1] if self._stack else self._root
        parent.children.append(node)
        self._stack.append(node)
        self._refresh()

    def file_end(
        self,
        path: str | os.PathLike[str],
        error: BaseException | str | None = None,
    ) -> None:
        """Закрыть файл; ошибка помечает узел красным.

        Уже завершённый узел (``ok``/``cached``/``error``) без новой ошибки
        свой статус не меняет.
        """
        key = self._key(path)
        node: _Node | None = None
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index].key == key:
                node = self._stack[index]
                del self._stack[index:]
                break
        if node is None:
            return
        if error is not None:
            node.status = ERROR
            node.error = str(error)
        elif node.status == RUNNING:
            node.status = OK
        self._refresh()

    def fail(self, message: str) -> None:
        """Пометить сборку ошибочной (корень и незавершённые этапы)."""
        text = str(message)
        for node in self._walk(self._root):
            if node is not self._root and node.status == RUNNING:
                node.status = ERROR
                if not node.error:
                    node.error = text
        self._root.status = ERROR
        # Текст уже виден на упавшем узле — у корня не дублируем.
        self._root.error = "" if self._has_error(text) else text
        self._refresh()

    def _walk(self, node: _Node) -> Iterator[_Node]:
        yield node
        for child in node.children:
            yield from self._walk(child)

    def _has_error(self, text: str) -> bool:
        return any(
            node.status == ERROR and node.error == text
            for node in self._walk(self._root)
        )

    def finish(self) -> None:
        """Остановить Live и напечатать финальное дерево (идемпотентно)."""
        if self._finished:
            return
        self._finished = True
        if self._live is not None:
            self._live.stop()
            self._live = None
        if not self._started:
            return
        self.console.print(self._render())

    # ── отрисовка ─────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._render())

    def _render(self) -> Tree:
        label = Text(self._root.label)
        if self._root.status == ERROR:
            label.append(" ✗", style="red")
            if self._root.error:
                label.append(" " + _one_line(self._root.error), style="red")
        tree = Tree(label)
        for child in self._root.children:
            tree.add(self._render_node(child))
        return tree

    def _render_node(self, node: _Node) -> Tree:
        tree = Tree(self._node_text(node))
        for child in node.children:
            tree.add(self._render_node(child))
        return tree

    @staticmethod
    def _node_text(node: _Node) -> Text:
        text = Text(node.label)
        if node.uses > 1:
            text.append(f" ×{node.uses}")
        if node.detail:
            text.append(" " + node.detail)
        glyph, style = _GLYPHS[node.status]
        text.append(" " + glyph, style=style)
        if node.status == CACHED:
            text.append(" cached", style="dim")
        if node.status == ERROR and node.error:
            text.append(" " + _one_line(node.error), style="red")
        return text


# ── модульная точка доступа ────────────────────────────────────────────────

_reporter: ContextVar[BuildReporter | None] = ContextVar(
    "dl.build_reporter", default=None
)


def get_reporter() -> BuildReporter | None:
    """Текущий репортёр или ``None`` (тогда все события — no-op)."""
    return _reporter.get()


def set_reporter(
    reporter: BuildReporter | None,
) -> Token[BuildReporter | None]:
    """Установить репортёр для текущего контекста."""
    return _reporter.set(reporter)


def reset_reporter(token: Token[BuildReporter | None]) -> None:
    """Вернуть предыдущий репортёр (по токену ``set_reporter``)."""
    _reporter.reset(token)


__all__ = [
    "BuildReporter",
    "CACHED",
    "ERROR",
    "OK",
    "RUNNING",
    "get_reporter",
    "reset_reporter",
    "set_reporter",
]
````

## File: dl/resolver.py
````python
"""Загрузка модулей, разрешение путей импорта и кэш (DL v2.1).

Модуль кэшируется по абсолютному пути и отпечатку файла (``mtime_ns`` +
``size``): один файл вычисляется один раз, а функции из него можно вызывать
сколько угодно раз. Если файл изменился, отпечаток другой — модуль
пересчитывается. Цикл определяется по стеку загружаемых файлов (``E004``).

Разобранный AST дополнительно кэшируется на диске (:class:`dl.cache.DiskCache`).
Дисковый кэш передаётся в цепочку ``evaluate`` → ``resolve_import`` через
``ContextVar`` — по образцу репортёра (:mod:`dl.report`): сигнатуры вызова не
меняются, а установка действует только в текущем контексте.

Glob-импорт (``import ./dir/*.dl``): звёздочка только в последнем сегменте.
Результат — слияние всех найденных файлов через merge (строгое: W001/E003).
Сортировка по абсолютному пути, детерминированно. Модуль без параметров —
вычисляется сразу; с параметрами — ошибка E014. Пустой каталог → ``{}``.
"""

from __future__ import annotations

import glob
import os
from contextvars import ContextVar, Token
from pathlib import Path
from stat import S_ISREG
from typing import Any

from .cache import DiskCache
from .errors import CircularImportError, GlobParameterizedModule, ModuleNotFoundError
from .parser import parse
from .report import get_reporter


def _copy(value: Any) -> Any:
    """Копия вычисленного модуля.

    Function отдаётся как есть (она неизменяема и вызывается многократно),
    словари/массивы копируются, чтобы потребитель не мог испортить кэш.
    """
    if isinstance(value, dict):
        return {key: _copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy(item) for item in value]
    return value


class Resolver:
    """Кэш и стек вычисленных модулей."""

    def __init__(self, cache: DiskCache | None = None) -> None:
        # Ключ — (абсолютный путь, mtime_ns, size): изменение файла даёт
        # другой ключ, поэтому устаревшее значение не возвращается.
        self._cache: dict[tuple[str, int, int], Any] = {}
        self._stack: list[str] = []
        self.cache = cache

    # ── дисковый кэш ──────────────────────────────────────────────────────

    def _disk(self) -> DiskCache | None:
        """Явный кэш конструктора или установленный через ``ContextVar``."""
        if self.cache is not None:
            return self.cache
        return get_disk_cache()

    # ── пути ──────────────────────────────────────────────────────────────

    @staticmethod
    def resolve_path(path: str, base_dir: Path | str) -> Path:
        """Абсолютный путь импорта относительно каталога модуля-источника."""
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = Path(base_dir) / candidate
        return candidate.resolve()

    @staticmethod
    def _stat(path: Path) -> os.stat_result | None:
        try:
            return os.stat(path)
        except OSError:
            return None

    # ── загрузка ──────────────────────────────────────────────────────────

    def load(
        self,
        path: str,
        base_dir: Path | str,
        context: dict | None = None,
    ) -> Any:
        """Загрузить, вычислить и закэшировать модуль по пути импорта."""
        full = self.resolve_path(path, base_dir)
        key = str(full)

        if key in self._stack:
            chain = " -> ".join([*self._stack, key])
            raise CircularImportError(
                f"E004 CircularImportError: circular import {chain}"
            )

        # Один stat на всю загрузку: и для отпечатка, и для дискового кэша.
        stat = self._stat(full)
        is_regular = stat is not None and S_ISREG(stat.st_mode)
        fingerprint: tuple[str, int, int] | None = None
        if stat is not None and is_regular:
            fingerprint = (key, stat.st_mtime_ns, stat.st_size)

        memory_hit = (
            fingerprint is not None and fingerprint in self._cache
        )
        disk = self._disk()
        ast: dict | None = None
        disk_hit = False
        if (
            not memory_hit
            and disk is not None
            and stat is not None
            and is_regular
        ):
            ast = disk.get(full, stat)
            disk_hit = ast is not None

        cached = memory_hit or disk_hit
        reporter = get_reporter()
        if reporter is not None:
            reporter.file_start(str(full), cached=cached)

        error: BaseException | None = None
        try:
            if memory_hit:
                return _copy(self._cache[fingerprint])  # type: ignore[index]

            if not is_regular or stat is None:
                raise ModuleNotFoundError(
                    f"E002 ModuleNotFoundError: module not found: {full}"
                )

            if ast is None:
                source = full.read_text(encoding="utf-8")
                ast = parse(source, str(full))
                if disk is not None:
                    disk.put(full, stat, ast)

            self._stack.append(key)
            try:
                # Ленивый импорт: evaluator сам импортирует resolver.
                from .evaluator import evaluate

                value = evaluate(ast, full.parent, context)
            finally:
                self._stack.pop()

            assert fingerprint is not None
            self._cache[fingerprint] = value
            return _copy(value)
        except BaseException as exc:
            error = exc
            raise
        finally:
            if reporter is not None:
                reporter.file_end(str(full), error=error)

    def resolve_glob(
        self,
        pattern: str,
        base_dir: Path | str,
        context: dict | None = None,
    ) -> Any:
        """Загрузить и слить все файлы по glob-паттерну.

        pattern: путь с * в последнем сегменте (например, ./dir/*.dl)
        base_dir: каталог модуля-источника
        context: контекст для вызова модулей

        Результат — слияние всех файлов через merge (строгое: W001/E003).
        Сортировка по абсолютному пути, детерминированно.
        Модуль без параметров — вычисляется сразу; с параметрами — E014.
        Пустой каталог → {}.
        """
        from .evaluator import Function, call_value, evaluate
        from .merger import merge

        base = Path(base_dir).resolve()
        # Глоб-паттерн: последний сегмент содержит *
        # Пример: ./dir/*.dl → base / "dir" / "*.dl"
        if pattern.startswith("./"):
            rel_path = pattern[2:]
        elif pattern.startswith("../"):
            rel_path = pattern
        else:
            rel_path = pattern

        # Разделяем путь на директорию и паттерн
        parts = rel_path.split("/")
        if "*" in parts[-1]:
            dir_parts = parts[:-1]
            glob_pattern = parts[-1]
        else:
            # Звёздочка в середине пути — не поддерживается
            dir_parts = parts
            glob_pattern = "*.dl"

        target_dir = base / "/".join(dir_parts) if dir_parts else base

        if not target_dir.exists():
            return {}

        # Поиск файлов
        files = sorted(target_dir.glob(glob_pattern))

        if not files:
            return {}

        # Слияние всех файлов
        result: dict = {}
        for file_path in files:
            if not file_path.is_file():
                continue

            # Загрузка файла через обычный load (не рекурсивно)
            module_value = self.load(str(file_path), file_path.parent, context)

            # Проверка: модуль с параметрами — ошибка E014
            if isinstance(module_value, Function) and module_value.params:
                raise GlobParameterizedModule(
                    f"E014 GlobParameterizedModule: "
                    f"glob import cannot import module with parameters: {file_path}"
                )

            # Модуль без параметров — вызываем сразу
            if isinstance(module_value, Function) and not module_value.params:
                module_value = call_value(module_value, [], None, context, file_path.parent)

            # Слияние с результатом
            if isinstance(module_value, dict):
                result = merge(result, module_value, str(file_path))

        return result

    # ── обслуживание ──────────────────────────────────────────────────────

    def clear(self) -> None:
        self._cache.clear()
        self._stack.clear()


_default = Resolver()


# ── дисковый кэш в текущем контексте ──────────────────────────────────────

_disk_cache: ContextVar[DiskCache | None] = ContextVar(
    "dl.disk_cache", default=None
)


def get_disk_cache() -> DiskCache | None:
    """Дисковый кэш AST, установленный в текущем контексте."""
    return _disk_cache.get()


def set_disk_cache(
    cache: DiskCache | None,
) -> Token[DiskCache | None]:
    """Установить дисковый кэш для текущего контекста."""
    return _disk_cache.set(cache)


def reset_disk_cache(token: Token[DiskCache | None]) -> None:
    """Вернуть предыдущий дисковый кэш (по токену ``set_disk_cache``)."""
    _disk_cache.reset(token)


# ── модульная точка доступа ───────────────────────────────────────────────


def resolve_import(
    path: str,
    base_dir: Path | str,
    context: dict | None = None,
) -> Any:
    """Разрешить ``import`` через общий кэш."""
    return _default.load(path, base_dir, context)


def resolve_glob_import(
    pattern: str,
    base_dir: Path | str,
    context: dict | None = None,
) -> Any:
    """Разрешить glob-``import`` через общий кэш."""
    return _default.resolve_glob(pattern, base_dir, context)


def resolve_path(path: str, base_dir: Path | str) -> Path:
    """Абсолютный путь импорта (без загрузки)."""
    return _default.resolve_path(path, base_dir)


def reset_cache() -> None:
    """Сбросить in-memory кэш и стек (дисковый кэш не трогается)."""
    _default.clear()


__all__ = [
    "Resolver",
    "get_disk_cache",
    "reset_cache",
    "reset_disk_cache",
    "resolve_glob_import",
    "resolve_import",
    "resolve_path",
    "set_disk_cache",
]
````

## File: dl/serializer.py
````python
"""Сериализация вычисленного значения DL в json/toml/yaml."""

from __future__ import annotations

import json
from typing import Any

import toml
import yaml

from .errors import FormatNotFoundError

FORMATS = ("json", "toml", "yaml")


def _drop_none(value: Any) -> Any:
    """Убрать ``None`` из структур (TOML не умеет null)."""
    if isinstance(value, dict):
        return {
            key: _drop_none(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_drop_none(item) for item in value]
    return value


def normalize_format(value: str | None) -> str | None:
    """Привести имя формата к каноническому виду (``yml`` → ``yaml``)."""
    if value is None:
        return None
    fmt = str(value).strip().lower().lstrip(".")
    if fmt == "yml":
        return "yaml"
    return fmt


def serialize(value: dict, format: str | None = None) -> str:
    """Сериализовать словарь в заданный формат (``E005`` при неизвестном)."""
    fmt = normalize_format(format)
    if fmt is None:
        raise FormatNotFoundError(
            "E005 FormatNotFoundError: output format is not specified"
        )
    if fmt not in FORMATS:
        raise FormatNotFoundError(
            f"E005 FormatNotFoundError: unknown output format '{format}'"
        )

    if fmt == "json":
        return json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if fmt == "toml":
        return toml.dumps(_drop_none(value))
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False)


__all__ = ["FORMATS", "normalize_format", "serialize"]
````

## File: dl/validator.py
````python
"""Валидация значения по AST DL-схемы (этап 3).

Публичный API:

    validate(value, class_name, classes, path="") -> list[str]
    validate_or_raise(value, class_name, classes, path="") -> None

``classes`` — список классов из :func:`dl.evaluator.evaluate` для документа
``schema`` (``{"kind": "schema", "classes": [...]}``). Каждый класс —
``{"kind": "class", "name": ..., "fields": [Field, ...]}``.

Правила (раздел 4.6 спецификации):

* optional-поле может отсутствовать; обязательное — ``E011`` с путём;
* ``boolean`` не является ``integer``, ``integer`` не ``float``,
  ``float``/``number`` принимают целые;
* ``enum`` — значение входит в список (строки, числа, булевы, null);
* ``union`` — достаточно одного подходящего варианта;
* ``map`` — объект, все значения типа ``T``;
* лишние ключи разрешены (``additionalProperties: true`` по умолчанию).

Все ошибки — строки вида::

    E011 TypeMismatch: <path>: expected <type>, got <type>
"""

from __future__ import annotations

from typing import Any

from .errors import TypeMismatchError

# ---------------------------------------------------------------------------
# Имена типов
# ---------------------------------------------------------------------------


def got_type(value: Any) -> str:
    """Имя типа значения в терминах DL (bool — не integer)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def type_name(typ: dict) -> str:
    """Человекочитаемое имя типа из AST."""
    kind = typ.get("kind")
    if kind == "primitive":
        return str(typ.get("name"))
    if kind == "array":
        return f"[{type_name(typ.get('of') or {})}]"
    if kind == "map":
        return f"map<{type_name(typ.get('of') or {})}>"
    if kind == "enum":
        return "enum { " + " | ".join(str(v) for v in typ.get("values") or []) + " }"
    if kind == "union":
        return " | ".join(type_name(v) for v in typ.get("variants") or [])
    if kind == "named":
        return str(typ.get("name"))
    if kind == "object":
        return "object"
    return "any"


def _join_path(path: str, segment: str) -> str:
    return f"{path}.{segment}" if path else segment


def _item_path(path: str, index: Any) -> str:
    return f"{path}[{index}]"


# ---------------------------------------------------------------------------
# Проверка типов
# ---------------------------------------------------------------------------


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _enum_literals(value: Any) -> set[str]:
    """Литералы, которыми значение может совпасть с элементом enum."""
    if value is None:
        return {"null"}
    if isinstance(value, bool):
        return {"true" if value else "false"}
    if isinstance(value, int):
        return {str(value)}
    if isinstance(value, float):
        return {str(value)}
    if isinstance(value, str):
        return {value}
    return set()


def _validate_type(
    value: Any,
    typ: dict,
    classes: dict[str, dict],
    path: str,
    errors: list[str],
) -> None:
    kind = typ.get("kind")

    if kind == "primitive":
        name = typ.get("name")
        if name == "any":
            return
        if name == "null":
            ok = value is None
        elif name == "boolean":
            ok = isinstance(value, bool)
        elif name == "string":
            ok = isinstance(value, str)
        elif name == "integer":
            ok = _is_integer(value)
        elif name == "float":
            ok = _is_number(value)
        elif name == "number":
            ok = _is_number(value)
        else:  # неизвестный примитив — не блокируем
            return
        if not ok:
            _mismatch(errors, path, type_name(typ), got_type(value))
        return

    if kind == "array":
        if not isinstance(value, list):
            _mismatch(errors, path, type_name(typ), got_type(value))
            return
        inner = typ.get("of") or {"kind": "primitive", "name": "any"}
        for index, item in enumerate(value):
            _validate_type(
                item, inner, classes, _item_path(path, index), errors
            )
        return

    if kind == "map":
        if not isinstance(value, dict):
            _mismatch(errors, path, type_name(typ), got_type(value))
            return
        inner = typ.get("of") or {"kind": "primitive", "name": "any"}
        for key, item in value.items():
            _validate_type(
                item, inner, classes, _join_path(path, str(key)), errors
            )
        return

    if kind == "enum":
        allowed = [str(item) for item in typ.get("values") or []]
        literals = _enum_literals(value)
        if not literals or not (literals & set(allowed)):
            _mismatch(errors, path, type_name(typ), got_type(value))
        return

    if kind == "union":
        variants = typ.get("variants") or []
        best: list[str] | None = None
        for variant in variants:
            scratch: list[str] = []
            _validate_type(value, variant, classes, path, scratch)
            if not scratch:
                return
            if best is None or len(scratch) < len(best):
                best = scratch
        if best:
            # Показываем наиболее близкий вариант: конкретные пути полезнее
            # общего «не подошло ни одно объединение».
            errors.extend(best)
        else:
            _mismatch(errors, path, type_name(typ), got_type(value))
        return

    if kind == "named":
        name = str(typ.get("name"))
        _validate_class(value, name, classes, path, errors)
        return

    if kind == "object":
        _validate_fields(
            value,
            typ.get("fields") or [],
            classes,
            path,
            errors,
            expected="object",
        )
        return

    # Неизвестный тип — не блокируем (схема новее валидатора).
    return


def _validate_class(
    value: Any,
    class_name_value: str,
    classes: dict[str, dict],
    path: str,
    errors: list[str],
) -> None:
    cls = classes.get(class_name_value)
    if cls is None:
        _mismatch(errors, path, class_name_value, got_type(value))
        return
    _validate_fields(
        value,
        cls.get("fields") or [],
        classes,
        path,
        errors,
        expected=class_name_value,
    )


def _validate_fields(
    value: Any,
    fields: list[dict],
    classes: dict[str, dict],
    path: str,
    errors: list[str],
    *,
    expected: str,
) -> None:
    if not isinstance(value, dict):
        _mismatch(errors, path, expected, got_type(value))
        return

    for field in fields:
        name = str(field.get("name"))
        field_path = _join_path(path, name)
        optional = bool(field.get("optional"))
        field_type = field.get("type") or {"kind": "primitive", "name": "any"}

        if name not in value:
            if not optional:
                _mismatch(
                    errors,
                    field_path,
                    type_name(field_type),
                    "missing",
                )
            continue

        _validate_type(
            value[name], field_type, classes, field_path, errors
        )


def _mismatch(
    errors: list[str], path: str, expected: str, got: str
) -> None:
    errors.append(
        f"E011 TypeMismatch: {path or '<root>'}: "
        f"expected {expected}, got {got}"
    )


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------


def class_map(classes: list[dict]) -> dict[str, dict]:
    """Индекс классов по имени."""
    return {
        str(cls.get("name")): cls
        for cls in classes
        if cls.get("kind") == "class"
    }


def validate(
    value: Any,
    class_name: str,
    classes: list[dict],
    path: str = "",
) -> list[str]:
    """Проверить значение по классу схемы. Возвращает список ошибок."""
    errors: list[str] = []
    _validate_class(value, class_name, class_map(classes), path, errors)
    return errors


def validate_or_raise(
    value: Any,
    class_name: str,
    classes: list[dict],
    path: str = "",
) -> None:
    """Проверить значение и бросить ``E011`` со всеми ошибками."""
    errors = validate(value, class_name, classes, path)
    if errors:
        raise TypeMismatchError("\n".join(errors))


__all__ = [
    "class_map",
    "got_type",
    "type_name",
    "validate",
    "validate_or_raise",
]
````

## File: examples/modules/agents.dl
````
( $ ) => {
    let agents = import ../agents/agents.dl;

    ...agents();
}
````

## File: examples/modules/permissions.dl
````
( $ ) => {
    permission: {
        bash: {
            "*find*": "deny";
            "*grep*": "deny";
            "*npm*": "deny";
            "*sqlite*": "ask";
            "*opencode*": "ask";
        };
        "glob": "deny";
        "grep": "deny";
        "websearch": "deny";
    };
}
````

## File: examples/providers/createprovider.dl
````
( $, name, npm, port, options: {}, models ) => {
    let makeoptions = import ./models/func/makeoptions.dl;

    npm: npm;
    name: "{name}";
    options: {
        ...makeoptions(port);
        ...options;
    };
    models: models;
}
````

## File: examples/providers/deepseek-proxy.dl
````
( $, name, npm, port, models ) => {
    let createprovider = import ./createprovider.dl;

    createprovider(name, {
        npm: npm;
        port: port;
        options: {
            toolCallFallback: "auto";
            useCompletionUrls: true;
        };
        models: models;
    });
}
````

## File: pyproject.toml
````toml
[project]
name = "dl"
version = "0.1.0"
description = "DL language compiler"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "lark>=1.3.1",
    "pygls>=2.1.1",
    "pyyaml>=6.0.3",
    "rich>=15.0.0",
    "toml>=0.10.2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.scripts]
dl = "dl.cli:main"
dl-lsp = "dl_lsp.server:main"

[tool.uv]
package = true

[dependency-groups]
dev = [
    "pytest>=9.1.1",
]
````

## File: spec.md
````markdown
# Язык конфигурации DL — Спецификация v2.4

Версия: **2.4**
Дата: **2026-10-25**

Декларативный язык описания конфигурации с компиляцией в JSON, TOML и YAML.
Источник истины для синтаксиса — файлы каталога `examples/`.

---

## 1. Обзор

DL — декларативный язык без управляющих конструкций: документ описывает данные,
модули описывают функции, которые эти данные порождают.

**Виды файлов:**

| Вид | Признак | Назначение |
|-----|---------|------------|
| Конфигурация | заголовок формата: `json( $ ) => Config { ... }` | итоговый документ |
| Модуль | заголовок без формата: `( params ) => { ... }` | функция/значение, подключаемое через `import` |
| Схема | заголовок `schema => { ... }` | классы для валидации (`*.schema`) |
| Мета-файл | `settings.dl` в каталоге сборки | список сборок и общие значения (`$.builds`, `$.npm`) |

**Конвейер компиляции:**

```
текст → разбор (AST) → разрешение import → вычисление функций
      → слияние объектов → валидация по схеме → сериализация в формат
```

**Базовые принципы:**

- Значение документа — объект, собранный из последовательности инструкций.
- `import` только загружает модуль; вызов — отдельная операция.
- Слияние объектов детерминировано и описано в разделе 6.
- Схемы (раздел 4) описывают форму результата; `$ref` в них уже развёрнут генератором.

---

## 2. Лексика

- Кодировка UTF-8; переводы строк LF или CRLF.
- Пробелы, табуляции и переводы строк разделяют лексемы; отступы не значимы.
- Комментарии: `//` до конца строки. Doc-комментарии: `///` — относятся к следующему объявлению (полю класса).

```dl
// обычный комментарий
/// Документация поля (попадает в сгенерированную схему)
default_agent?: string;
```

**Идентификаторы:** `[A-Za-z_][A-Za-z0-9_-]*`.

**Ключевые слова:** `json`, `toml`, `yaml`, `schema`, `class`, `enum`, `map`,
`let`, `import`, `true`, `false`, `null`, а также имена примитивных типов
`string`, `integer`, `number`, `float`, `boolean`, `any`.

**Знаки:** `{ }` `[ ]` `( )` `:` `;` `,` `=` `.` `?` `|` `$` `...` и кавычки `"` `'`.

**Строки:** в двойных или одинарных кавычках. Оба вида равнозначны; выбор диктуется
удобством (одинарные удобны, когда внутри есть двойные, и наоборот).

---

## 3. Значения

| Значение | Синтаксис | Пример |
|----------|-----------|--------|
| Строка | `"..."` или `'...'` | `"jarvis"`, `'@ai-sdk/openai-compatible'` |
| Целое | цифры, опционально `-` | `9625` |
| Дробное | с точкой | `3.14` |
| Булево | `true` / `false` | `true` |
| Null | `null` | `null` |
| Массив | `[ ... ]` | `[ "a" "b" ]` |
| Объект | `{ ... }` | `{ name: "x"; }` |
| Импорт | `import <путь>` | `import ./models/x.dl` |
| Вызов | `<имя>( ... )` | `makeoptions(9625)` |

### 3.1. Интерполяция строк

Внутри строки конструкция `{expr}` подставляет значение выражения:

```dl
name: "{name}";
baseURL: "http://{host}:{port}/v1";
```

Подставляемое выражение — имя параметра/привязки или путь доступа (`a.b`).
Интерполяция работает и в путях `import` (раздел 5.4).

### 3.2. Массивы

Элементы разделяются пробелом или переводом строки. Запятые допустимы, но
необязательны и на результат не влияют.

```dl
instructions: [
    "~/.config/opencode/global-rules.md"
];

plugin: [
    "opencode-intellisearch",
    "@tarquinen/opencode-dcp@3.1.13",
    "opencode-agent-memory"
];

"permissions": [
    { action: "edit"; resource: "*"; effect: "deny"; },
    { action: "shell"; resource: "*"; effect: "deny"; }
];
```

Пустой массив — `[]`.

### 3.3. Объекты

```dl
permission: {
    bash: {
        "*find*": "deny";
        "*sqlite*": "ask";
    };
    "glob": "deny";
};
```

- Поле: `key: value;` или `key = value;` — формы эквивалентны.
- Условное поле: `key?: value;` — добавляется только при определённом значении
  (раздел 5.2).
- Ключ — идентификатор или строка в кавычках (для ключей с `*`, `-`, пробелами и т.п.).
- Пустой объект — `{}`.
- `;` после последней инструкции блока необязательна.

### 3.4. Точечная нотация

Путь в ключе создаёт вложенность; промежуточные объекты объявлять отдельно не нужно:

```dl
// examples/modules/mcp.dl (фрагмент)
mcp.servers = {
    ...deepwiki();
    ...sequential();
    // ...
};
```

Здесь `mcp` отдельно не объявляется: инструкция эквивалентна

```dl
mcp: {
    servers: {
        // ...
    };
};
```

Правила:

- `a.b = value;` и `a.b: value;` эквивалентны; `=` предпочтителен для путей и объектов.
- Каждый сегмент пути, кроме последнего, — объект; он создаётся неявно.
- Если промежуточный объект уже существует, новое поле сливается в него по
  правилам раздела 6.4 (дубликат с тем же значением — `W001`, с другим — `E003`).
- Если промежуточный сегмент уже имеет не-объектное значение — `E003 ConflictError`.
- Точечная нотация применима в теле модуля/документа и в объектах.
- Для контекста `$` точечный путь — это доступ/запись по пути:
  `$.builds`, `$.npm.openaicomp` (раздел 7).

Путь `$.override()` (раздел 6.5) — особая форма, а не обычная точечная запись.

---

## 4. Схемы и классы

### 4.1. Заголовок документа

Полная форма:

```dl
json( $ ) => Config {
    // тело документа
}
```

- `json` / `toml` / `yaml` — целевой формат.
- `( $ )` — контекст; необязателен, если `$` не используется.
- `=> Config` — имя класса-схемы для валидации результата; необязательно.
- Тело — блок объектов и инструкций (раздел 5.2).

Сокращённые формы, встречающиеся в примерах:

```dl
( $ ) => { ... }        // модуль или settings.dl
() => { ... }           // модуль без параметров
```

### 4.2. Файл схемы

```dl
schema => {
    class Config {
        /// Default model to use when no session or agent model is selected
        model?: string
        | {
            providerID: string;
            model: string;
            variant?: string;
        };
        /// Control whether sessions may be shared manually, automatically, or not at all
        share?: enum { "manual" | "auto" | "disabled" };
        /// Ordered tool permission rules applied to agent tool use
        permissions?: [PermissionRule];
    };

    class PermissionRule {
        action: string;
        resource: string;
        effect: enum { "allow" | "deny" | "ask" };
    };
}
```

- Файл схемы содержит только объявления `class`.
- Имена классов — CamelCase без точек (`PermissionRule`, `McpLocalConfigEncoded`).
- `Config` — корневой класс документа.

### 4.3. Класс и поля

```dl
class Name {
    field: type;                 // обязательное
    field?: type;                // необязательное
    field: type = default;       // со значением по умолчанию
};
```

- `///` перед полем — doc-комментарий поля.
- Значение по умолчанию — литерал DL (`true`, `120000`, `"auto"`, `[]`, `{}`).

### 4.4. Типы

| Тип | Запись |
|-----|--------|
| Строка | `string` |
| Целое | `integer` |
| Число | `number` |
| Дробное | `float` |
| Булево | `boolean` |
| Null | `null` |
| Любое | `any` |
| Массив | `[T]` |
| Словарь | `map<T>` |
| Перечисление | `enum { "a" \| "b" }` |
| Объединение | `A \| B` |
| Имя класса | `PermissionRule` |
| Анонимный объект | `{ ... }` |

`$ref` в схеме не используется: генератор разворачивает ссылки в имена классов
или в анонимные объекты/объединения. Рекурсивные ссылки разворачиваются в `any`.

### 4.5. Генерация схемы из JSON Schema

Схема OpenCode (`https://opencode.ai/config.json`) конвертируется в DL-схему
(`examples/config.schema`) по правилам:

| JSON Schema | DL |
|-------------|-----|
| `object` + `properties` | `class Name { ... }` |
| `required` | поле без `?` |
| отсутствие в `required` | поле с `?` |
| `string`/`integer`/`number`/`boolean`/`null` | примитив |
| `array` + `items` | `[T]` |
| `additionalProperties` | `map<T>` (`true` → `map<any>`) |
| `enum` | `enum { "a" \| "b" }` |
| `oneOf` / `anyOf` | `A \| B` |
| `$ref: #/$defs/X` | имя класса `X` (если X — объект с `properties`), иначе тип раскрывается |
| `description` | `///` над полем |
| `default` | `= <литерал>` |

**Нормализация имён классов:** точки в именах `$defs` недопустимы, поэтому они
удаляются, а ведущий сегмент `Config` отбрасывается:

```
Permission.Rule          -> PermissionRule
Config.AgentEncoded      -> AgentEncoded
Mcp.LocalConfigEncoded   -> McpLocalConfigEncoded
ConfigV2.Reference.Git   -> ConfigV2ReferenceGit
```

Преобразование идемпотентно: имя без точек остаётся как есть.
Невыразимые ограничения (`pattern`, `minimum`, `patternProperties` и т.п.)
в схему не попадают и перечисляются в отчёте генератора.

### 4.6. Валидация

- Если документ объявляет класс (`json( $ ) => Config { ... }`), результат
  проверяется по этому классу загруженной схемы.
- Если сборка в `settings.dl` объявляет `schema`, проверка идёт по схеме сборки.
- Несоответствие типа — `E011 TypeMismatch`.

---

## 5. Функции и модули

### 5.1. Сигнатура и параметры

```dl
( $, port, host: "localhost" ) => {
    // тело
}

( $, name, npm, port, options: {} ) => {
    // тело
}

( $, name, type, url?, command?, headers?, timeout ) => {
    // тело
}
```

- Параметры разделяются запятыми.
- `$` — контекст вызывающего документа; всегда первый, если присутствует.
  При вызове передаётся неявно (раздел 5.5).
- Параметр с дефолтом: `имя: <литерал>`, например `options: {}`, `host: "localhost"`.
  Если аргумент не передан, параметр получает это значение.
- Опциональный параметр: `имя?`. Может быть не передан; в теле тогда имеет
  неопределённое значение (undefined).
- Порядок параметров значим для позиционного вызова (5.5).
- Неизвестный параметр при именованном вызове — `E009 UnknownParameter`.
- Отсутствующий обязательный параметр — `E010 MissingParameter`.

**Обязательный, опциональный, с дефолтом:**

| Запись | Обяз. | При отсутствии аргумента |
|--------|-------|--------------------------|
| `param` | да | `E010 MissingParameter` |
| `param?` | нет | undefined (поле с `?` не создаётся) |
| `param: literal` | нет | значение по умолчанию |

Комбинация `param?: literal` (опциональный параметр со значением по умолчанию)
в v2.2 не определена (раздел 11).

### 5.2. Тело функции и результат

Тело — последовательность инструкций:

| Инструкция | Смысл |
|------------|-------|
| `key: value;` | добавить поле в результат |
| `key = value;` | то же; предпочтительно для путей и объектов |
| `key?: value;` | условное поле: добавить, только если значение определено |
| `a.b = value;` | точечная нотация: поле по пути, вложенность создаётся неявно |
| `key: fn(args);` | поле, значение которого — результат вызова |
| `let name = expr;` | локальная привязка, в результат не попадает |
| `fn(args);` | вызов-инструкция; объект-результат вливается в текущий объект |
| `...expr;` | spread: объект-результат вливается с приоритетом (раздел 6) |

Результат тела — объект. Объекты, порождённые последовательными выражениями
(вызовами и spread), сливаются в один объект в порядке появления.

#### Возврат объекта

Объект возвращается только через field-инструкции: каждое поле — отдельная
инструкция `name: value;` (или `name = value;`). Объектный литерал `{ ... }`
в позиции инструкции недопустим — он является значением и должен стоять справа
от `:` или `=`; самостоятельный `{ ... };` — синтаксическая ошибка (`E001`).

```dl
// правильно: поля добавляются field-инструкциями
( $, name ) => {
    name: "{name}";
}

// неправильно: объектный литерал в позиции инструкции (E001)
( $, name ) => {
    { "{name}": name; }
}
```

#### Условные поля

`key?: value;` добавляет поле только тогда, когда значение **определено**:
не `null` и не undefined.

```dl
// examples/mcp/create-server.dl
( $, name, type, url?, command?, headers?, environment?, timeout ) => {
    type: type;
    url?: url;
    command?: command;
    headers?: headers;
    environment?: environment;
    timeout: timeout;
}
```

- Параметр не передан → undefined → поле отсутствует в результате.
- Передано `null` → поле отсутствует.
- Передано `""`, `0`, `false`, пустой массив/объект → значения определены,
  поле присутствует.
- Условное поле не участвует в слиянии, если не создано; конфликтов не порождает.

```dl
// examples/providers/models/localproxy.dl (фрагмент)
() => {
    let createmodel = import ./func/createmodel.dl;

    createmodel("free-gemini-2.5-pro");
    createmodel("free-minimax-m2.7");
    // ...
}
```

```dl
// examples/providers/models/func/createmodel.dl
( $, name ) => {
    "{name}": {
        name: "{name}";
    }
}
```

Каждый вызов `createmodel("...")` возвращает объект с одним ключом; объекты
последовательно сливаются в словарь моделей.

`;` после последней инструкции блока необязательна.

### 5.3. Локальные привязки

```dl
let makeoptions = import ./models/func/makeoptions.dl;
let createprovider = import ./createprovider.dl;
```

Привязка видна во всём теле функции ниже места объявления. В результат не попадает.

### 5.4. Импорт

```
import <путь>
```

- `import` **не принимает аргументов**: `import ./x.dl(args)` — синтаксическая
  ошибка (`E001`). Вызов — отдельная операция: сначала загрузить модуль,
  затем вызвать значение.
- Путь: `./...`, `../...` или абсолютный. Расширение `.dl`.
- В пути допустима интерполяция: `import ./models/{name}.dl`.
- Результат импорта — значение модуля: объект (если тело вернуло объект)
  или функция (если это модуль с параметрами).
- Импорт выполняется при вычислении: модуль с параметрами сам по себе ничего
  не порождает, пока его не вызвали.
- Один и тот же файл можно импортировать из разных модулей; циклический
  импорт — `E004 CircularImportError`; отсутствующий файл — `E002`.

```dl
// как значение поля
models: import ./models/{name}.dl;

// как значение привязки
let createprovider = import ./createprovider.dl;
```

### 5.4.1. Glob-импорт

```dl
import ./dir/*.dl
```

- Звёздочка `*` разрешена **только в последнем сегменте** пути.
- Результат — слияние всех найденных файлов через `merge` (строгое:
  одинаковые значения — `W001`, разные — `E003`).
- Сортировка по абсолютному пути, детерминированно.
- Модуль без параметров — вычисляется сразу; с параметрами — `E014`.
- Пустой каталог → `{}`.
- Интерполяция в пути разрешена: `import ./{dir}/*.dl`.

```dl
// Слияние всех файлов из каталога
models: import ./models/*.dl;

// Интерполяция в пути
let dir = "providers";
providers: import ./{dir}/*.dl;
```

**Ошибки:**

- `E014 GlobParameterizedModule` — модуль с параметрами в glob-импорте.
- `E003 ConflictError` — конфликт значений при слиянии.
- `W001 DuplicateKey` — одинаковые значения (предупреждение).

### 5.5. Вызовы

**Форма вызова:**

```
fn( позиционные..., { именованные... } )
```

- Позиционные аргументы идут первыми, в порядке сигнатуры.
- Объект именованных аргументов — последний и необязательный.
- `$` в аргументах не указывается: контекст подставляется неявно.
- Ключи объекта — имена параметров; порядок не важен.
- Значения — произвольные выражения (включая spread, раздел 6.3).

**Контекст `$`:**

- `$` — не позиционный аргумент и не передаётся при вызове; контекст
  пробрасывается неявно по цепочке вызовов.
- В сигнатуре `$` всегда первый (раздел 5.1), но в списке аргументов его нет:
  позиционные аргументы сопоставляются с параметрами **после** `$`.
- Вызов `fn($)` при отсутствии у `fn` пользовательских параметров даёт
  `E009 UnknownParameter: too many positional arguments`. Ключ `"$"` в объекте
  именованных аргументов также даёт `E009` (`'$' is passed implicitly`).

```dl
providers();   // правильно: контекст подставлен неявно
providers($);  // неправильно: E009 UnknownParameter
```

**Только позиционные:**

```dl
makeoptions(9625);
createmodel("deepseek/deepseek-v4.1-flash");
```

**Позиционные + именованные** (основная форма в примерах):

```dl
// examples/providers/entries/localproxy.dl (фрагмент)
localproxy: createprovider('localproxy', {
    npm: $.npm.openaicomp;
    port: 9625;
});
```

`'localproxy'` — позиционный аргумент `name`; `npm` и `port` — именованные.
`options` не передан и получает дефолт `{}`.

```dl
// examples/mcp/servers/deepwiki.dl (фрагмент)
deepwiki: createServer('deepwiki', {
    type: "remote";
    url: "https://mcp.deepwiki.com/mcp";
    timeout: timeout;
});
```

**Только именованные** — если позиционных аргументов нет, единственный объект
трактуется как объект именованных аргументов:

```dl
someModule({ a: 1; b: 2; });
```

Чтобы передать объект как позиционное значение, свяжите его через `let`
и передайте идентификатор: `let o = { a: 1; }; fn(o);`.

**Результат вызова:**

| Позиция | Поведение |
|---------|-----------|
| `fn(args);` — инструкция | объект-результат вливается в текущий объект |
| `key: fn(args);` | результат становится значением поля `key` |
| `let x = fn(args);` | результат связывается с `x`, в результат не попадает |

**Ограничения:**

- Объект именованных аргументов всегда последний; позиционные аргументы после
  него не допускаются (`E001`).
- Пропустить опциональный параметр в позиционной форме нельзя: для этого
  используется именованный объект.
- Прежняя форма вызова, где объект аргументов присваивался имени функции через
  `=`, в v2.2 отсутствует (`E001`). Вызов — это всегда `fn( ... )`.

### 5.6. Композиция модулей

```dl
// examples/providers/createprovider.dl
( $, name, npm, port, options: {} ) => {
    let makeoptions = import ./models/func/makeoptions.dl;

    npm: npm;
    name: "{name}";
    options: {
        ...makeoptions(port);
        ...options;
    };
    models: import ./models/{name}.dl;
}
```

```dl
// examples/providers/deepseek-proxy.dl
( $, name, npm, port ) => {
    let createprovider = import ./createprovider.dl;

    createprovider(name, {
        npm: npm;
        port: port;
        options: {
            toolCallFallback: "auto";
            useCompletionUrls: true;
        }
    });
}
```

`deepseek-proxy` не дублирует построение `options`: базовый URL создаёт
`makeoptions(port)` внутри `createprovider`, а собственные опции провайдера
передаются через `options` и перекрывают базу (spread). Вызов-инструкция
вливает результат `createprovider(...)` в результат `deepseek-proxy`.

---

## 6. Объекты и слияние

### 6.1. Поля

```dl
npm: npm;
name: "{name}";
default_agent: "jarvis";
url?: url;
mcp.servers = {
    // ...
};
```

`key: value;` и `key = value;` эквивалентны. `=` предпочтителен для точечных
путей и объектов; `:` — обычная форма для простых полей.

### 6.2. Поле со значением-вызовом

```dl
// examples/providers/entries/localproxy.dl (фрагмент)
localproxy: createprovider('localproxy', {
    npm: $.npm.openaicomp;
    port: 9625;
});
```

`key: fn(позиционные..., { именованные... });` — поле `key`, значением которого
становится результат вызова. Результат-объект не вливается в текущий объект,
а полностью становится значением поля.

### 6.3. Spread

```dl
options: {
    ...makeoptions(port);
    ...options;
};
```

`...expr;` вычисляет `expr` (обычно объект) и вливает его поля в текущий объект.
Spread выполняется в месте появления и **переопределяет** ранее заданные ключи.

### 6.4. Правила слияния

| Ситуация | Поведение |
|----------|-----------|
| Разные ключи | объединяются |
| Одинаковые ключи, одинаковые значения | `W001 DuplicateKey` + тихое слияние |
| Одинаковые ключи, разные значения | `E003 ConflictError` |
| Одинаковые пути в точечной нотации | как обычные ключи: `W001` / `E003` |
| Переопределение через `...expr` | разрешено, конфликтом не считается |
| Переопределение через `$.override()` | разрешено, конфликтом не считается |
| `$.override()` для неразрешаемого ключа | `E007 NotOverridableKey` |
| Использование `$` без контекста в сигнатуре | `E008 NoContext` |

**Порядок слияния:**

1. Вычислить тело модуля/документа сверху вниз.
2. Поля добавляются в результат; повтор ключа — по таблице выше.
3. Точечная нотация разворачивается в вложенные объекты в месте появления.
4. Последовательные выражения-объекты (вызовы, `...`) вливаются в текущий объект.
5. Spread `...expr` переопределяет ключи в месте появления, `$.override()` —
   после тела документа. Ни то, ни другое не порождает `E003`.

### 6.5. Явное переопределение

```dl
$.override().provider.localproxy.npm: $.npm.voidrot;
```

Форма `$.override()` применяется к ключу, помеченному как переопределяемый.
Механизм пометки ключей в v2.2 не определён (см. раздел 11); в примерах
используется только spread.

---

## 7. `settings.dl` и сборка

### 7.1. Структура

`settings.dl` — модуль с контекстом, без заголовка формата. Поля контекста
задают общие значения и список сборок:

```dl
// examples/settings.dl
( $ ) => {
    $.builds: [
        {
            source: "./configuration.dl";
            output: "./opencode.json";
            schema: "https://opencode.ai/config.json";
        }
    ];
    $.npm.openaicomp: "@ai-sdk/openai-compatible";
    $.npm.voidrot: "@voidrot/openai-featherless-compatible";
}
```

Значения `$.npm.*` доступны компилируемым документам как `$.npm.openaicomp`
и т.п.

### 7.2. Сборки

`$.builds[]` — массив объектов:

| Поле | Обяз. | Описание |
|------|-------|----------|
| `source` | да | путь к исходному `.dl` |
| `output` | да | путь к результату; формат определяется расширением (`.json`, `.toml`, `.yaml`) |
| `schema` | нет | URL JSON Schema для валидации результата |

### 7.3. Схема из URL

Если `schema` — URL:

1. Компилятор скачивает схему (`E012 SchemaFetchError` при ошибке).
2. Генерирует DL-схему `<имя>.schema`, где `<имя>` — имя файла из URL:
   `https://opencode.ai/config.json` → `config.schema`
   (`E013 SchemaGenerateError` при ошибке конвертации).
3. Кэширует файл схемы рядом с `settings.dl`.
4. Валидирует результат сборки по этой схеме.

### 7.4. Выбор файлов компиляции

1. `dl compile <file>` — компилируется указанный файл (аргумент имеет приоритет).
2. `dl compile` без аргумента — если в текущем каталоге есть `settings.dl`,
   его `builds[]` определяют набор сборок (`source`/`output`/`schema`);
   иначе ищется `configuration.dl` в текущем каталоге (без рекурсии).

---

## 8. CLI

```bash
dl compile [file]            # компиляция; без file — configuration.dl в текущем каталоге
dl eval <file>               # вычислить и напечатать результат, без записи файла
dl parse <file>              # разобрать, напечатать AST
dl schema <url> [-o file]    # скачать JSON Schema и сгенерировать DL-схему
dl --help                    # справка
```

- `dl schema` без `-o` пишет `<имя>.schema` в текущем каталоге.
- `dl compile` учитывает `settings.dl` (раздел 7.4).
- `dl eval` удобен для проверки слияния и интерполяции без записи в файл.

**Алгоритм `dl compile`:**

```
1. Есть аргумент → компилировать указанный файл.
2. Аргумента нет → если есть settings.dl с builds[] — компилировать каждую сборку,
   иначе — configuration.dl в cwd (без рекурсии).
3. Для каждой сборки:
   ├── разбор → AST
   ├── разрешение import (пути, интерполяция, циклы)
   ├── вычисление функций и слияние
   ├── валидация по схеме (если задана)
   └── сериализация в формат из заголовка/расширения output
```

---

## 9. Ошибки и предупреждения

### 9.1. Ошибки

| Код | Имя | Описание |
|-----|-----|----------|
| E001 | SyntaxError | Нарушение синтаксиса (в т.ч. `import ./x.dl(args)`, объект аргументов не последним, старая форма вызова) |
| E002 | ModuleNotFoundError | Файл импорта не найден |
| E003 | ConflictError | Одинаковые ключи/пути с разными значениями |
| E004 | CircularImportError | Циклический импорт |
| E005 | FormatNotFoundError | Неизвестный формат вывода |
| E006 | ParseError | Ошибка разбора AST |
| E007 | NotOverridableKey | Переопределение неразрешаемого ключа |
| E008 | NoContext | `$` используется без контекста в сигнатуре |
| E009 | UnknownParameter | Неизвестный параметр при именованном вызове |
| E010 | MissingParameter | Не передан обязательный параметр |
| E011 | TypeMismatch | Значение не соответствует типу схемы |
| E012 | SchemaFetchError | Не удалось скачать схему по URL |
| E013 | SchemaGenerateError | Не удалось сгенерировать DL-схему |

### 9.2. Предупреждения

| Код | Имя | Описание |
|-----|-----|----------|
| W001 | DuplicateKey | Дубликат ключа с одинаковым значением (слияние) |
| W002 | UnusedImport | Импорт не используется |
| W003 | DeprecatedSyntax | Устаревший синтаксис |

---

## 10. Примеры

### 10.1. Структура примеров

```
examples/
├── configuration.dl          # точка входа: 5 × let + spread-вызовы
├── settings.dl               # $.builds, $.npm.*
├── config.schema             # схема opencode.json
├── modules/                  # модули-разделы
│   ├── providers.dl
│   ├── mcp.dl
│   ├── permissions.dl
│   ├── agents.dl
│   └── runtime.dl
├── providers/
│   ├── createprovider.dl      # фабрика записи провайдера
│   ├── deepseek-proxy.dl      # вариант фабрики с собственными options
│   ├── entries/               # записи provider.<name>
│   │   ├── localproxy.dl
│   │   ├── deepseek-proxy.dl
│   │   └── zen-free.dl
│   └── models/                # словари models.<name>
│       ├── localproxy.dl
│       ├── deepseek-proxy.dl
│       ├── zen-free.dl
│       └── func/
│           ├── createmodel.dl
│           └── makeoptions.dl
├── mcp/
│   ├── create-server.dl       # фабрика конфигурации сервера
│   ├── default-timeout.dl     # общий timeout
│   └── servers/               # записи mcp.servers.<name>
│       ├── deepwiki.dl
│       ├── sequential-thinking.dl
│       ├── context7.dl
│       ├── lightpanda.dl
│       └── deploychan.dl
└── agents/                    # записи agent.<name> / agents.<name>
    ├── title.dl
    ├── general.dl
    └── jarvis.dl
```

Документ собирается из модулей: каждый модуль-раздел возвращает объект с одним
или несколькими верхними ключами, а `configuration.dl` только связывает их
через `let` и spread.

### 10.2. Точка входа

```dl
// examples/configuration.dl
json( $ ) => Config {
    let providers = import ./modules/providers.dl;
    let mcp = import ./modules/mcp.dl;
    let permissions = import ./modules/permissions.dl;
    let agents = import ./modules/agents.dl;
    let runtime = import ./modules/runtime.dl;

    ...providers();
    ...mcp();
    ...permissions();
    ...agents();
    ...runtime();
}
```

`$` не передаётся: у всех модулей в сигнатуре `( $ )`, контекст подставляется
неявно (раздел 5.5). Spread-вызовы выполняются в порядке появления, поэтому
поздние разделы переопределяют совпадающие ключи (раздел 6.3).

### 10.3. Модуль-раздел

```dl
// examples/modules/providers.dl
( $ ) => {
    let localproxy = import ../providers/entries/localproxy.dl;
    let deepseek = import ../providers/entries/deepseek-proxy.dl;
    let zenfree = import ../providers/entries/zen-free.dl;

    provider: {
        ...localproxy();
        ...deepseek();
        ...zenfree();
    };
}
```

Модуль возвращает объект field-инструкцией `provider: { ... };`; записи
провайдеров вливаются в него через spread.

### 10.4. Запись провайдера

```dl
// examples/providers/entries/localproxy.dl
( $ ) => {
    let createprovider = import ../createprovider.dl;

    localproxy: createprovider('localproxy', {
        npm: $.npm.openaicomp;
        port: 9625;
    });
}
```

Запись возвращает объект `{ localproxy: ... }`; он вливается в `provider` из
`modules/providers.dl`. Остальные записи (`deepseek-proxy`, `zen-free`)
устроены так же.

### 10.5. Цепочка провайдеров

```dl
// examples/providers/models/func/makeoptions.dl
( $, port, host: "localhost" ) => {
    baseURL: "http://{host}:{port}/v1";
}
```

```dl
// examples/providers/createprovider.dl
( $, name, npm, port, options: {} ) => {
    let makeoptions = import ./models/func/makeoptions.dl;

    npm: npm;
    name: "{name}";
    options: {
        ...makeoptions(port);
        ...options;
    };
    models: import ./models/{name}.dl;
}
```

```dl
// examples/providers/deepseek-proxy.dl
( $, name, npm, port ) => {
    let createprovider = import ./createprovider.dl;

    createprovider(name, {
        npm: npm;
        port: port;
        options: {
            toolCallFallback: "auto";
            useCompletionUrls: true;
        }
    });
}
```

```dl
// examples/providers/entries/deepseek-proxy.dl
( $ ) => {
    let deepseek = import ../deepseek-proxy.dl;

    deepseek-proxy: deepseek('deepseek-proxy', {
        npm: $.npm.voidrot;
        port: 9626;
    });
}
```

Запись провайдера передаёт только имя, npm-пакет и порт; `options` собирает
`createprovider` из `makeoptions(port)` и переданных значений.

### 10.6. Модели провайдера

```dl
// examples/providers/models/localproxy.dl
() => {
    let createmodel = import ./func/createmodel.dl;

    createmodel("free-gemini-2.5-pro");
    createmodel("free-minimax-m2.7");
    createmodel("free-claude-haiku-4-5-20251001");
    // ... остальные модели
}
```

Словарь моделей подключается как значение поля: `models: import ./models/{name}.dl;`.

### 10.7. MCP-серверы

```dl
// examples/mcp/create-server.dl
( $, name, type, url?, command?, headers?, environment?, timeout ) => {
    type: type;
    url?: url;
    command?: command;
    headers?: headers;
    environment?: environment;
    timeout: timeout;
}
```

```dl
// examples/mcp/servers/deepwiki.dl
( $ ) => {
    let createServer = import ../create-server.dl;
    let timeout = import ../default-timeout.dl;

    deepwiki: createServer('deepwiki', {
        type: "remote";
        url: "https://mcp.deepwiki.com/mcp";
        timeout: timeout;
    });
}
```

`createServer` возвращает плоский объект конфигурации сервера; внешнюю обёртку
по имени создаёт модуль `mcp/servers/*.dl`. `modules/mcp.dl` вливает их в
`mcp.servers` через spread. `default-timeout.dl` объявлен как `() => { ... }`,
поэтому импортируется готовым объектом — скобки при использовании не нужны.

### 10.8. Агенты

```dl
// examples/agents/jarvis.dl
( $ ) => {
    jarvis: {
        permissions: [
            { action: "edit"; resource: "*"; effect: "deny"; },
            { action: "shell"; resource: "*"; effect: "deny"; },
            { action: "websearch"; resource: "*"; effect: "deny"; },
            { action: "webfetch"; resource: "*"; effect: "deny"; },
            { action: "deepwiki_*"; resource: "*"; effect: "deny"; },
            { action: "context7_*"; resource: "*"; effect: "deny"; },
            { action: "lightpanda_*"; resource: "*"; effect: "deny"; }
        ];
    };
}
```

Файл возвращает объект `{ jarvis: ... }`; `modules/agents.dl` вливает его в
`agents`, а `title.dl` и `general.dl` — в `agent`.

### 10.9. Сборка

```dl
// examples/settings.dl
( $ ) => {
    $.builds: [
        {
            source: "./configuration.dl";
            output: "./opencode.json";
            schema: "https://opencode.ai/config.json";
        }
    ];
    $.npm.openaicomp: "@ai-sdk/openai-compatible";
    $.npm.voidrot: "@voidrot/openai-featherless-compatible";
}
```

### 10.10. Схема

```dl
// examples/config.schema (фрагмент; остальные классы опущены)
schema => {
    class McpLocalConfigEncoded {
        type: enum { "local" };
        command: [string];
        cwd?: string;
        environment?: map<string>;
        disabled?: boolean;
        codemode?: boolean;
        timeout?: {
            startup?: integer;
            catalog?: integer;
            execution?: integer;
        };
        protocol?: enum { "legacy" | "auto" | "2026-07-28" };
    };
}
```

---

## 11. Ограничения

- Нет управляющих конструкций: условий, циклов, арифметики. Язык только собирает данные.
- Один документ — один результат; один файл — один заголовок.
- `import` не принимает аргументов; вызов — отдельная операция, применяемая к
  загруженному значению.
- `$ref` в `.schema` не сохраняется: генератор разворачивает ссылки.
- Имена классов не содержат точек; нормализация выполняется генератором.
- Экранирование внутри строк (`\"`, `\n` и т.п.) в v2.2 не описано —
  используйте другой вид кавычек.
- Механизм пометки переопределяемых ключей (`$key` в v1) в v2.2 не определён;
  используйте spread (`...`) или `$.override()` (E007 для неразрешаемых ключей).
- Точечная нотация описана (раздел 3.4); неявно создаваемые промежуточные
  объекты не получают отдельных объявлений. Не-объектный промежуточный
  сегмент — `E003`.
- Опциональный параметр нельзя пропустить в позиционном вызове: используйте
  объект именованных аргументов. Комбинация `param?: literal` не определена.
- Объектный литерал в конце списка аргументов всегда трактуется как объект
  именованных аргументов; для позиционной передачи объекта используйте привязку.
- Позиционные аргументы после объекта именованных не допускаются.
- `$` не является позиционным аргументом и не передаётся при вызове: контекст
  пробрасывается неявно. `fn($)` при отсутствии у функции пользовательских
  параметров — `E009`, ключ `"$"` в именованном объекте — `E009`.
- Объект возвращается field-инструкциями (`name: value;`). Объектный литерал
  `{ ... }` в позиции инструкции недопустим (только как значение) — `E001`.
- Валидация выполняется только при наличии схемы (класс в заголовке или
  `schema` в сборке).
- Невыразимые в DL ограничения JSON Schema (`pattern`, `minimum`,
  `patternProperties`, `deprecated` и т.п.) теряются при генерации и
  перечисляются в отчёте генератора.
- Максимальная глубина вложенности и размер файла не ограничены (зависят от памяти).
- Кодировка UTF-8; переводы строк LF или CRLF; отступы не значимы.

---

## 12. История версий

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2026-10-25 | Начальная спецификация |
| 1.1 | 2026-10-25 | Контекст `$`, переопределяемые ключи `$key`, явное переопределение `$.override()` |
| 2.0 | 2026-10-25 | Финальный синтаксис: заголовок `json( $ ) => Config`, файлы схем `schema => { class ... }`, классы/типы и `///`; массивы без обязательных запятых; интерполяция в строках и путях импорта; функции с дефолтами, `let`, `import` без аргументов; позиционные и именованные вызовы, spread `...expr`; слияние W001/E003; `settings.dl` с `$.builds` и схемой по URL; CLI `dl schema`; ошибки E001–E013, предупреждения W001–W003. Имена классов без точек (`Permission.Rule` → `PermissionRule`). |
| 2.1 | 2026-10-25 | Форма вызова закреплена как `fn(позиционные..., { именованные... })`; `$` передаётся неявно; удалена прежняя форма вызова через `=` с объектом аргументов. Добавлены опциональные параметры `param?` и условные поля `key?: value;` (поле только при определённом значении). Добавлена точечная нотация `a.b = value;` с неявным созданием вложенности; `key: value;` и `key = value;` объявлены эквивалентными. `createprovider` больше не принимает `extra` (убран `...extra`); `deepseek-proxy` вызывает `createprovider(name, { ... })`; `mcp/default.dl` возвращает плоский объект конфигурации сервера без внешней обёртки по имени. Примеры синхронизированы с `examples/`. |
| **2.2** | **2026-10-25** | Модульная структура `examples/`: точка входа `configuration.dl` (5 × `let` + spread-вызовы) и модули-разделы `modules/*.dl`; записи провайдеров — `providers/entries/`, MCP-серверы — `mcp/servers/`, агенты — `agents/`. Фабрика MCP-сервера вынесена в `mcp/create-server.dl` (добавлен параметр `environment?`). Зафиксировано правило неявного `$`: `$` — не позиционный аргумент и не передаётся при вызове, `fn($)` даёт `E009`. Зафиксировано, что модуль возвращает объект через field-инструкции, а объектный литерал `{ ... }` в позиции инструкции недопустим. Обновлён раздел 10. |
| **2.3** | **2026-10-25** | **Glob-импорт**: `import ./dir/*.dl` — слияние всех файлов каталога через `merge` (строгое: W001/E003). Звёздочка только в последнем сегменте. Модуль без параметров — вычисляется сразу; с параметрами — `E014`. Пустой каталог → `{}`. Интерполяция в пути разрешена. Ошибка `E014 GlobParameterizedModule`. |
| **2.4** | **2026-10-25** | **Рефакторинг examples/**: consolidated MCP-серверы (`mcp/servers/*.dl` → `mcp/servers.dl`), агенты (`agents/*.dl` → `agents/agents.dl`). `modules/mcp.dl` и `modules/agents.dl` используют единый файл вместо множественных импортов. Glob-импорт для `providers/entries/*.dl` невозможен из-за E014 (модули с параметром `$`). Уменьшена фрагментация: 8 файлов → 2, дерево сборки показывает каждый путь 1 раз. |
````

## File: dl/cache.py
````python
"""Дисковый кэш разобранного AST DL.

AST (результат :func:`dl.parser.parse`) — чистая функция от текста файла,
поэтому его можно хранить на диске между запусками. Результат ``evaluate``
не кэшируется: он зависит от контекста и импортов.

Файл кэша — JSON::

    {"version": 1, "source": "<абсолютный путь>",
     "mtime_ns": 123, "size": 456, "ast": {...}}

Имя — ``sha256(<абсолютный путь>).hexdigest()[:16] + ".cache"`` в каталоге
``<directory>/.__cache__/``. Каталог создаётся лениво при первой записи.

Любое расхождение (версия, путь, mtime, размер) или битый JSON — промах
(``None``), без исключений: кэш не должен ломать сборку.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

CACHE_VERSION = 1
CACHE_DIR_NAME = ".__cache__"
SUFFIX = ".cache"


class DiskCache:
    """AST-кэш в каталоге ``<directory>/.__cache__``."""

    def __init__(self, directory: Path | str) -> None:
        self.directory = Path(directory)

    # ── пути ──────────────────────────────────────────────────────────────

    @property
    def cache_dir(self) -> Path:
        return self.directory / CACHE_DIR_NAME

    @staticmethod
    def _source_key(source: Path | str) -> str:
        return str(Path(source).resolve())

    def _path_for(self, source: Path | str) -> Path:
        digest = hashlib.sha256(self._source_key(source).encode("utf-8")).hexdigest()[
            :16
        ]
        return self.cache_dir / f"{digest}{SUFFIX}"

    # ── чтение ────────────────────────────────────────────────────────────

    def get(
        self,
        source: Path | str,
        stat: os.stat_result,
    ) -> dict | None:
        """Вернуть AST, если запись валидна и отпечаток совпал."""
        try:
            raw = self._path_for(source).read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict):
            return None

        if data.get("version") != CACHE_VERSION:
            return None
        if data.get("source") != self._source_key(source):
            return None
        if data.get("mtime_ns") != stat.st_mtime_ns:
            return None
        if data.get("size") != stat.st_size:
            return None

        ast = data.get("ast")
        if not isinstance(ast, dict):
            return None
        return ast

    # ── запись ────────────────────────────────────────────────────────────

    def put(
        self,
        source: Path | str,
        stat: os.stat_result,
        ast: dict,
    ) -> None:
        """Атомарно записать AST (временный файл + ``os.replace``)."""
        payload = {
            "version": CACHE_VERSION,
            "source": self._source_key(source),
            "mtime_ns": stat.st_mtime_ns,
            "size": stat.st_size,
            "ast": ast,
        }
        target = self._path_for(source)
        temp_name: str | None = None
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            handle_fd, temp_name = tempfile.mkstemp(
                dir=self.cache_dir, prefix=".tmp-", suffix=SUFFIX
            )
            with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=4)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
            temp_name = None
        except (OSError, TypeError, ValueError):
            # Кэш не участвует в результате сборки — молча пропускаем.
            return
        finally:
            if temp_name is not None:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass

    # ── обслуживание ──────────────────────────────────────────────────────

    def clear(self) -> None:
        """Удалить все ``*.cache`` из каталога кэша (каталог оставить)."""
        try:
            entries = list(self.cache_dir.iterdir())
        except OSError:
            return
        for entry in entries:
            if entry.is_file() and entry.suffix == SUFFIX:
                try:
                    entry.unlink()
                except OSError:
                    pass


__all__ = ["CACHE_DIR_NAME", "CACHE_VERSION", "DiskCache"]
````

## File: examples/agents/agents.dl
````
( $ ) => {
    agent: {
        jarvis: {
            permission: {
                edit: { "*": "deny"; };
                bash: { "*": "deny"; };
                websearch: "deny";
                webfetch: "deny";
                "deepwiki_*": "deny";
                "context7_*": "deny";
                "lightpanda_*": "deny";
            };
        };
        title: {
            model: "opencode/big-pickle";
        };
        general: {
            permission: {
                edit: {
                    "*": "allow";
                };
                bash: {
                    "*": "allow";
                    "*grep*": "deny";
                    "*find*": "deny";
                    "*npx*": "deny";
                    "*npm*": "deny";
                    "*sqlite*": "ask";
                };
                websearch: "deny";
                webfetch: "deny";
                skill: {
                    "agent-delegation": "deny";
                    "jarvis-cycles": "deny";
                };
            };
            tools: {
                "glob": false;
                "grep": false;
                "sequential-thinking_*": true;
                "deepwiki_*": true;
                "context7_*": true;
                "lightpanda_*": true;
                "memory_set": false;
                "memory_replace": false;
                "memory_list": false;
            };
        };
        explore: {
            disable: true;
        };
    };
}
````

## File: examples/mcp/create-server.dl
````
( $, name, type, url?, command?, headers?, environment?, timeout, description? ) => {
    type: type;
    enabled: true;
    url?: url;
    command?: command;
    headers?: headers;
    environment?: environment;
    description?: description;
    timeout: timeout;
}
````

## File: examples/mcp/servers.dl
````
( $ ) => {
    let createServer = import ./create-server.dl;

    deepwiki: createServer('deepwiki', {
        type: "remote";
        url: "https://mcp.deepwiki.com/mcp";
        timeout: 120000;
    });
    sequential-thinking: createServer('sequential-thinking', {
        type: "local";
        command: [
            "/home/kasiro/.npm-global/bin/mcp-server-sequential-thinking"
        ];
        timeout: 120000;
    });
    context7: createServer('context7', {
        type: "remote";
        url: "https://mcp.context7.com/mcp";
        headers: {
            Authorization: "Bearer ctx7sk-418a5f6a-2b9c-4caa-94e2-573821193500";
        };
        timeout: 120000;
    });
    lightpanda: createServer('lightpanda', {
        type: "local";
        command: [
            "/home/kasiro/.npm-global/bin/lightpanda-mcp"
        ];
        environment: {
            LIGHTPANDA_DISABLE_TELEMETRY: "true";
        };
        timeout: 60000;
        description: "Lightpanda headless browser — быстрый MCP скрапинг";
    });
    deploychan: createServer('deploychan', {
        type: "remote";
        url: "https://mcp.deploychan.webcam/mcp";
        timeout: 120000;
    });
}
````

## File: examples/modules/def.dl
````
( $ ) => {
    default_agent: "jarvis";
    instructions: [
        "~/.config/opencode/global-rules.md"
    ];
    share: "disabled";
}
````

## File: examples/modules/mcp.dl
````
( $ ) => {
    let servers = import ../mcp/servers.dl;

    mcp: servers();
}
````

## File: examples/modules/providers.dl
````
( $ ) => {
    let offprovider = import ../providers/offprovider.dl;
    let deepseek = import ../providers/deepseek-proxy.dl;
    let createprovider = import ../providers/createprovider.dl;
    let createmodel = import ../providers/func/createmodel.dl;

    provider: {
        localproxy: createprovider('localproxy', {
            npm: $.npm.openaicomp;
            port: 9625;
            models: {
                createmodel("free-gemini-2.5-pro");
                createmodel("free-minimax-m2.7");
                createmodel("free-claude-haiku-4-5-20251001");
                createmodel("free-gemini-2.5-flash");
                createmodel("free-qwen3.5-plus");
                createmodel("free-qwen3.5-flash");
                createmodel("free-minimax-m2.5");
                createmodel("free-gemini-2.5-flash-lite");
                createmodel("free-gemini-3-flash-preview");
            };
        });
        deepseek-proxy: deepseek('deepseek-proxy', {
            npm: $.npm.voidrot;
            port: 9626;
            models: {
                createmodel("deepseek/deepseek-v4.1-flash");
            };
        });
        zen-free: createprovider('zen-free', {
            npm: $.npm.openaicomp;
            port: 9877;
            models: {
                createmodel("muse-spark-1.3-contributor-free");
                createmodel("muse-spark-1.2-contributor-free");
                createmodel("mimo-v2.5-free");
                createmodel("mimo-v2.6-flash-free");
                createmodel("ling-3.0-flash-fin-free");
                createmodel("nemotron-3-ultra-free");
                createmodel("nemotron-3.5-lightning-free");
                createmodel("big-pickle");
                createmodel("space-bunny-free");
                createmodel("deepseek-v4.1-flash-free");
            };
        });
        anymodel: offprovider('anymodel', {
            npm: $.npm.openaicomp;
            baseurl: 'https://anymodel.org/v1';
            options: {
                apiKey: 'sk-dc9d4b7df36ba555-eldltg-e377fcc3';
            };
            models: {
                createmodel("am/gpt-oss-20b");
                createmodel("am/llama-3.2-11b-vision-instruct");
                createmodel("am/laguna-xs-2.1");
                createmodel("am/nemotron-3-nano-omni-30b-a3b-reasoning");
                createmodel("am/nemotron-3-ultra-550b-a55b");

                createmodel("ds/deepseek-v4-flash");
                createmodel("glm/glm-4.7");
                createmodel("glm/glm-5.3-flash");
                createmodel("kmc/k2.6");
                createmodel("xai/grok-4.20-0309-reasoning");
            };
        });
    };
}
````

## File: examples/modules/runtime.dl
````
( $ ) => {
    "lsp": {};
    "plugin": [
        "opencode-intellisearch",
        "@tarquinen/opencode-dcp@3.1.13",
        "opencode-agent-memory"
    ];
    "compaction": {
        "auto": false;
        "prune": false;
    };
    "tool_output": {
        "max_lines": 5000;
        "max_bytes": 204800;
    };
    "experimental": {
        "mcp_timeout": 120000;
    };
}
````

## File: examples/configuration.dl
````
json( $ ) => {
    let providers = import ./modules/providers.dl;
    let mcp = import ./modules/mcp.dl;
    let permissions = import ./modules/permissions.dl;
    let agents = import ./modules/agents.dl;
    let runtime = import ./modules/runtime.dl;
    let def = import ./modules/def.dl;

    "$schema": "{$.schema}";
    ...providers();
    ...def();
    ...permissions();
    ...mcp();
    ...agents();
    ...runtime();
}
````

## File: examples/settings.dl
````
( $ ) => {
    $.schema: "https://opencode.ai/config.json";
    $.builds: [
        {
            source: "./configuration.dl";
            output: "./opencode.json";
        }
    ];
    $.npm.openaicomp: "@ai-sdk/openai-compatible";
    $.npm.voidrot: "@voidrot/openai-featherless-compatible";
}
````

## File: examples/opencode.json
````json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "localproxy": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "localproxy",
      "options": {
        "baseURL": "http://localhost:9625/v1"
      },
      "models": {
        "free-gemini-2.5-pro": {
          "name": "free-gemini-2.5-pro"
        },
        "free-minimax-m2.7": {
          "name": "free-minimax-m2.7"
        },
        "free-claude-haiku-4-5-20251001": {
          "name": "free-claude-haiku-4-5-20251001"
        },
        "free-gemini-2.5-flash": {
          "name": "free-gemini-2.5-flash"
        },
        "free-qwen3.5-plus": {
          "name": "free-qwen3.5-plus"
        },
        "free-qwen3.5-flash": {
          "name": "free-qwen3.5-flash"
        },
        "free-minimax-m2.5": {
          "name": "free-minimax-m2.5"
        },
        "free-gemini-2.5-flash-lite": {
          "name": "free-gemini-2.5-flash-lite"
        },
        "free-gemini-3-flash-preview": {
          "name": "free-gemini-3-flash-preview"
        }
      }
    },
    "deepseek-proxy": {
      "npm": "@voidrot/openai-featherless-compatible",
      "name": "deepseek-proxy",
      "options": {
        "baseURL": "http://localhost:9626/v1",
        "toolCallFallback": "auto",
        "useCompletionUrls": true
      },
      "models": {
        "deepseek/deepseek-v4.1-flash": {
          "name": "deepseek/deepseek-v4.1-flash"
        }
      }
    },
    "zen-free": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "zen-free",
      "options": {
        "baseURL": "http://localhost:9877/v1"
      },
      "models": {
        "muse-spark-1.3-contributor-free": {
          "name": "muse-spark-1.3-contributor-free"
        },
        "muse-spark-1.2-contributor-free": {
          "name": "muse-spark-1.2-contributor-free"
        },
        "mimo-v2.5-free": {
          "name": "mimo-v2.5-free"
        },
        "mimo-v2.6-flash-free": {
          "name": "mimo-v2.6-flash-free"
        },
        "ling-3.0-flash-fin-free": {
          "name": "ling-3.0-flash-fin-free"
        },
        "nemotron-3-ultra-free": {
          "name": "nemotron-3-ultra-free"
        },
        "nemotron-3.5-lightning-free": {
          "name": "nemotron-3.5-lightning-free"
        },
        "big-pickle": {
          "name": "big-pickle"
        },
        "space-bunny-free": {
          "name": "space-bunny-free"
        },
        "deepseek-v4.1-flash-free": {
          "name": "deepseek-v4.1-flash-free"
        }
      }
    },
    "anymodel": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "anymodel",
      "options": {
        "baseURL": "https://anymodel.org/v1",
        "apiKey": "sk-dc9d4b7df36ba555-eldltg-e377fcc3"
      },
      "models": {
        "am/gpt-oss-20b": {
          "name": "am/gpt-oss-20b"
        },
        "am/llama-3.2-11b-vision-instruct": {
          "name": "am/llama-3.2-11b-vision-instruct"
        },
        "am/laguna-xs-2.1": {
          "name": "am/laguna-xs-2.1"
        },
        "am/nemotron-3-nano-omni-30b-a3b-reasoning": {
          "name": "am/nemotron-3-nano-omni-30b-a3b-reasoning"
        },
        "am/nemotron-3-ultra-550b-a55b": {
          "name": "am/nemotron-3-ultra-550b-a55b"
        },
        "ds/deepseek-v4-flash": {
          "name": "ds/deepseek-v4-flash"
        },
        "glm/glm-4.7": {
          "name": "glm/glm-4.7"
        },
        "glm/glm-5.3-flash": {
          "name": "glm/glm-5.3-flash"
        },
        "kmc/k2.6": {
          "name": "kmc/k2.6"
        },
        "xai/grok-4.20-0309-reasoning": {
          "name": "xai/grok-4.20-0309-reasoning"
        }
      }
    }
  },
  "default_agent": "jarvis",
  "instructions": [
    "~/.config/opencode/global-rules.md"
  ],
  "share": "disabled",
  "permission": {
    "bash": {
      "*find*": "deny",
      "*grep*": "deny",
      "*npm*": "deny",
      "*sqlite*": "ask",
      "*opencode*": "ask"
    },
    "glob": "deny",
    "grep": "deny",
    "websearch": "deny"
  },
  "mcp": {
    "deepwiki": {
      "type": "remote",
      "enabled": true,
      "url": "https://mcp.deepwiki.com/mcp",
      "timeout": 120000
    },
    "sequential-thinking": {
      "type": "local",
      "enabled": true,
      "command": [
        "/home/kasiro/.npm-global/bin/mcp-server-sequential-thinking"
      ],
      "timeout": 120000
    },
    "context7": {
      "type": "remote",
      "enabled": true,
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "Authorization": "Bearer ctx7sk-418a5f6a-2b9c-4caa-94e2-573821193500"
      },
      "timeout": 120000
    },
    "lightpanda": {
      "type": "local",
      "enabled": true,
      "command": [
        "/home/kasiro/.npm-global/bin/lightpanda-mcp"
      ],
      "environment": {
        "LIGHTPANDA_DISABLE_TELEMETRY": "true"
      },
      "description": "Lightpanda headless browser — быстрый MCP скрапинг",
      "timeout": 60000
    },
    "deploychan": {
      "type": "remote",
      "enabled": true,
      "url": "https://mcp.deploychan.webcam/mcp",
      "timeout": 120000
    }
  },
  "agent": {
    "jarvis": {
      "permission": {
        "edit": {
          "*": "deny"
        },
        "bash": {
          "*": "deny"
        },
        "websearch": "deny",
        "webfetch": "deny",
        "deepwiki_*": "deny",
        "context7_*": "deny",
        "lightpanda_*": "deny"
      }
    },
    "title": {
      "model": "opencode/big-pickle"
    },
    "general": {
      "permission": {
        "edit": {
          "*": "allow"
        },
        "bash": {
          "*": "allow",
          "*grep*": "deny",
          "*find*": "deny",
          "*npx*": "deny",
          "*npm*": "deny",
          "*sqlite*": "ask"
        },
        "websearch": "deny",
        "webfetch": "deny",
        "skill": {
          "agent-delegation": "deny",
          "jarvis-cycles": "deny"
        }
      },
      "tools": {
        "glob": false,
        "grep": false,
        "sequential-thinking_*": true,
        "deepwiki_*": true,
        "context7_*": true,
        "lightpanda_*": true,
        "memory_set": false,
        "memory_replace": false,
        "memory_list": false
      }
    },
    "explore": {
      "disable": true
    }
  },
  "lsp": {},
  "plugin": [
    "opencode-intellisearch",
    "@tarquinen/opencode-dcp@3.1.13",
    "opencode-agent-memory"
  ],
  "compaction": {
    "auto": false,
    "prune": false
  },
  "tool_output": {
    "max_lines": 5000,
    "max_bytes": 204800
  },
  "experimental": {
    "mcp_timeout": 120000
  }
}
````
