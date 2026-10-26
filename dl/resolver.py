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
