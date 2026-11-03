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


def _is_priority_value(value: Any) -> bool:
    """Проверить, является ли значение приоритетным объектом.

    Приоритетное значение имеет вид {priority: int, value: any}.
    """
    return (
        isinstance(value, dict)
        and "priority" in value
        and "value" in value
        and isinstance(value["priority"], int)
    )


def _extract_priority_value(value: Any) -> tuple[int, Any] | None:
    """Извлечь (priority, value) из приоритетного объекта или None.

    Возвращает кортеж (priority, wrapped_value) если value имеет структуру
    {priority: int, value: any}, иначе None.
    """
    if _is_priority_value(value):
        return (value["priority"], value["value"])
    return None


def _merge_priority_values(
    base_val: Any,
    override_val: Any,
    path: str,
) -> Any:
    """Слить два значения с учётом приоритетов.

    Правила:
    - Если оба значения приоритетные: выигрывает меньший priority (0 > 1000).
      При равных priority — E003.
    - Если одно приоритетное, другое обычное: обычное переопределяет (поздний wins).
    - Если оба обычные: переопределение (поздний wins).
    - Вложенные объекты сливаются рекурсивно.
    """
    base_priority = _extract_priority_value(base_val)
    override_priority = _extract_priority_value(override_val)

    if base_priority is not None and override_priority is not None:
        # Оба приоритетные
        base_prio, base_inner = base_priority
        override_prio, override_inner = override_priority

        if base_prio < override_prio:
            # Базовое значение имеет меньший priority (выше приоритет)
            return _copy_value(base_val)
        elif override_prio < base_prio:
            # Переопределяющее значение имеет меньший priority
            return _copy_value(override_val)
        else:
            # Равные priority — конфликт
            raise ConflictError(
                f"E003 ConflictError: conflicting priorities at {path}: "
                f"both have priority {base_prio}"
            )
    elif override_priority is not None:
        # Только override приоритетное — обычное значение переопределяет
        return _copy_value(override_val)
    elif base_priority is not None:
        # Только base приоритетное — переопределяем обычным
        return _copy_value(override_val)
    else:
        # Оба обычные — переопределение
        return _copy_value(override_val)


def deep_merge(target: dict, source: dict, path: str = "") -> dict:
    """Слить ``source`` в ``target`` с переопределением (без W001/E003).

    Используется для ``...expr`` и вызовов-инструкций (раздел 6.3).
    Поддерживает приоритетные значения вида {priority: int, value: any}.
    """
    for key, value in source.items():
        full = _join(path, key)
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # Проверяем, не являются ли оба значения приоритетными объектами
            if _is_priority_value(target[key]) and _is_priority_value(value):
                target[key] = _merge_priority_values(target[key], value, full)
            else:
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
