"""Генерация DL-схем из JSON Schema, скачивание и кэширование (этап 3).

Публичный API:

    generate_schema(json_schema, source_url, notes=None) -> str
    download_schema(url, timeout=30) -> dict
    ensure_schema(url, dest_dir, force=False) -> Path
    load_schema(path) -> list[dict]
    schema_filename(url) -> str

Правила конвертации — раздел 4.5 спецификации:

    object + properties      -> class <Name> { ... }
    required                 -> поле без "?"
    optional                 -> поле с "?"
    string/integer/number/   -> примитивы
    boolean/null
    array + items            -> [T]
    additionalProperties     -> map<T> (true -> map<any>)
    enum                     -> enum { "a" | "b" }
    oneOf/anyOf              -> A | B
    $ref #/$defs/X           -> class_name(X) (если X — object-класс, иначе тип
                                раскрывается); точки в именах недопустимы,
                                ведущий Config. отбрасывается
    default                  -> = <literal>
    description              -> /// <text> над полем

Невыразимые в DL ограничения (pattern, minimum, additionalProperties у
объекта с properties, deprecated и т.п.) собираются в ``notes`` и печатаются
в stderr командой ``dl schema``.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .errors import SchemaFetchError, SchemaGenerateError

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")

PRIMITIVES = {
    "string": "string",
    "integer": "integer",
    "number": "number",
    "float": "float",
    "boolean": "boolean",
    "null": "null",
}

DEFAULT_SCHEMA_NAME = "config.schema"

# Некоторые CDN отдают 403 на стандартный User-Agent urllib.
DEFAULT_USER_AGENT = "dl/0.1"


# ---------------------------------------------------------------------------
# Литералы и имена
# ---------------------------------------------------------------------------


def qkey(key: str) -> str:
    """Ключ DL: простой идентификатор — как есть, иначе в кавычках."""
    return key if IDENT.match(key) else json.dumps(key, ensure_ascii=False)


def class_name(name: str) -> str:
    """DL-имя класса: точки убираются, ведущий сегмент ``Config`` отбрасывается.

    DL не допускает точек в именах классов, поэтому имена из ``$defs``
    нормализуются в CamelCase::

        Permission.Rule          -> PermissionRule
        Config.AgentEncoded      -> AgentEncoded
        Mcp.LocalConfigEncoded   -> McpLocalConfigEncoded
        ConfigV2.Reference.Git   -> ConfigV2ReferenceGit

    Функция идемпотентна: имя без точек возвращается как есть.
    """
    parts = name.split(".")
    if len(parts) > 1 and parts[0] == "Config":
        parts = parts[1:]
    return "".join(parts)


def lit(value: Any) -> str:
    """Литерал DL для default/enum."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(lit(v) for v in value) + "]"
    if isinstance(value, dict):
        return (
            "{ "
            + " ".join(f"{qkey(k)}: {lit(v)};" for k, v in value.items())
            + " }"
        )
    return json.dumps(value, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Конвертер
# ---------------------------------------------------------------------------


class SchemaConverter:
    """JSON Schema → DL-схема."""

    def __init__(self, schema: dict):
        self.root = schema
        self.defs = schema.get("$defs") or schema.get("definitions") or {}
        self.notes: list[str] = []
        self.notes_seen: set[str] = set()
        self.stack: list[str] = []

    # ------------------------------------------------------------------ utils
    @staticmethod
    def pad(indent: int) -> str:
        return "    " * indent

    def note(self, msg: str) -> None:
        if msg not in self.notes_seen:
            self.notes_seen.add(msg)
            self.notes.append(msg)

    @staticmethod
    def def_name(ref: str) -> str:
        return ref.rsplit("/", 1)[-1]

    def resolve(self, ref: str) -> dict | None:
        if ref.startswith("#/$defs/") or ref.startswith("#/definitions/"):
            return self.defs.get(self.def_name(ref))
        self.note(f"внешний $ref не раскрыт: {ref} -> any")
        return None

    def is_object_def(self, schema: Any) -> bool:
        """Класс генерируется только для object-схем с properties."""
        return isinstance(schema, dict) and bool(schema.get("properties"))

    # ------------------------------------------------------------- rendering
    def render_type(self, schema: Any, indent: int) -> list[str]:
        """Вернуть тип списком строк.

        Первая строка — тип без ведущего отступа, последняя — закрывающая
        скобка с отступом ``indent`` (если тип многострочный).
        """
        if not isinstance(schema, dict) or not schema:
            return ["any"]

        if "$ref" in schema:
            ref = schema["$ref"]
            resolved = self.resolve(ref)
            if resolved is None:
                return ["any"]
            name = class_name(self.def_name(ref))
            if self.is_object_def(resolved):
                return [name]
            if name in self.stack:
                self.note(f"рекурсивный $ref раскрыт как any: {ref}")
                return ["any"]
            self.stack.append(name)
            try:
                return self.render_type(resolved, indent)
            finally:
                self.stack.pop()

        if "enum" in schema:
            return ["enum { " + " | ".join(lit(v) for v in schema["enum"]) + " }"]

        for key in ("oneOf", "anyOf"):
            if key in schema:
                return self.render_union(schema[key], indent)

        type_ = schema.get("type")

        if type_ == "array" or "items" in schema or "prefixItems" in schema:
            if "prefixItems" in schema and "items" not in schema:
                self.note("prefixItems (кортеж) упрощён до [any]")
                return ["[any]"]
            items = schema.get("items")
            if not isinstance(items, dict):
                return ["[any]"]
            inner = self.render_type(items, indent + 1)
            if len(inner) == 1:
                return [f"[{inner[0]}]"]
            return (
                ["["]
                + [self.pad(indent + 1) + inner[0]]
                + inner[1:-1]
                + [inner[-1], self.pad(indent) + "]"]
            )

        if (
            type_ == "object"
            or "properties" in schema
            or "additionalProperties" in schema
        ):
            return self.render_object(schema, indent)

        if isinstance(type_, list):
            alts = [self.render_type({"type": t}, indent) for t in type_]
            return self.join_union(alts, indent)

        if type_ in PRIMITIVES:
            return [PRIMITIVES[type_]]

        self.note("схема без type/properties/enum упрощена до any")
        return ["any"]

    def render_union(self, alternatives: list, indent: int) -> list[str]:
        rendered = []
        for alt in alternatives:
            if alt == {}:
                self.note("пустая схема в anyOf/oneOf упрощена до any")
                return ["any"]
            rendered.append(self.render_type(alt, indent))
        return self.join_union(rendered, indent)

    def join_union(self, rendered: list[list[str]], indent: int) -> list[str]:
        unique: list[list[str]] = []
        seen: set[str] = set()
        for item in rendered:
            text = "\n".join(item)
            if text not in seen:
                seen.add(text)
                unique.append(item)
        if not unique:
            return ["any"]
        if all(len(item) == 1 for item in unique):
            return [" | ".join(item[0] for item in unique)]
        lines = [unique[0][0]]
        lines += unique[0][1:]
        for item in unique[1:]:
            lines.append(self.pad(indent) + "| " + item[0])
            lines += item[1:]
        return lines

    def collect_object(self, schema: dict) -> tuple[dict, set[str], Any]:
        """Собрать properties/required/additionalProperties с учётом allOf."""
        props: dict = {}
        required: set[str] = set()
        additional = None
        additional_owner = None

        parts = [schema] + list(schema.get("allOf") or [])
        for part in parts:
            if not isinstance(part, dict):
                continue
            if "$ref" in part:
                resolved = self.resolve(part["$ref"])
                if not isinstance(resolved, dict):
                    continue
                part = resolved
            props.update(part.get("properties") or {})
            required.update(part.get("required") or [])
            if "additionalProperties" in part and part["additionalProperties"] not in (
                False,
                None,
            ):
                additional = part["additionalProperties"]
                additional_owner = additional_owner or (
                    "properties" in schema and schema
                )

        if props and additional is not None:
            self.note(
                "additionalProperties у объекта с properties не выражен: "
                f"поля {sorted(props)[:3]}"
            )
        if schema.get("patternProperties"):
            self.note("patternProperties не выражен")
        return props, required, additional

    def render_object(self, schema: dict, indent: int) -> list[str]:
        props, required, additional = self.collect_object(schema)

        if not props:
            if additional is True or additional == {}:
                return ["map<any>"]
            if additional is not None:
                inner = self.render_type(additional, indent + 1)
                if len(inner) == 1:
                    return [f"map<{inner[0]}>"]
                return (
                    ["map<"]
                    + [self.pad(indent + 1) + inner[0]]
                    + inner[1:-1]
                    + [inner[-1], self.pad(indent) + ">"]
                )
            return ["{}"]

        lines = ["{"]
        for name, sub in props.items():
            lines += self.render_field(name, sub, name in required, indent + 1)
        lines.append(self.pad(indent) + "}")
        return lines

    def render_field(
        self, name: str, sub: Any, required: bool, indent: int
    ) -> list[str]:
        pad = self.pad(indent)
        out: list[str] = []

        if isinstance(sub, dict):
            description = sub.get("description")
            if description:
                for line in str(description).splitlines():
                    text = line.strip()
                    if text:
                        out.append(f"{pad}/// {text}")

        type_lines = self.render_type(sub, indent)
        optional = "" if required else "?"
        default = ""
        if isinstance(sub, dict) and "default" in sub:
            default = " = " + lit(sub["default"])

        if len(type_lines) == 1:
            out.append(f"{pad}{qkey(name)}{optional}: {type_lines[0]}{default};")
        else:
            out.append(f"{pad}{qkey(name)}{optional}: {type_lines[0]}")
            out.extend(type_lines[1:-1])
            out.append(type_lines[-1] + default + ";")
        return out

    # ----------------------------------------------------------------- class
    def render_class(self, name: str, schema: dict, indent: int = 1) -> list[str]:
        props, required, _additional = self.collect_object(schema)
        lines = [f"{self.pad(indent)}class {name} {{"]
        for field_name, sub in props.items():
            lines += self.render_field(
                field_name, sub, field_name in required, indent + 1
            )
        lines.append(f"{self.pad(indent)}}};")
        return lines

    # ------------------------------------------------------------------ main
    def convert(self, source_url: str) -> tuple[str, int]:
        out = [
            f"// Сгенерировано из {source_url}",
            "// Не редактировать вручную.",
            "schema => {",
        ]

        out.append("    class Config {")
        root_props, root_required, _ = self.collect_object(self.root)
        for field_name, sub in root_props.items():
            out += self.render_field(
                field_name, sub, field_name in root_required, 2
            )
        out.append("    };")

        class_count = 1
        for name, definition in self.defs.items():
            if not self.is_object_def(definition):
                continue
            out += self.render_class(class_name(name), definition, indent=1)
            class_count += 1

        out.append("}")
        return "\n".join(out) + "\n", class_count


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------


def generate_schema(
    json_schema: dict,
    source_url: str,
    notes: list[str] | None = None,
) -> str:
    """Сгенерировать DL-схему (``schema => { class ... }``) из JSON Schema.

    ``notes`` — необязательный список, куда складываются невыразимые
    ограничения (для отчёта CLI).
    """
    if not isinstance(json_schema, dict):
        raise SchemaGenerateError(
            "E013 SchemaGenerateError: JSON Schema must be an object"
        )
    converter = SchemaConverter(json_schema)
    try:
        text, _count = converter.convert(source_url)
    except Exception as error:  # noqa: BLE001 - любая ошибка конвертации = E013
        raise SchemaGenerateError(
            f"E013 SchemaGenerateError: {error}"
        ) from error
    if notes is not None:
        notes.extend(converter.notes)
    return text


def schema_filename(url: str) -> str:
    """Имя файла схемы из URL: ``.../config.json`` → ``config.schema``."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/")
    last = path.rsplit("/", 1)[-1] if path else ""
    if not last:
        return DEFAULT_SCHEMA_NAME
    stem = last.rsplit(".", 1)[0] if "." in last else last
    if not stem:
        return DEFAULT_SCHEMA_NAME
    return f"{stem}.schema"


def download_schema(url: str, timeout: float = 30) -> dict:
    """Скачать JSON Schema по URL (``E012`` при любой ошибке).

    Поддерживаются http(s), file и любые схемы, понятные ``urllib``.
    """
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": DEFAULT_USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise SchemaFetchError(
            f"E012 SchemaFetchError: cannot fetch {url}: {error}"
        ) from error
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise SchemaFetchError(
            f"E012 SchemaFetchError: invalid JSON from {url}: {error}"
        ) from error
    if not isinstance(data, dict):
        raise SchemaFetchError(
            f"E012 SchemaFetchError: schema at {url} is not a JSON object"
        )
    return data


def ensure_schema(url: str, dest_dir: Path | str, force: bool = False) -> Path:
    """Скачать, сгенерировать и закэшировать схему.

    Файл называется по последнему сегменту URL (``config.json`` →
    ``config.schema``) и лежит в ``dest_dir``. Существующий файл
    используется повторно, если ``force=False``.
    """
    directory = Path(dest_dir)
    destination = directory / schema_filename(url)
    if destination.is_file() and not force:
        return destination

    data = download_schema(url)
    text = generate_schema(data, url)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
    except OSError as error:
        raise SchemaGenerateError(
            f"E013 SchemaGenerateError: cannot write {destination}: {error}"
        ) from error
    return destination


def load_schema(path: Path | str) -> list[dict]:
    """Прочитать файл ``*.schema`` и вернуть список классов.

    Схема — обычный DL-документ: parse + evaluate (``kind == "schema"``).
    """
    from .evaluator import evaluate
    from .parser import parse

    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        raise SchemaGenerateError(
            f"E013 SchemaGenerateError: cannot read {source}: {error}"
        ) from error
    ast = parse(text, str(source))
    value = evaluate(ast, source.parent)
    if not isinstance(value, dict) or value.get("kind") != "schema":
        raise SchemaGenerateError(
            f"E013 SchemaGenerateError: {source} is not a schema document"
        )
    return list(value.get("classes") or [])


__all__ = [
    "SchemaConverter",
    "class_name",
    "download_schema",
    "ensure_schema",
    "generate_schema",
    "lit",
    "load_schema",
    "qkey",
    "schema_filename",
]
