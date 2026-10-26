"""Тесты Resolver: отпечаток файла и дисковый кэш AST."""

from __future__ import annotations

import os
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from dl.cache import DiskCache
from dl.report import CACHED, BuildReporter, reset_reporter, set_reporter
from dl.resolver import Resolver


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def cache_files(directory: Path) -> list[Path]:
    return list((directory / ".__cache__").glob("*.cache"))


# ─────────────────────────── дисковый кэш AST ───────────────────────────────


def test_second_resolver_reads_ast_from_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = write(tmp_path / "mod.dl", "json => { value: 1; }")
    cache = DiskCache(tmp_path)

    first = Resolver(cache)
    assert first.load("mod.dl", tmp_path) == {"value": 1}
    assert cache_files(tmp_path), "первый разбор записал AST в .__cache__"

    def forbidden(*args, **kwargs):
        raise AssertionError("источник не должен читаться при попадании в кэш")

    # Кэш сам читает свой .cache через Path.read_text — запрещаем только
    # чтение исходника.
    original_read_text = Path.read_text

    def guarded_read_text(self: Path, *args, **kwargs):
        if self.resolve() == module.resolve():
            forbidden()
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    monkeypatch.setattr("dl.resolver.parse", forbidden)

    # Новый Resolver: in-memory пуст, значит AST берётся именно с диска.
    second = Resolver(cache)
    assert second.load("mod.dl", tmp_path) == {"value": 1}


def test_changed_file_invalidates_disk_cache(tmp_path: Path):
    module = write(tmp_path / "mod.dl", "json => { value: 1; }")
    cache = DiskCache(tmp_path)
    resolver = Resolver(cache)

    assert resolver.load("mod.dl", tmp_path) == {"value": 1}

    # Другой размер гарантирует другой отпечаток (mtime_ns на быстрых ФС
    # может совпасть с точностью до наносекунды).
    write(module, "json => { value: 222; }")
    assert resolver.load("mod.dl", tmp_path) == {"value": 222}

    # И новый Resolver тоже видит пересчитанный AST, а не старый кэш.
    fresh = Resolver(cache)
    assert fresh.load("mod.dl", tmp_path) == {"value": 222}


def test_disk_hit_is_reported_as_cached(tmp_path: Path):
    write(tmp_path / "mod.dl", "json => { value: 1; }")
    cache = DiskCache(tmp_path)
    assert Resolver(cache).load("mod.dl", tmp_path) == {"value": 1}

    stream = StringIO()
    reporter = BuildReporter(
        console=Console(file=stream, force_terminal=False, width=100)
    )
    reporter.start(tmp_path / "root.dl", tmp_path / "out.json")
    token = set_reporter(reporter)
    try:
        assert Resolver(cache).load("mod.dl", tmp_path) == {"value": 1}
    finally:
        reset_reporter(token)
        reporter.finish()

    key = str((tmp_path / "mod.dl").resolve())
    assert reporter._nodes[key].status == CACHED


# ─────────────────────── in-memory кэш по отпечатку ────────────────────────


def test_in_memory_cache_is_invalidated_by_change(tmp_path: Path):
    module = write(tmp_path / "mod.dl", "json => { value: 1; }")
    resolver = Resolver()  # без дискового кэша

    assert resolver.load("mod.dl", tmp_path) == {"value": 1}
    write(module, "json => { value: 222; }")
    assert resolver.load("mod.dl", tmp_path) == {"value": 222}


def test_in_memory_hit_does_not_touch_disk(tmp_path: Path):
    write(tmp_path / "mod.dl", "json => { value: 1; }")
    resolver = Resolver()  # без дискового кэша

    assert resolver.load("mod.dl", tmp_path) == {"value": 1}
    assert not (tmp_path / ".__cache__").exists()

    # Повторный вызов — из памяти; файл кэша по-прежнему не появился.
    assert resolver.load("mod.dl", tmp_path) == {"value": 1}
    assert not (tmp_path / ".__cache__").exists()


def test_independent_resolvers_have_independent_memory(tmp_path: Path):
    write(tmp_path / "mod.dl", "json => { value: 1; }")
    first = Resolver()
    second = Resolver()

    assert first.load("mod.dl", tmp_path) == {"value": 1}
    assert second.load("mod.dl", tmp_path) == {"value": 1}
    assert first._cache and second._cache


def test_missing_module_reports_e002(tmp_path: Path):
    from dl.errors import ModuleNotFoundError as DLErrorModuleNotFound

    with pytest.raises(DLErrorModuleNotFound) as info:
        Resolver().load("nope.dl", tmp_path)
    assert "E002" in str(info.value)


def test_mtime_only_change_is_a_different_fingerprint(tmp_path: Path):
    module = write(tmp_path / "mod.dl", "json => { value: 1; }")
    resolver = Resolver()

    assert resolver.load("mod.dl", tmp_path) == {"value": 1}
    before = os.stat(module)
    # Содержимое/размер те же, меняется только mtime_ns.
    os.utime(module, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000))
    assert resolver.load("mod.dl", tmp_path) == {"value": 1}
    assert len(resolver._cache) == 2
