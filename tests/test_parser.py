"""Тесты парсера DL v2.1 (этап 1)."""

from pathlib import Path

import pytest

from dl.parser import parse

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


# ─────────────────────────────── заголовки ──────────────────────────────────


def test_config_header():
    doc = parse('json( $ ) => Config { name: "x"; }')
    assert doc["kind"] == "config"
    assert doc["format"] == "json"
    assert doc["schema"] == "Config"
    assert doc["params"] == [{"name": "$", "optional": False, "default": None}]
    assert len(doc["body"]) == 1


def test_config_header_without_context_and_schema():
    doc = parse('yaml => { a: 1; }')
    assert doc["kind"] == "config"
    assert doc["format"] == "yaml"
    assert doc["schema"] is None
    assert doc["params"] is None


def test_toml_header():
    assert parse('toml( $ ) => { a: 1; }')["format"] == "toml"


def test_module_header():
    doc = parse('( $, name ) => { name: name; }')
    assert doc["kind"] == "module"
    assert doc["format"] is None
    assert doc["schema"] is None
    assert [p["name"] for p in doc["params"]] == ["$", "name"]


def test_module_without_params():
    doc = parse('() => { a: 1; }')
    assert doc["kind"] == "module"
    assert doc["params"] == []


def test_schema_header():
    doc = parse('schema => { class Config { a?: string; }; }')
    assert doc["kind"] == "schema"
    assert doc["format"] is None
    assert doc["params"] is None
    assert doc["body"][0]["kind"] == "class"


# ──────────────────────────────── параметры ─────────────────────────────────


def test_params_required_optional_default():
    doc = parse('( $, name, url?, options: {} ) => { a: 1; }')
    params = doc["params"]
    assert params[0] == {"name": "$", "optional": False, "default": None}
    assert params[1] == {"name": "name", "optional": False, "default": None}
    assert params[2] == {"name": "url", "optional": True, "default": None}
    assert params[3]["name"] == "options"
    assert params[3]["optional"] is False
    assert params[3]["default"] == {"kind": "object", "body": []}


def test_param_default_scalar():
    doc = parse('( $, host: "localhost", port: 80, flag: true ) => { a: 1; }')
    defaults = [p["default"] for p in doc["params"][1:]]
    assert defaults[0]["parts"] == [("lit", "localhost")]
    assert defaults[1] == {"kind": "int", "value": 80}
    assert defaults[2] == {"kind": "bool", "value": True}


# ─────────────────────────────── инструкции ─────────────────────────────────


def test_let_statement():
    doc = parse('json => { let x = import ./a.dl; a: x; }')
    let = doc["body"][0]
    assert let == {
        "kind": "let",
        "name": "x",
        "value": {"kind": "import", "path": "./a.dl", "parts": None, "glob": False},
    }
    assert doc["body"][1]["value"] == {"kind": "ref", "path": ["x"]}


def test_field_and_dotted_path():
    doc = parse('json => { a.b.c = 1; }')
    assert doc["body"][0] == {
        "kind": "field",
        "path": ["a", "b", "c"],
        "value": {"kind": "int", "value": 1},
        "optional": False,
    }


def test_field_equals_and_colon_equivalent():
    a = parse('json => { x = 1; }')["body"][0]
    b = parse('json => { x: 1; }')["body"][0]
    assert a == b


def test_optional_field():
    doc = parse('( $, url? ) => { url?: url; }')
    stmt = doc["body"][0]
    assert stmt["kind"] == "field"
    assert stmt["optional"] is True
    assert stmt["path"] == ["url"]
    assert stmt["value"] == {"kind": "ref", "path": ["url"]}


def test_spread_statement():
    doc = parse('json => { ...makeoptions(port); }')
    stmt = doc["body"][0]
    assert stmt["kind"] == "spread"
    assert stmt["value"]["kind"] == "call"
    assert stmt["value"]["name"] == "makeoptions"


def test_expr_statement():
    doc = parse('() => { createmodel("x"); }')
    stmt = doc["body"][0]
    assert stmt["kind"] == "expr"
    assert stmt["value"]["kind"] == "call"
    assert stmt["value"]["name"] == "createmodel"


def test_quoted_keys():
    doc = parse('json => { "glob": "deny"; "agent": { a: 1; }; }')
    assert doc["body"][0]["path"] == ["glob"]
    assert doc["body"][1]["path"] == ["agent"]
    assert doc["body"][1]["value"]["kind"] == "object"


def test_context_field_path():
    doc = parse('( $ ) => { $.npm.x: "@scope/pkg"; }')
    assert doc["body"][0]["path"] == ["$", "npm", "x"]


# ───────────────────────────────── вызовы ───────────────────────────────────


def test_call_positional_and_named():
    doc = parse(
        'json => { p: createprovider("localproxy", { npm: $.npm.x; port: 9625; }); }'
    )
    call = doc["body"][0]["value"]
    assert call["kind"] == "call"
    assert call["name"] == "createprovider"
    assert len(call["positional"]) == 1
    assert call["positional"][0]["parts"] == [("lit", "localproxy")]
    assert [f["path"] for f in call["named"]] == [["npm"], ["port"]]


def test_call_only_named():
    doc = parse('json => { a: f({ x: 1; y: 2; }); }')
    call = doc["body"][0]["value"]
    assert call["positional"] == []
    assert [f["path"] for f in call["named"]] == [["x"], ["y"]]


def test_call_without_args():
    call = parse('json => { a: f(); }')["body"][0]["value"]
    assert call == {"kind": "call", "name": "f", "positional": [], "named": None}


# ───────────────────────────────── импорт ───────────────────────────────────


def test_import_plain():
    doc = parse('json => { let a = import ../base.dl; }')
    assert doc["body"][0]["value"] == {
        "kind": "import",
        "path": "../base.dl",
        "parts": None,
        "glob": False,
    }


def test_import_interpolated():
    doc = parse('json => { models: import ./models/{name}.dl; }')
    imp = doc["body"][0]["value"]
    assert imp["kind"] == "import"
    assert imp["parts"] == [
        ("lit", "./models/"),
        ("expr", ["name"]),
        ("lit", ".dl"),
    ]


# ───────────────────────────────── строки ───────────────────────────────────


def test_string_plain():
    assert parse('json => { a: "x"; }')["body"][0]["value"] == {
        "kind": "string",
        "parts": [("lit", "x")],
    }


def test_string_interpolation():
    doc = parse('json => { a: "http://{host}:{port}/v1"; }')
    assert doc["body"][0]["value"]["parts"] == [
        ("lit", "http://"),
        ("expr", ["host"]),
        ("lit", ":"),
        ("expr", ["port"]),
        ("lit", "/v1"),
    ]


def test_string_single_quotes_and_escapes():
    doc = parse("json => { a: 'it\\'s'; }")
    assert doc["body"][0]["value"]["parts"] == [("lit", "it's")]


# ───────────────────────────────── массивы ─────────────────────────────────


def test_array_space_separated():
    items = parse('json => { a: [ "x" "y" 3 ]; }')["body"][0]["value"]["items"]
    assert [i["kind"] for i in items] == ["string", "string", "int"]


def test_array_commas_optional():
    items = parse('json => { a: [1, 2 3,]; }')["body"][0]["value"]["items"]
    assert [i["value"] for i in items] == [1, 2, 3]


def test_array_empty():
    assert parse('json => { a: []; }')["body"][0]["value"] == {
        "kind": "array",
        "items": [],
    }


def test_array_of_objects():
    doc = parse('json => { a: [ { x: 1; }, { y: 2; } ]; }')
    items = doc["body"][0]["value"]["items"]
    assert [i["kind"] for i in items] == ["object", "object"]


# ────────────────────────────── схемы и типы ────────────────────────────────


def test_class_with_doc_and_fields():
    src = """
    schema => {
        class Config {
            /// Default model
            model?: string;
            port: integer = 8080;
        };
    }
    """
    doc = parse(src)
    cls = doc["body"][0]
    assert cls["name"] == "Config"
    assert cls["doc"] is None
    assert [f["name"] for f in cls["fields"]] == ["model", "port"]
    assert cls["fields"][0]["doc"] == "Default model"
    assert cls["fields"][0]["optional"] is True
    assert cls["fields"][1]["optional"] is False
    assert cls["fields"][1]["default"] == {"kind": "int", "value": 8080}


def test_types():
    src = """
    schema => {
        class C {
            a: string;
            b: [integer];
            c: map<boolean>;
            d: enum { "x" | "y" };
            e: A | B;
            f: [string | [any]];
            g: { inner?: number; };
        };
    }
    """
    fields = {f["name"]: f["type"] for f in parse(src)["body"][0]["fields"]}
    assert fields["a"] == {"kind": "primitive", "name": "string"}
    assert fields["b"] == {"kind": "array", "of": {"kind": "primitive", "name": "integer"}}
    assert fields["c"] == {"kind": "map", "of": {"kind": "primitive", "name": "boolean"}}
    assert fields["d"] == {"kind": "enum", "values": ["x", "y"]}
    assert fields["e"] == {
        "kind": "union",
        "variants": [
            {"kind": "named", "name": "A"},
            {"kind": "named", "name": "B"},
        ],
    }
    assert fields["f"]["kind"] == "array"
    assert fields["f"]["of"]["kind"] == "union"
    assert fields["g"]["kind"] == "object"
    assert fields["g"]["fields"][0]["name"] == "inner"


def test_enum_boolean_values():
    src = 'schema => { class C { a?: enum { true }; b?: enum { false }; }; }'
    fields = parse(src)["body"][0]["fields"]
    assert fields[0]["type"] == {"kind": "enum", "values": ["true"]}
    assert fields[1]["type"] == {"kind": "enum", "values": ["false"]}


# ─────────────────────── необязательная `;` перед `}` ───────────────────────


def test_no_semicolon_before_closing_brace():
    doc = parse('( $, name ) => { a: 1; b: 2 }')
    assert len(doc["body"]) == 2


def test_trailing_semicolon_allowed():
    assert len(parse('json => { a: 1; b: 2; }')["body"]) == 2


def test_nested_object_without_final_semicolon():
    doc = parse('json => { a: { b: 1 } }')
    inner = doc["body"][0]["value"]["body"]
    assert inner[0]["path"] == ["b"]


# ───────────────────────────── все примеры ──────────────────────────────────


@pytest.mark.parametrize(
    "path",
    sorted([*EXAMPLES.rglob("*.dl"), *EXAMPLES.rglob("*.schema")]),
    ids=lambda p: str(p.relative_to(EXAMPLES)),
)
def test_examples_parse(path: Path):
    doc = parse(path.read_text(encoding="utf-8"), str(path))
    assert doc["kind"] in {"config", "module", "schema"}
    assert isinstance(doc["body"], list)
    assert doc["body"], f"{path} разобран в пустой блок"
