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
