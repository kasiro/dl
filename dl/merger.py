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
