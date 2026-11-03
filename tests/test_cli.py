"""Тесты CLI: build через flake.build_to_files(), eval (этап 3)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import toml
import yaml

from dl.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ─────────────────────────────── dl build ─────────────────────────────────


def test_build_without_argument_uses_configuration_dl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    """build без аргументов использует configuration.dl."""
    write(
        tmp_path / "configuration.dl",
        """
        ( $, $config ) => {
            import ./modules.dl;
            outputs: {
                "result.json": {
                    format: "json";
                    value: $config;
                };
            };
        }
        """,
    )
    write(tmp_path / "modules.dl", 'json => { a: 1; b: [1, 2]; }')

    monkeypatch.chdir(tmp_path)
    capsys.readouterr()
    code = main(["build"])

    assert code == 0
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result["a"] == 1
    assert result["b"] == [1, 2]


def test_build_file_uses_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """build с аргументом использует outputs из flake-документа."""
    write(
        tmp_path / "config.dl",
        """
        ( $, $config ) => {
            import ./modules.dl;
            outputs: {
                "custom/out.json": {
                    format: "json";
                    value: $config;
                };
            };
        }
        """,
    )
    write(tmp_path / "modules.dl", 'json => { name: "ok"; count: 2; }')

    monkeypatch.chdir(tmp_path)
    code = main(["build", "config.dl"])

    assert code == 0
    output = tmp_path / "custom" / "out.json"
    assert output.is_file()
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["name"] == "ok"
    assert result["count"] == 2


def test_build_without_settings_uses_configuration_dl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """build без settings.dl использует configuration.dl с простым содержимым."""
    write(
        tmp_path / "configuration.dl",
        """
        ( $, $config ) => {
            import ./modules.dl;
            outputs: {
                "configuration.yaml": {
                    format: "yaml";
                    value: $config;
                };
            };
        }
        """,
    )
    write(tmp_path / "modules.dl", 'json => { app: { name: "dl"; }; }')

    monkeypatch.chdir(tmp_path)
    code = main(["build"])

    assert code == 0
    data = yaml.safe_load((tmp_path / "configuration.yaml").read_text())
    assert data == {"app": {"name": "dl"}}


# ──────────────────────────────── dl eval ───────────────────────────────────


def test_eval_prints_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    write(tmp_path / "doc.dl", 'json => { name: "ok"; count: 1; }')

    monkeypatch.chdir(tmp_path)
    capsys.readouterr()
    assert main(["eval", "doc.dl"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == {"name": "ok", "count": 1}





# ───────────────────────────── сериализация ─────────────────────────────────


def test_build_toml_nested_arrays_and_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write(
        tmp_path / "config.dl",
        """
        ( $, $config ) => {
            import ./modules.dl;
            outputs: {
                "out.toml": {
                    format: "toml";
                    value: $config;
                };
            };
        }
        """,
    )
    write(
        tmp_path / "modules.dl",
        'json => { nested: { a: 1; deep: { b: "x"; }; }; list: [1, 2]; none: null; }',
    )
    monkeypatch.chdir(tmp_path)

    assert main(["build", "config.dl"]) == 0
    data = toml.loads((tmp_path / "out.toml").read_text(encoding="utf-8"))
    assert data["nested"] == {"a": 1, "deep": {"b": "x"}}
    assert data["list"] == [1, 2]
    assert "none" not in data


def test_build_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    write(
        tmp_path / "config.dl",
        """
        ( $, $config ) => {
            import ./modules.dl;
            outputs: {
                "out.yaml": {
                    format: "yaml";
                    value: $config;
                };
            };
        }
        """,
    )
    write(tmp_path / "modules.dl", 'json => { app: { name: "тест"; }; }')
    monkeypatch.chdir(tmp_path)

    assert main(["build", "config.dl"]) == 0
    data = yaml.safe_load((tmp_path / "out.yaml").read_text(encoding="utf-8"))
    assert data == {"app": {"name": "тест"}}


# ──────────────────────────────── help ──────────────────────────────────────


def test_help_lists_commands(capsys: pytest.CaptureFixture):
    assert main([]) == 1
    output = capsys.readouterr().out
    for command in ("build", "parse", "eval"):
        assert command in output
