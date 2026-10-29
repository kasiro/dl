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
