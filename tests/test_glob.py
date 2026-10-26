"""Тесты glob-импорта в DL v2.3."""

from __future__ import annotations

from pathlib import Path

import pytest

from dl.errors import GlobParameterizedModule
from dl.evaluator import evaluate_file
from dl.resolver import Resolver


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ─────────────────────────── базовые тесты ───────────────────────────────


def test_glob_import_empty_directory(tmp_path: Path):
    """Пустой каталог → {}."""
    (tmp_path / "empty").mkdir()
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./empty/*.dl; }",
    )
    result = evaluate_file(config)
    assert result == {"models": {}}


def test_glob_import_single_file(tmp_path: Path):
    """Один файл — работает как обычный import."""
    (tmp_path / "mods").mkdir()
    write(
        tmp_path / "mods" / "mod.dl",
        "() => { value: 1; }",
    )
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./mods/*.dl; }",
    )
    result = evaluate_file(config)
    assert result == {"models": {"value": 1}}


def test_glob_import_merge_multiple_files(tmp_path: Path):
    """Слияние нескольких файлов через merge."""
    (tmp_path / "mods").mkdir()
    write(
        tmp_path / "mods" / "a.dl",
        "() => { a: 1; }",
    )
    write(
        tmp_path / "mods" / "b.dl",
        "() => { b: 2; }",
    )
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./mods/*.dl; }",
    )
    result = evaluate_file(config)
    assert result == {"models": {"a": 1, "b": 2}}


def test_glob_import_sorted_deterministically(tmp_path: Path):
    """Сортировка по абсолютному пути, детерминированно."""
    (tmp_path / "mods").mkdir()
    write(
        tmp_path / "mods" / "z.dl",
        "() => { z: 26; }",
    )
    write(
        tmp_path / "mods" / "a.dl",
        "() => { a: 1; }",
    )
    write(
        tmp_path / "mods" / "m.dl",
        "() => { m: 13; }",
    )
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./mods/*.dl; }",
    )
    result = evaluate_file(config)
    # Слияние детерминировано, порядок a, m, z
    assert result == {"models": {"a": 1, "m": 13, "z": 26}}


def test_glob_import_subdirectory(tmp_path: Path):
    """Glob-импорт из подкаталога."""
    (tmp_path / "mods").mkdir()
    write(
        tmp_path / "mods" / "first.dl",
        "() => { first: 1; }",
    )
    write(
        tmp_path / "mods" / "second.dl",
        "() => { second: 2; }",
    )
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./mods/*.dl; }",
    )
    result = evaluate_file(config)
    assert result == {"models": {"first": 1, "second": 2}}


def test_glob_import_parameterized_module_error(tmp_path: Path):
    """Модуль с параметрами — ошибка E014."""
    write(
        tmp_path / "bad.dl",
        "(name) => { name: name; }",
    )
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./*.dl; }",
    )
    with pytest.raises(GlobParameterizedModule) as info:
        evaluate_file(config)
    assert "E014" in str(info.value)


def test_glob_import_conflict_error(tmp_path: Path):
    """Конфликт значений — E003."""
    (tmp_path / "mods").mkdir()
    write(
        tmp_path / "mods" / "a.dl",
        "() => { value: 1; }",
    )
    write(
        tmp_path / "mods" / "b.dl",
        "() => { value: 2; }",
    )
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./mods/*.dl; }",
    )
    from dl.errors import ConflictError

    with pytest.raises(ConflictError) as info:
        evaluate_file(config)
    assert "E003" in str(info.value)


def test_glob_import_same_value_warning(tmp_path: Path, caplog):
    """Одинаковые значения — W001 (warning)."""
    (tmp_path / "mods").mkdir()
    write(
        tmp_path / "mods" / "a.dl",
        "() => { value: 42; }",
    )
    write(
        tmp_path / "mods" / "b.dl",
        "() => { value: 42; }",
    )
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./mods/*.dl; }",
    )
    import logging

    with caplog.at_level(logging.WARNING, logger="dl"):
        result = evaluate_file(config)
    assert result == {"models": {"value": 42}}
    assert "W001" in caplog.text


def test_glob_import_nested_object_merge(tmp_path: Path):
    """Глубокое слияние вложенных объектов."""
    (tmp_path / "mods").mkdir()
    write(
        tmp_path / "mods" / "a.dl",
        "() => { config: { a: 1; }; }",
    )
    write(
        tmp_path / "mods" / "b.dl",
        "() => { config: { b: 2; }; }",
    )
    config = write(
        tmp_path / "config.dl",
        "json => { models: import ./mods/*.dl; }",
    )
    result = evaluate_file(config)
    assert result == {"models": {"config": {"a": 1, "b": 2}}}


def test_glob_import_with_interpolation(tmp_path: Path):
    """Интерполяция в пути импорта."""
    (tmp_path / "providers").mkdir()
    write(
        tmp_path / "providers" / "localproxy.dl",
        "() => { localproxy: { name: 'localproxy'; }; }",
    )
    write(
        tmp_path / "providers" / "openai.dl",
        "() => { openai: { name: 'openai'; }; }",
    )
    config = write(
        tmp_path / "config.dl",
        """
        json( $ ) => {
            let dir = "providers";
            models: import ./{dir}/*.dl;
        }
        """,
    )
    result = evaluate_file(config)
    assert "models" in result
    assert "localproxy" in result["models"]
    assert "openai" in result["models"]
