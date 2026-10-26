"""Тесты дискового AST-кэша (dl.cache)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from dl.cache import CACHE_DIR_NAME, CACHE_VERSION, DiskCache
from dl.cli import main


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def cache_files(directory: Path) -> list[Path]:
    return list((directory / CACHE_DIR_NAME).glob("*.cache"))


# ────────────────────────────── запись/чтение ───────────────────────────────


def test_put_get_roundtrip_creates_directory_lazily(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    ast = {"kind": "config", "body": [{"kind": "field"}]}

    assert not (tmp_path / CACHE_DIR_NAME).exists()
    cache.put(source, os.stat(source), ast)

    assert (tmp_path / CACHE_DIR_NAME).is_dir()
    assert cache.get(source, os.stat(source)) == ast


def test_file_name_is_sha256_prefix(tmp_path: Path):
    import hashlib

    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    cache.put(source, os.stat(source), {"kind": "config", "body": []})

    expected = (
        hashlib.sha256(str(source.resolve()).encode("utf-8")).hexdigest()[:16]
        + ".cache"
    )
    assert [path.name for path in cache_files(tmp_path)] == [expected]


# ──────────────────────────────── инвалидация ───────────────────────────────


def test_miss_after_mtime_change(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    before = os.stat(source)
    cache.put(source, before, {"kind": "config", "body": []})

    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000))
    assert cache.get(source, os.stat(source)) is None


def test_miss_after_size_change(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    cache.put(source, os.stat(source), {"kind": "config", "body": []})
    before_size = os.stat(source).st_size

    write(source, "json => { a: 123456; }")
    assert os.stat(source).st_size != before_size
    assert cache.get(source, os.stat(source)) is None


def test_miss_on_version_change(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    cache.put(source, os.stat(source), {"kind": "config", "body": []})

    path = cache_files(tmp_path)[0]
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["version"] = CACHE_VERSION + 1
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert cache.get(source, os.stat(source)) is None


def test_miss_on_source_change(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    other = write(tmp_path / "other.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    cache.put(source, os.stat(source), {"kind": "config", "body": []})

    path = cache_files(tmp_path)[0]
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["source"] = str(other.resolve())
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert cache.get(source, os.stat(source)) is None


# ───────────────────────────────── битый JSON ───────────────────────────────


def test_broken_json_returns_none(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    cache.put(source, os.stat(source), {"kind": "config", "body": []})

    cache_files(tmp_path)[0].write_text("{not json", encoding="utf-8")
    assert cache.get(source, os.stat(source)) is None


def test_missing_file_returns_none(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    assert cache.get(source, os.stat(source)) is None


# ──────────────────────────────── атомарность ───────────────────────────────


def test_put_is_atomic_and_leaves_no_temp_files(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    ast = {"kind": "config", "body": [{"kind": "field"}]}

    cache.put(source, os.stat(source), ast)

    entries = list((tmp_path / CACHE_DIR_NAME).iterdir())
    assert len(entries) == 1
    assert entries[0].suffix == ".cache"
    payload = json.loads(entries[0].read_text(encoding="utf-8"))
    assert payload["ast"] == ast
    assert payload["version"] == CACHE_VERSION
    assert payload["source"] == str(source.resolve())


def test_clear_removes_only_cache_files(tmp_path: Path):
    source = write(tmp_path / "mod.dl", "json => { a: 1; }")
    cache = DiskCache(tmp_path)
    cache.put(source, os.stat(source), {"kind": "config", "body": []})
    keep = cache.cache_dir / "keep.txt"
    keep.write_text("keep", encoding="utf-8")

    cache.clear()

    assert cache_files(tmp_path) == []
    assert keep.is_file()
    assert cache.get(source, os.stat(source)) is None


# ──────────────────────────────── CLI-флаги ─────────────────────────────────


def test_compile_uses_cache_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write(tmp_path / "mod.dl", "json => { value: 1; }")
    write(
        tmp_path / "doc.dl",
        "json => { let m = import ./mod.dl; nested: m; }",
    )
    monkeypatch.chdir(tmp_path)

    assert main(["compile", "doc.dl"]) == 0
    assert cache_files(tmp_path), "по умолчанию импорт пишется в .__cache__"


def test_no_cache_does_not_create_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write(tmp_path / "mod.dl", "json => { value: 1; }")
    write(
        tmp_path / "doc.dl",
        "json => { let m = import ./mod.dl; nested: m; }",
    )
    monkeypatch.chdir(tmp_path)

    assert main(["compile", "doc.dl", "--no-cache"]) == 0
    assert not (tmp_path / CACHE_DIR_NAME).exists()


def test_eval_no_cache_does_not_create_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    write(tmp_path / "mod.dl", "json => { value: 1; }")
    write(
        tmp_path / "doc.dl",
        "json => { let m = import ./mod.dl; nested: m; }",
    )
    monkeypatch.chdir(tmp_path)
    capsys.readouterr()

    assert main(["eval", "doc.dl", "--no-cache"]) == 0
    assert not (tmp_path / CACHE_DIR_NAME).exists()
    assert json.loads(capsys.readouterr().out) == {"nested": {"value": 1}}


def test_parse_does_not_create_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    write(
        tmp_path / "doc.dl",
        "json => { let m = import ./mod.dl; nested: m; }",
    )
    monkeypatch.chdir(tmp_path)
    capsys.readouterr()

    assert main(["parse", "doc.dl"]) == 0
    assert not (tmp_path / CACHE_DIR_NAME).exists()
