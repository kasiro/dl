"""DL v2.2 — компилятор конфигураций.

Публичный API:

    parse(source, filename="<input>") -> dict
    evaluate(ast, base_dir, context=None) -> dict | Function
    merge(base, override) -> dict
    serialize(value, format) -> str
"""

from .evaluator import evaluate
from .merger import merge
from .parser import parse
from .serializer import serialize

__all__ = [
    "parse",
    "evaluate",
    "merge",
    "serialize",
]
__version__ = "0.1.0"
