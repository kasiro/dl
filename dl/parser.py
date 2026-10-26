"""Разбор DL v2.1 в AST.

Публичный API:
    parse(source: str, filename: str = "<input>") -> dict

Контракт AST описан в задании (этап 1). Одно расширение контракта:
анонимный объектный тип в схеме (`{ field: type; ... }`) представлен как
``{"kind": "object", "fields": [Field, ...]}`` — в перечне типов задания он
не указан, но examples/config.schema без него не выразить.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from lark import Lark, Token, Transformer

GRAMMAR_PATH = Path(__file__).with_name("grammar.lark")

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    '"': '"',
    "'": "'",
    "\\": "\\",
    "0": "\0",
}

# Интерполяция внутри строки: {name}, {a.b}, {$.npm.x}
_INTERP_RE = re.compile(r"\{([A-Za-z_$][A-Za-z0-9_$.\-]*)\}")


def _unescape(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            out.append(_ESCAPES.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _unquote(token: Token) -> str:
    """Снять кавычки и раскрыть escape-последовательности у STRING."""
    raw = str(token)
    if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
        raw = raw[1:-1]
    return _unescape(raw)


def _split_interpolation(text: str) -> list[tuple[str, str] | tuple[str, list[str]]]:
    """Разбить строку на литералы и интерполяции.

    Результат: [("lit", str) | ("expr", [str]), ...]. Если интерполяций нет,
    возвращается один литерал (возможно пустой).
    """
    parts: list[tuple[str, str] | tuple[str, list[str]]] = []
    pos = 0
    for match in _INTERP_RE.finditer(text):
        if match.start() > pos:
            parts.append(("lit", text[pos : match.start()]))
        parts.append(("expr", match.group(1).split(".")))
        pos = match.end()
    if pos < len(text):
        parts.append(("lit", text[pos:]))
    if not parts:
        parts.append(("lit", ""))
    return parts


def _doc_text(token: Token) -> str:
    text = str(token)
    if text.startswith("///"):
        text = text[3:]
    return text.strip()


def _field(
    name: str,
    typ: dict,
    optional: bool,
    default: dict | None,
    doc: str | None,
) -> dict:
    return {
        "name": name,
        "type": typ,
        "optional": optional,
        "default": default,
        "doc": doc,
    }


def _document(
    kind: str,
    fmt: str | None,
    schema: str | None,
    params: list[dict] | None,
    body: list[dict],
) -> dict:
    return {
        "kind": kind,
        "format": fmt,
        "schema": schema,
        "params": params,
        "body": body,
    }


# ---------------------------------------------------------------------------
# Трансформер
# ---------------------------------------------------------------------------


class DLTransformer(Transformer):
    """Преобразование дерева разбора Lark в AST DL."""

    # ── документ ──────────────────────────────────────────────────────────

    def start(self, items):
        return items[0]

    def config_with_schema(self, items):
        fmt, params, schema, body = items
        return _document("config", fmt.value, schema, params, body)

    def config_plain(self, items):
        fmt, params, body = items
        return _document("config", fmt.value, None, params, body)

    def config_bare_with_schema(self, items):
        fmt, schema, body = items
        return _document("config", fmt.value, schema, None, body)

    def config_bare(self, items):
        fmt, body = items
        return _document("config", fmt.value, None, None, body)

    def module_doc(self, items):
        params, body = items
        return _document("module", None, None, params, body)

    def schema_doc(self, items):
        return _document("schema", None, None, None, items[0])

    def schema_name(self, items):
        return items[0].value

    # ── параметры ─────────────────────────────────────────────────────────

    def param_block(self, items):
        return items[0] if items else []

    def param_list(self, items):
        return list(items)

    def param_context(self, items):
        return {"name": "$", "optional": False, "default": None}

    def param_plain(self, items):
        return {"name": items[0].value, "optional": False, "default": None}

    def param_optional(self, items):
        return {"name": items[0].value, "optional": True, "default": None}

    def param_default(self, items):
        return {"name": items[0].value, "optional": False, "default": items[1]}

    # ── блоки и инструкции ────────────────────────────────────────────────

    def block(self, items):
        return items[0] if items else []

    def stmts_more(self, items):
        return [items[0], *items[1]]

    def stmts_trailing(self, items):
        return [items[0]]

    def stmts_single(self, items):
        return [items[0]]

    def stmt(self, items):
        return items[0]

    def let_stmt(self, items):
        return {"kind": "let", "name": items[0].value, "value": items[1]}

    def spread_stmt(self, items):
        return {"kind": "spread", "value": items[0]}

    def field(self, items):
        return {
            "kind": "field",
            "path": items[0],
            "value": items[1],
            "optional": False,
        }

    def field_optional(self, items):
        return {
            "kind": "field",
            "path": items[0],
            "value": items[1],
            "optional": True,
        }

    def call_stmt(self, items):
        return {"kind": "expr", "value": items[0]}

    def field_path(self, items):
        return [self._segment(items[0]), *items[1:]]

    def path_seg(self, items):
        return self._segment(items[0])

    @staticmethod
    def _segment(token: Token) -> str:
        if token.type == "STRING":
            return _unquote(token)
        return token.value

    # ── выражения ─────────────────────────────────────────────────────────

    def expr(self, items):
        # Обёртка для альтернатив expr без собственного алиаса.
        return items[0]

    def string_lit(self, items):
        return {
            "kind": "string",
            "parts": _split_interpolation(_unquote(items[0])),
        }

    def int_lit(self, items):
        return {"kind": "int", "value": int(items[0].value)}

    def float_lit(self, items):
        return {"kind": "float", "value": float(items[0].value)}

    def true_lit(self, items):
        return {"kind": "bool", "value": True}

    def false_lit(self, items):
        return {"kind": "bool", "value": False}

    def null_lit(self, items):
        return {"kind": "null"}

    def array_empty(self, items):
        return {"kind": "array", "items": []}

    def array(self, items):
        return {"kind": "array", "items": items[0]}

    def expr_list_more(self, items):
        return [items[0], *items[1]]

    def expr_list_space(self, items):
        return [items[0], *items[1]]

    def expr_list_trailing(self, items):
        return [items[0]]

    def expr_list_single(self, items):
        return [items[0]]

    def object(self, items):
        return {"kind": "object", "body": items[0]}

    def call_empty(self, items):
        return {
            "kind": "call",
            "name": items[0].value,
            "positional": [],
            "named": None,
        }

    def call(self, items):
        name = items[0].value
        args = items[1]
        # Объект последним аргументом — это именованные аргументы (5.5).
        if args and args[-1].get("kind") == "object":
            return {
                "kind": "call",
                "name": name,
                "positional": args[:-1],
                "named": args[-1]["body"],
            }
        return {"kind": "call", "name": name, "positional": args, "named": None}

    def args_more(self, items):
        return [items[0], *items[1]]

    def args_trailing(self, items):
        return [items[0]]

    def args_single(self, items):
        return [items[0]]

    def import_expr(self, items):
        path = items[0].value
        parts = None
        is_glob = "*" in path
        if _INTERP_RE.search(path):
            parts = _split_interpolation(path)
        return {"kind": "import", "path": path, "parts": parts, "glob": is_glob}

    def ref(self, items):
        return {"kind": "ref", "path": items[0]}

    def ref_path(self, items):
        return [self._segment(items[0]), *items[1:]]

    # ── схема ─────────────────────────────────────────────────────────────

    def schema_block(self, items):
        return list(items)

    def class_plain(self, items):
        return {
            "kind": "class",
            "name": items[0].value,
            "doc": None,
            "fields": list(items[1:]),
        }

    def class_doc(self, items):
        return {
            "kind": "class",
            "name": items[1].value,
            "doc": items[0],
            "fields": list(items[2:]),
        }

    def doc(self, items):
        return "\n".join(_doc_text(token) for token in items)

    def field_name(self, items):
        return self._segment(items[0])

    def class_field_plain(self, items):
        return _field(items[0], items[1], False, _opt(items, 2), None)

    def class_field_optional(self, items):
        return _field(items[0], items[1], True, _opt(items, 2), None)

    def class_field_doc_plain(self, items):
        return _field(items[1], items[2], False, _opt(items, 3), items[0])

    def class_field_doc_optional(self, items):
        return _field(items[1], items[2], True, _opt(items, 3), items[0])

    def obj_field_plain(self, items):
        return _field(items[0], items[1], False, _opt(items, 2), None)

    def obj_field_optional(self, items):
        return _field(items[0], items[1], True, _opt(items, 2), None)

    def obj_field_doc_plain(self, items):
        return _field(items[1], items[2], False, _opt(items, 3), items[0])

    def obj_field_doc_optional(self, items):
        return _field(items[1], items[2], True, _opt(items, 3), items[0])

    # ── типы ──────────────────────────────────────────────────────────────

    def type(self, items):
        if len(items) == 1:
            return items[0]
        return {"kind": "union", "variants": list(items)}

    def type_atom(self, items):
        return items[0]

    def t_string(self, items):
        return {"kind": "primitive", "name": "string"}

    def t_integer(self, items):
        return {"kind": "primitive", "name": "integer"}

    def t_number(self, items):
        return {"kind": "primitive", "name": "number"}

    def t_float(self, items):
        return {"kind": "primitive", "name": "float"}

    def t_boolean(self, items):
        return {"kind": "primitive", "name": "boolean"}

    def t_null(self, items):
        return {"kind": "primitive", "name": "null"}

    def t_any(self, items):
        return {"kind": "primitive", "name": "any"}

    def array_type(self, items):
        return {"kind": "array", "of": items[0]}

    def map_type(self, items):
        return {"kind": "map", "of": items[0]}

    def enum_type(self, items):
        return {"kind": "enum", "values": list(items)}

    def enum_string(self, items):
        return _unquote(items[0])

    def enum_number(self, items):
        return str(int(items[0].value))

    def enum_true(self, items):
        return "true"

    def enum_false(self, items):
        return "false"

    def enum_null(self, items):
        return "null"

    def object_type(self, items):
        return {"kind": "object", "fields": list(items)}

    def named_type(self, items):
        return {"kind": "named", "name": items[0].value}


def _opt(items: list, index: int):
    return items[index] if len(items) > index else None


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------


def load_grammar() -> str:
    return GRAMMAR_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _get_parser() -> Lark:
    return Lark(load_grammar(), parser="lalr", start="start")


def parse(source: str, filename: str = "<input>") -> dict:
    """Разобрать исходник DL в AST.

    filename используется только для сообщений об ошибках (в текущей версии
    пробрасываются исключения Lark как есть).
    """
    tree = _get_parser().parse(source)
    return DLTransformer().transform(tree)


if __name__ == "__main__":
    print(parse('json => { name: "test"; }'))
