"""Тесты вычислителя и слияния DL v2.1 (этап 2)."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from dl.errors import (
    CircularImportError,
    ConflictError,
    DLContextError,
    MissingParameterError,
    UnknownParameterError,
)
from dl.evaluator import (
    Function,
    call_value,
    evaluate,
    evaluate_file,
    evaluate_settings,
)
from dl.parser import parse

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


# ─────────────────────────────── помощники ──────────────────────────────────


def load_example(name: str):
    path = EXAMPLES / name
    return path, parse(path.read_text(encoding="utf-8"), str(path))


def evaluate_example(name: str, context: dict | None = None):
    path, ast = load_example(name)
    return evaluate(ast, path.parent, context)


def write_module(tmp_path: Path, name: str, source: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def settings_context() -> dict:
    path, ast = load_example("settings.dl")
    return evaluate_settings(ast, path.parent)


@pytest.fixture(scope="module")
def configuration(settings_context: dict) -> dict:
    return evaluate_example("configuration.dl", settings_context)


# ────────────────────────────── 1. configuration ────────────────────────────


def test_configuration_structure(configuration: dict) -> None:
    localproxy = configuration["provider"]["localproxy"]
    assert localproxy["npm"] == "@ai-sdk/openai-compatible"
    assert localproxy["name"] == "localproxy"
    assert localproxy["options"]["baseURL"] == "http://localhost:9625/v1"
    assert len(localproxy["models"]) == 9

    deepwiki = configuration["mcp"]["servers"]["deepwiki"]
    assert deepwiki["type"] == "remote"
    assert deepwiki["url"] == "https://mcp.deepwiki.com/mcp"
    assert deepwiki["timeout"] == {"catalog": 120000, "execution": 120000}

    permissions = configuration["agents"]["jarvis"]["permissions"]
    assert permissions[0] == {"action": "edit", "resource": "*", "effect": "deny"}
    assert len(permissions) == 7


# ───────────────────────────── 2. models/localproxy ─────────────────────────


def test_localproxy_models_module() -> None:
    path, ast = load_example("providers/models/localproxy.dl")
    value = evaluate(ast, path.parent)
    assert isinstance(value, Function)

    models = call_value(value, [], None, {})
    assert len(models) == 9
    assert models["free-gemini-2.5-pro"] == {"name": "free-gemini-2.5-pro"}
    assert models["free-gemini-3-flash-preview"] == {
        "name": "free-gemini-3-flash-preview"
    }


# ─────────────────────────── 3. опциональные поля ───────────────────────────


def test_optional_field_presence(configuration: dict) -> None:
    servers = configuration["mcp"]["servers"]

    assert servers["deepwiki"]["url"] == "https://mcp.deepwiki.com/mcp"

    sequential = servers["sequential-thinking"]
    assert "url" not in sequential
    assert sequential["command"] == [
        "/home/kasiro/.npm-global/bin/mcp-server-sequential-thinking"
    ]

    lightpanda = servers["lightpanda"]
    assert "url" not in lightpanda
    assert lightpanda["environment"] == {"LIGHTPANDA_DISABLE_TELEMETRY": "true"}


# ─────────────────────────── 4. deepseek-proxy spread ───────────────────────


def test_deepseek_proxy_options(configuration: dict) -> None:
    proxy = configuration["provider"]["deepseek-proxy"]
    assert proxy["npm"] == "@voidrot/openai-featherless-compatible"
    assert proxy["options"] == {
        "baseURL": "http://localhost:9626/v1",
        "toolCallFallback": "auto",
        "useCompletionUrls": True,
    }
    assert proxy["models"] == {
        "deepseek/deepseek-v4.1-flash": {"name": "deepseek/deepseek-v4.1-flash"}
    }


# ──────────────────────────── 5. E003 конфликт ──────────────────────────────


def test_conflict_different_values(tmp_path: Path) -> None:
    path = write_module(tmp_path, "conflict.dl", 'json => { a: 1; a: 2; }')
    with pytest.raises(ConflictError) as error:
        evaluate_file(path)
    assert "E003" in str(error.value)


def test_conflict_dotted_vs_scalar(tmp_path: Path) -> None:
    path = write_module(
        tmp_path, "dotted.dl", 'json => { a: 1; a.b: 2; }'
    )
    with pytest.raises(ConflictError) as error:
        evaluate_file(path)
    assert "E003" in str(error.value)


# ───────────────────────────── 6. W001 дубликат ─────────────────────────────


def test_duplicate_same_value_warning(tmp_path: Path, caplog) -> None:
    path = write_module(tmp_path, "duplicate.dl", 'json => { a: 1; a: 1; }')
    with caplog.at_level(logging.WARNING, logger="dl"):
        result = evaluate_file(path)
    assert result == {"a": 1}
    assert "W001" in caplog.text
    assert "DuplicateKey" in caplog.text


# ─────────────────────────── 7. E004 цикл импортов ──────────────────────────


def test_circular_import(tmp_path: Path) -> None:
    write_module(tmp_path, "a.dl", "json => { x: import ./b.dl; }")
    write_module(tmp_path, "b.dl", "json => { y: import ./a.dl; }")
    with pytest.raises(CircularImportError) as error:
        evaluate_file(tmp_path / "a.dl")
    assert "E004" in str(error.value)


def test_missing_module(tmp_path: Path) -> None:
    path = write_module(tmp_path, "missing.dl", "json => { x: import ./nope.dl; }")
    with pytest.raises(Exception) as error:  # dl.errors.ModuleNotFoundError
        evaluate_file(path)
    assert "E002" in str(error.value)


# ─────────────────────── 8. E010 / E009 параметры вызова ────────────────────


def test_missing_required_parameter(tmp_path: Path) -> None:
    write_module(tmp_path, "mod.dl", '( $, name ) => { name: name; }')
    path = write_module(
        tmp_path, "main.dl", "json => { let m = import ./mod.dl; x: m(); }"
    )
    with pytest.raises(MissingParameterError) as error:
        evaluate_file(path)
    assert "E010" in str(error.value)


def test_unknown_named_parameter(tmp_path: Path) -> None:
    write_module(tmp_path, "mod.dl", '( $, name ) => { name: name; }')
    path = write_module(
        tmp_path,
        "main.dl",
        'json => { let m = import ./mod.dl; x: m("a", { bogus: 1; }); }',
    )
    with pytest.raises(UnknownParameterError) as error:
        evaluate_file(path)
    assert "E009" in str(error.value)
    assert "bogus" in str(error.value)


# ──────────────────────── 9. let и вложенные вызовы ─────────────────────────


def test_let_and_nested_calls(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "inner.dl",
        '( $, word ) => { doubled: "{word}{word}"; }',
    )
    write_module(
        tmp_path,
        "middle.dl",
        "( $, word ) => { let inner = import ./inner.dl; inner(word); }",
    )
    path = write_module(
        tmp_path,
        "main.dl",
        'json => { let mid = import ./middle.dl; result: mid("ab"); }',
    )
    assert evaluate_file(path) == {"result": {"doubled": "abab"}}


# ────────────────────────── 10. точечная нотация ────────────────────────────


def test_mcp_servers_dotted_notation(configuration: dict) -> None:
    assert "mcp.servers" not in configuration
    assert isinstance(configuration["mcp"], dict)
    assert set(configuration["mcp"]["servers"]) == {
        "deepwiki",
        "sequential-thinking",
        "context7",
        "lightpanda",
        "deploychan",
    }


# ─────────────────────────── дополнительные проверки ────────────────────────


def test_settings_context(settings_context: dict) -> None:
    assert settings_context["builds"][0]["source"] == "./configuration.dl"
    assert settings_context["npm"]["openaicomp"] == "@ai-sdk/openai-compatible"
    assert (
        settings_context["npm"]["voidrot"]
        == "@voidrot/openai-featherless-compatible"
    )


def test_context_required_for_dollar(tmp_path: Path) -> None:
    path = write_module(tmp_path, "noctx.dl", "json => { a: $.x; }")
    with pytest.raises(DLContextError) as error:
        evaluate_file(path)
    assert "E008" in str(error.value)


def test_default_used_when_omitted(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "defaults.dl",
        '( $, value, suffix: "!" ) => { text: "{value}{suffix}"; }',
    )
    path = write_module(
        tmp_path,
        "main.dl",
        'json => { let f = import ./defaults.dl; a: f("hi"); b: f("hi", { suffix: "?"; }); }',
    )
    assert evaluate_file(path) == {"a": {"text": "hi!"}, "b": {"text": "hi?"}}


def test_context_propagates_through_calls(tmp_path: Path) -> None:
    write_module(
        tmp_path, "leaf.dl", "( $ ) => { from_ctx: $.name; }"
    )
    write_module(
        tmp_path,
        "middle.dl",
        "( $ ) => { let leaf = import ./leaf.dl; leaf(); }",
    )
    path = write_module(
        tmp_path,
        "main.dl",
        'json( $ ) => { let mid = import ./middle.dl; nested: mid(); }',
    )
    assert evaluate_file(path, {"name": "jarvis"}) == {
        "nested": {"from_ctx": "jarvis"}
    }


def test_spread_overrides_without_conflict(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "base.dl",
        '() => { a: 1; b: 2; }',
    )
    path = write_module(
        tmp_path,
        "main.dl",
        "json => { let base = import ./base.dl; obj: { a: 9; b: 8; ...base; }; }",
    )
    assert evaluate_file(path) == {"obj": {"a": 1, "b": 2}}
