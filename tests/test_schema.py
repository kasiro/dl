"""Тесты генерации схем, валидации и связывания со сборкой (этап 3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dl.errors import SchemaFetchError, TypeMismatchError
from dl.evaluator import evaluate
from dl.parser import parse
from dl.schema_gen import (
    download_schema,
    ensure_schema,
    generate_schema,
    load_schema,
    schema_filename,
)
from dl.validator import validate, validate_or_raise

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


# ─────────────────────────── мини-JSON Schema ───────────────────────────────

MINI_SCHEMA = {
    "$id": "https://example.com/mini.json",
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Display name"},
        "mode": {"enum": ["fast", "slow"]},
        "count": {"type": "integer"},
        "ratio": {"type": "number"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "limits": {
            "type": "object",
            "additionalProperties": {"type": "integer"},
        },
        "child": {"$ref": "#/$defs/Child"},
    },
    "required": ["name", "mode"],
    "$defs": {
        "Child": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "label": {"type": "string"},
            },
            "required": ["id"],
        },
        "Unused": {
            "type": "object",
            "properties": {"value": {"type": "boolean"}},
        },
    },
}


def parse_schema_text(text: str) -> dict:
    """Разобрать сгенерированный текст и вычислить схему."""
    ast = parse(text, "<generated>")
    return evaluate(ast, Path.cwd())


# ───────────────────────────── 1. генерация ─────────────────────────────────


def test_generate_schema_two_classes_enum_optional_map():
    text = generate_schema(MINI_SCHEMA, "https://example.com/mini.json")

    assert "schema => {" in text
    assert "class Config {" in text
    assert "class Child {" in text
    assert "/// Display name" in text
    # enum
    assert 'mode: enum { "fast" | "slow" };' in text
    # optional (нет в required) и map из additionalProperties
    assert "count?: integer;" in text
    assert "limits?: map<integer>;" in text
    assert "tags?: [string];" in text
    assert "child?: Child;" in text
    # $defs.Unused тоже становится классом
    assert "class Unused {" in text

    value = parse_schema_text(text)
    assert value["kind"] == "schema"
    names = [cls["name"] for cls in value["classes"]]
    assert names == ["Config", "Child", "Unused"]

    config = value["classes"][0]
    fields = {field["name"]: field for field in config["fields"]}
    assert fields["name"]["optional"] is False
    assert fields["mode"]["type"]["kind"] == "enum"
    assert fields["count"]["optional"] is True
    assert fields["limits"]["type"] == {
        "kind": "map",
        "of": {"kind": "primitive", "name": "integer"},
    }


def test_generate_schema_rejects_non_object():
    from dl.errors import SchemaGenerateError

    with pytest.raises(SchemaGenerateError):
        generate_schema([], "https://example.com/x.json")  # type: ignore[arg-type]


def test_schema_filename():
    assert schema_filename("https://opencode.ai/config.json") == "config.schema"
    assert schema_filename("file:///tmp/a/config.json") == "config.schema"
    assert schema_filename("https://example.com/schema.json") == "schema.schema"


# ──────────────────────── 2. download / ensure_schema ───────────────────────


def test_download_schema_file_url(tmp_path: Path):
    source = tmp_path / "config.json"
    source.write_text(json.dumps(MINI_SCHEMA), encoding="utf-8")

    data = download_schema(source.as_uri())
    assert data["type"] == "object"
    assert data["$defs"]["Child"]["properties"]["id"]["type"] == "integer"


def test_download_schema_invalid_url():
    with pytest.raises(SchemaFetchError) as info:
        download_schema("file:///definitely/not/here/config.json")
    assert info.value.code == "E012"


def test_ensure_schema_caches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    calls = {"count": 0}

    def fake_download(url: str, timeout: float = 30) -> dict:
        calls["count"] += 1
        return MINI_SCHEMA

    monkeypatch.setattr("dl.schema_gen.download_schema", fake_download)

    path = ensure_schema("https://example.com/config.json", tmp_path)
    assert path == tmp_path / "config.schema"
    assert path.is_file()
    assert calls["count"] == 1

    # повторный вызов использует кэш и не качает схему
    again = ensure_schema("https://example.com/config.json", tmp_path)
    assert again == path
    assert calls["count"] == 1

    # force перекачивает
    ensure_schema("https://example.com/config.json", tmp_path, force=True)
    assert calls["count"] == 2


def test_ensure_schema_writes_parseable_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        "dl.schema_gen.download_schema", lambda url, timeout=30: MINI_SCHEMA
    )
    path = ensure_schema("https://example.com/config.json", tmp_path)
    classes = load_schema(path)
    assert [cls["name"] for cls in classes] == ["Config", "Child", "Unused"]


# ────────────────────────────── 3. валидация ────────────────────────────────

SCHEMA_TEXT = """
schema => {
    class Config {
        name: string;
        count: integer;
        ratio?: number;
        flag?: boolean;
        mode?: enum { "fast" | "slow" };
        tags?: [string];
        limits?: map<integer>;
        payload?: string | { id: integer; };
        child?: Child;
    };
    class Child {
        id: integer;
        label?: string;
    };
}
"""


@pytest.fixture(scope="module")
def classes() -> list[dict]:
    value = parse_schema_text(SCHEMA_TEXT)
    assert value["kind"] == "schema"
    return value["classes"]


def test_valid_object_has_no_errors(classes: list[dict]):
    value = {
        "name": "x",
        "count": 2,
        "ratio": 1,
        "flag": True,
        "mode": "fast",
        "tags": ["a", "b"],
        "limits": {"a": 1, "b": 2},
        "payload": {"id": 3},
        "child": {"id": 1, "label": "c"},
        "extra": "allowed",
    }
    assert validate(value, "Config", classes) == []


def test_missing_required_field(classes: list[dict]):
    errors = validate({"count": 1}, "Config", classes)
    assert errors == [
        "E011 TypeMismatch: name: expected string, got missing"
    ]


def test_wrong_primitive_type(classes: list[dict]):
    errors = validate({"name": "x", "count": True}, "Config", classes)
    assert errors == [
        "E011 TypeMismatch: count: expected integer, got boolean"
    ]


def test_integer_rejects_float(classes: list[dict]):
    errors = validate({"name": "x", "count": 1.5}, "Config", classes)
    assert "E011 TypeMismatch: count: expected integer, got float" in errors


def test_number_accepts_integer_and_float(classes: list[dict]):
    assert validate({"name": "x", "count": 1, "ratio": 2}, "Config", classes) == []
    assert (
        validate({"name": "x", "count": 1, "ratio": 2.5}, "Config", classes) == []
    )


def test_boolean_rejects_string(classes: list[dict]):
    errors = validate({"name": "x", "count": 1, "flag": "yes"}, "Config", classes)
    assert errors == [
        "E011 TypeMismatch: flag: expected boolean, got string"
    ]


def test_enum_error(classes: list[dict]):
    errors = validate({"name": "x", "count": 1, "mode": "turbo"}, "Config", classes)
    assert errors == [
        "E011 TypeMismatch: mode: expected enum { fast | slow }, got string"
    ]


def test_union_accepts_variant(classes: list[dict]):
    assert validate({"name": "x", "count": 1, "payload": "s"}, "Config", classes) == []
    assert validate({"name": "x", "count": 1, "payload": {"id": 1}}, "Config", classes) == []


def test_union_error(classes: list[dict]):
    errors = validate({"name": "x", "count": 1, "payload": 5}, "Config", classes)
    assert errors
    assert all(error.startswith("E011 TypeMismatch: payload") for error in errors)


def test_map_values(classes: list[dict]):
    assert validate({"name": "x", "count": 1, "limits": {"a": 1}}, "Config", classes) == []
    errors = validate({"name": "x", "count": 1, "limits": {"a": "x"}}, "Config", classes)
    assert errors == [
        "E011 TypeMismatch: limits.a: expected integer, got string"
    ]


def test_array_items(classes: list[dict]):
    errors = validate({"name": "x", "count": 1, "tags": ["a", 2]}, "Config", classes)
    assert errors == [
        "E011 TypeMismatch: tags[1]: expected string, got integer"
    ]


def test_named_class_and_nested_path(classes: list[dict]):
    errors = validate(
        {"name": "x", "count": 1, "child": {"id": "no"}}, "Config", classes
    )
    assert errors == [
        "E011 TypeMismatch: child.id: expected integer, got string"
    ]


def test_validate_or_raise_collects_all(classes: list[dict]):
    with pytest.raises(TypeMismatchError) as info:
        validate_or_raise({"count": "x", "flag": 1}, "Config", classes)
    message = str(info.value)
    assert info.value.code == "E011"
    assert "name: expected string, got missing" in message
    assert "count: expected integer, got string" in message
    assert "flag: expected boolean, got integer" in message


# ───────────────────── 4. examples/config.schema ────────────────────────────


def test_examples_schema_parses_and_has_config():
    path = EXAMPLES / "config.schema"
    classes = load_schema(path)
    names = {cls["name"] for cls in classes}
    assert "Config" in names
    assert "PermissionRule" in names
    config = next(cls for cls in classes if cls["name"] == "Config")
    fields = {field["name"] for field in config["fields"]}
    assert {"model", "mcp", "provider", "agents"} <= fields
