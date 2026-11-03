"""Сериализация вычисленного значения DL в json/toml/yaml."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import toml
import yaml

from .errors import FormatNotFoundError, ParseError

if TYPE_CHECKING:
    from .evaluator import Function

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
    """Сериализовать словарь в заданный формат (``E005`` при неизвестном).
    
    Если передан Function — ошибка (нужно вызвать collect()).
    """
    from .evaluator import Function
    
    if isinstance(value, Function):
        raise ParseError(
            "E006 ParseError: value is a Function (module); "
            "use dl.modules.collect() to assemble the configuration"
        )
    
    if not isinstance(value, dict):
        raise ParseError(
            f"E006 ParseError: expected dict for serialization, "
            f"got {type(value).__name__}"
        )
    
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
