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
