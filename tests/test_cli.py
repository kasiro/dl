"""Тесты CLI: schema, compile по settings, eval с валидацией (этап 3)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import toml
import yaml

from dl.cli import main
from dl.schema_gen import load_schema

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

MINI_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer"},
    },
    "required": ["name"],
}


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ─────────────────────────────── dl schema ──────────────────────────────────


def test_schema_command_generates_from_file_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    source = write(tmp_path / "src" / "config.json", json.dumps(MINI_SCHEMA))
    monkeypatch.chdir(tmp_path)
    capsys.readouterr()

    code = main(["schema", source.as_uri()])
    assert code == 0

    target = tmp_path / "config.schema"
    assert target.is_file()
    classes = load_schema(target)
    assert classes[0]["name"] == "Config"
    assert "Generated:" in capsys.readouterr().out


def test_schema_command_skips_existing_without_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    source = write(tmp_path / "config.json", json.dumps(MINI_SCHEMA))
    monkeypatch.chdir(tmp_path)

    assert main(["schema", source.as_uri()]) == 0
    target = tmp_path / "config.schema"
    before = target.read_text(encoding="utf-8")

    capsys.readouterr()
    assert main(["schema", source.as_uri()]) == 0
    assert "use --force" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == before

    # --force перегенерирует
    changed = dict(MINI_SCHEMA)
    changed["properties"] = {
        "name": {"type": "string"},
        "count": {"type": "integer"},
        "extra": {"type": "boolean"},
    }
    source.write_text(json.dumps(changed), encoding="utf-8")
    assert main(["schema", source.as_uri(), "--force"]) == 0
    assert "extra" in target.read_text(encoding="utf-8")


def test_schema_command_output_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    source = write(tmp_path / "config.json", json.dumps(MINI_SCHEMA))
    monkeypatch.chdir(tmp_path)

    assert main(["schema", source.as_uri(), "-o", "custom.schema"]) == 0
    assert (tmp_path / "custom.schema").is_file()
    assert not (tmp_path / "config.schema").exists()


# ─────────────────────────────── dl compile ─────────────────────────────────


def test_compile_without_argument_uses_settings_builds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    write(
        tmp_path / "settings.dl",
        """
        ( $ ) => {
            $.builds: [
                {
                    source: "./doc.dl";
                    output: "./result.json";
                }
                {
                    source: "./pyproject.dl";
                    output: "./pyproject.json";
                }
            ];
        }
        """,
    )
    write(tmp_path / "doc.dl", 'json => { a: 1; b: [1, 2]; }')

    monkeypatch.chdir(tmp_path)
    capsys.readouterr()
    code = main(["compile"])
    captured = capsys.readouterr()

    assert code == 0
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result == {"a": 1, "b": [1, 2]}
    # отсутствующий pyproject.dl не ломает сборку
    assert not (tmp_path / "pyproject.json").exists()
    assert "pyproject.dl" in captured.err
    assert "skipped" in captured.err


def test_compile_file_uses_build_output_and_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write(
        tmp_path / "schema.dl",
        """
        schema => {
            class Config {
                name: string;
                count?: integer;
            };
        }
        """,
    )
    write(
        tmp_path / "settings.dl",
        """
        ( $ ) => {
            $.builds: [
                {
                    source: "./doc.dl";
                    output: "./custom/out.json";
                    schema: "./schema.dl";
                }
            ];
        }
        """,
    )
    write(tmp_path / "doc.dl", 'json => Config { name: "ok"; count: 2; }')

    monkeypatch.chdir(tmp_path)
    code = main(["compile", "doc.dl"])

    assert code == 0
    output = tmp_path / "custom" / "out.json"
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8")) == {
        "name": "ok",
        "count": 2,
    }


def test_compile_file_fails_on_schema_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    write(
        tmp_path / "schema.dl",
        "schema => { class Config { name: string; count: integer; }; }",
    )
    write(
        tmp_path / "settings.dl",
        """
        ( $ ) => {
            $.builds: [
                { source: "./doc.dl"; output: "./out.json"; schema: "./schema.dl"; }
            ];
        }
        """,
    )
    write(tmp_path / "doc.dl", 'json => { name: "ok"; count: "nope"; }')

    monkeypatch.chdir(tmp_path)
    capsys.readouterr()
    code = main(["compile", "doc.dl"])
    captured = capsys.readouterr()

    assert code == 1
    assert (
        "E011 TypeMismatch: count: expected integer, got string"
        in captured.err
    )
    assert not (tmp_path / "out.json").exists()


def test_compile_without_settings_uses_configuration_dl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write(tmp_path / "configuration.dl", 'yaml => { app: { name: "dl"; }; }')

    monkeypatch.chdir(tmp_path)
    code = main(["compile"])

    assert code == 0
    data = yaml.safe_load((tmp_path / "configuration.yaml").read_text())
    assert data == {"app": {"name": "dl"}}


# ──────────────────────────────── dl eval ───────────────────────────────────


def test_eval_validates_when_schema_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    write(
        tmp_path / "schema.dl",
        "schema => { class Config { name: string; count: integer; }; }",
    )
    write(
        tmp_path / "settings.dl",
        """
        ( $ ) => {
            $.builds: [
                { source: "./doc.dl"; output: "./out.json"; schema: "./schema.dl"; }
            ];
        }
        """,
    )
    write(tmp_path / "doc.dl", 'json => { name: "ok"; count: 1; }')

    monkeypatch.chdir(tmp_path)
    capsys.readouterr()
    assert main(["eval", "doc.dl"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == {"name": "ok", "count": 1}

    write(tmp_path / "bad.dl", 'json => { count: 1; }')
    write(
        tmp_path / "settings.dl",
        """
        ( $ ) => {
            $.builds: [
                { source: "./bad.dl"; output: "./bad.json"; schema: "./schema.dl"; }
            ];
        }
        """,
    )
    capsys.readouterr()
    assert main(["eval", "bad.dl"]) == 1
    assert "E011 TypeMismatch: name: expected string, got missing" in (
        capsys.readouterr().err
    )


# ──────────────────────── 5. examples/configuration.dl ──────────────────────


def test_compile_examples_configuration_validates_against_config_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    """Сборка примера проверяется по examples/config.schema.

    Известное расхождение примера с официальной схемой (environment:
    boolean vs map<string>) допускается: тогда CLI обязан выдать конкретный
    E011 с путём. Схема при этом не подгоняется.
    """
    copy = tmp_path / "examples"
    shutil.copytree(EXAMPLES, copy)
    monkeypatch.chdir(copy)

    capsys.readouterr()
    code = main(["compile", "configuration.dl"])
    captured = capsys.readouterr()

    if code == 0:
        assert (copy / "opencode.json").is_file()
    else:
        assert code == 1
        assert "E011 TypeMismatch:" in captured.err
        assert "mcp.servers.lightpanda" in captured.err


# ───────────────────────────── сериализация ─────────────────────────────────


def test_compile_toml_nested_arrays_and_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write(
        tmp_path / "doc.dl",
        'toml => { nested: { a: 1; deep: { b: "x"; }; }; list: [1, 2]; none: null; }',
    )
    monkeypatch.chdir(tmp_path)

    assert main(["compile", "doc.dl", "-o", "out.toml"]) == 0
    data = toml.loads((tmp_path / "out.toml").read_text(encoding="utf-8"))
    assert data["nested"] == {"a": 1, "deep": {"b": "x"}}
    assert data["list"] == [1, 2]
    assert "none" not in data


def test_compile_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    write(tmp_path / "doc.dl", 'yaml => { app: { name: "тест"; }; }')
    monkeypatch.chdir(tmp_path)

    assert main(["compile", "doc.dl", "-o", "out.yaml"]) == 0
    data = yaml.safe_load((tmp_path / "out.yaml").read_text(encoding="utf-8"))
    assert data == {"app": {"name": "тест"}}


# ──────────────────────────────── help ──────────────────────────────────────


def test_help_lists_commands(capsys: pytest.CaptureFixture):
    assert main([]) == 1
    output = capsys.readouterr().out
    for command in ("compile", "parse", "eval", "schema"):
        assert command in output
