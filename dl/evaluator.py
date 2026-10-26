"""Вычисление AST DL v2.1.

Публичный API:

    evaluate(ast, base_dir, context=None) -> dict | Function | dict-schema
    evaluate_file(path, context=None)
    evaluate_settings(ast, base_dir)
    evaluate_settings_file(path)
    call_value(fn, positional, named, ctx=None, base_dir=None)

Семантика (раздел 5–7 спецификации):

* документ ``config`` вычисляется сразу в словарь;
* документ ``module`` возвращается как :class:`Function` (даже если параметров
  нет — ``()``);
* документ ``schema`` возвращает описание классов для этапа 3;
* ``$`` (контекст) объявляется только параметром ``$``; обращение к ``$`` без
  него — ``E008``;
* контекст передаётся неявно по всей цепочке вызовов;
* блок выполняется сверху вниз: ``let`` — в scope, поля — с ``W001``/``E003``,
  spread и вызовы-инструкции — с переопределением (без конфликта).

Одно уточнение контракта: модуль **без параметров вообще** (``() =>``) при
импорте вызывается сразу — иначе ``models: import ./models/{name}.dl``
возвращал бы функцию, а не словарь моделей. Модули с объявленными параметрами
(в том числе с одним ``$``) остаются значениями-функциями.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import (
    DLContextError,
    GlobParameterizedModule,
    MissingParameterError,
    ParseError,
    UnknownParameterError,
)
from .merger import deep_merge, set_path
from .resolver import resolve_import

# ---------------------------------------------------------------------------
# Значения
# ---------------------------------------------------------------------------


@dataclass
class Function:
    """Модуль с параметрами: сигнатура + тело + каталог для импортов."""

    params: list[dict]
    body: list[dict]
    base_dir: Path
    name: str | None = None

    def __repr__(self) -> str:  # компактно в отчётах/ошибках
        names = ", ".join(param["name"] for param in self.params)
        return f"Function({names})"


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------


def as_path(base_dir: Path | str | None) -> Path:
    """Привести base_dir к абсолютному Path."""
    if base_dir is None:
        return Path.cwd()
    return Path(base_dir).resolve()


def _to_str(value: Any) -> str:
    """Приведение значения к строке для интерполяции."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def interp_segment(segment: str, scope: dict, ctx: dict | None) -> str:
    """Интерполировать сегмент точечного пути (ключ в кавычках: ``"{name}"``)."""
    if "{" not in segment:
        return segment
    from .parser import _split_interpolation

    parts = _split_interpolation(segment)
    if len(parts) == 1 and parts[0][0] == "lit":
        return segment
    chunks: list[str] = []
    for part in parts:
        if part[0] == "lit":
            chunks.append(str(part[1]))
        else:
            ref = part[1]
            assert isinstance(ref, list)
            chunks.append(_to_str(_lookup_ref(ref, scope, ctx)))
    return "".join(chunks)


def _has_context(params: list[dict]) -> bool:
    return any(param["name"] == "$" for param in params)


def _user_params(params: list[dict]) -> list[dict]:
    """Параметры без ``$`` — они участвуют в позиционном/именованном вызове."""
    return [param for param in params if param["name"] != "$"]


def _lookup_ref(path: list[str], scope: dict, ctx: dict | None) -> Any:
    """Разрешить путь ``ref``: ``$`` → контекст, иначе — scope."""
    if path[0] == "$":
        if "$" not in scope:
            raise DLContextError(
                "E008 NoContext: '$' used without context in signature"
            )
        value = scope["$"]
        rest = path[1:]
    else:
        name = path[0]
        if name not in scope:
            raise ParseError(
                f"E006 ParseError: undefined reference '{name}'"
            )
        value = scope[name]
        rest = path[1:]

    for segment in rest:
        if not isinstance(value, dict):
            raise ParseError(
                f"E006 ParseError: cannot access '{segment}' "
                f"in non-object value {value!r}"
            )
        if segment not in value:
            raise ParseError(
                f"E006 ParseError: undefined reference "
                f"'{'.'.join(path)}' (missing '{segment}')"
            )
        value = value[segment]
    return value


# ---------------------------------------------------------------------------
# Вызовы
# ---------------------------------------------------------------------------


def call_value(
    fn: Function,
    positional: list[Any],
    named: dict[str, Any] | None,
    ctx: dict | None = None,
    base_dir: Path | str | None = None,
) -> dict:
    """Вызвать функцию модуля.

    ``positional``/``named`` — уже вычисленные значения аргументов.
    ``$`` в именованных аргументах не передаётся: контекст подставляется
    неявно и распространяется по цепочке вызовов.
    """
    if not isinstance(fn, Function):
        raise ParseError("E006 ParseError: value is not a function")

    params = fn.params or []
    rest = _user_params(params)
    scope: dict[str, Any] = {}

    if _has_context(params):
        if ctx is None:
            ctx = {}
        scope["$"] = ctx

    # Позиционные — по порядку параметров после `$`.
    if len(positional) > len(rest):
        raise UnknownParameterError(
            f"E009 UnknownParameter: too many positional arguments "
            f"({len(positional)} for {len(rest)} parameters)"
        )
    for param, value in zip(rest, positional):
        scope[param["name"]] = value

    # Именованные — по имени.
    if named:
        by_name = {param["name"]: param for param in rest}
        for key, value in named.items():
            if key == "$":
                raise UnknownParameterError(
                    "E009 UnknownParameter: '$' is passed implicitly"
                )
            param = by_name.get(key)
            if param is None:
                raise UnknownParameterError(
                    f"E009 UnknownParameter: unknown parameter '{key}'"
                )
            if key in scope:
                raise ParseError(
                    f"E006 ParseError: parameter '{key}' passed twice"
                )
            scope[key] = value

    # Дефолты и опциональные параметры.
    module_dir = as_path(fn.base_dir or base_dir)
    for param in rest:
        name = param["name"]
        if name in scope:
            continue
        if param["default"] is not None:
            scope[name] = eval_expr(param["default"], scope, ctx, module_dir)
        elif param["optional"]:
            scope[name] = None
        else:
            raise MissingParameterError(
                f"E010 MissingParameter: missing required parameter '{name}'"
            )

    return eval_block(fn.body or [], scope, ctx, module_dir)


# ---------------------------------------------------------------------------
# Блоки и выражения
# ---------------------------------------------------------------------------


def eval_block(
    body: list[dict],
    scope: dict,
    ctx: dict | None,
    base_dir: Path,
) -> dict:
    """Выполнить блок сверху вниз и вернуть объект-результат."""
    result: dict[str, Any] = {}

    for stmt in body:
        kind = stmt["kind"]

        if kind == "let":
            scope[stmt["name"]] = eval_expr(stmt["value"], scope, ctx, base_dir)

        elif kind == "field":
            value = eval_expr(stmt["value"], scope, ctx, base_dir)
            if stmt.get("optional") and value is None:
                continue
            path = stmt["path"]
            if path and path[0] == "$":
                path = ["$", *(interp_segment(s, scope, ctx) for s in path[1:])]
            else:
                path = [interp_segment(segment, scope, ctx) for segment in path]
            if path and path[0] == "$":
                if "$" not in scope:
                    raise DLContextError(
                        "E008 NoContext: '$' used without context in signature"
                    )
                if ctx is None:
                    raise DLContextError(
                        "E008 NoContext: context is not available for writing"
                    )
                set_path(ctx, path[1:], value)
            else:
                set_path(result, path, value)

        elif kind == "spread":
            value = eval_expr(stmt["value"], scope, ctx, base_dir)
            if not isinstance(value, dict):
                raise ParseError(
                    f"E006 ParseError: spread expects an object, "
                    f"got {type(value).__name__}"
                )
            deep_merge(result, value)

        elif kind == "expr":
            value = eval_expr(stmt["value"], scope, ctx, base_dir)
            if not isinstance(value, dict):
                raise ParseError(
                    f"E006 ParseError: expression result must be an object, "
                    f"got {type(value).__name__}"
                )
            deep_merge(result, value)

        else:  # pragma: no cover - защита от расширения AST
            raise ParseError(f"E006 ParseError: unknown statement '{kind}'")

    return result


def eval_expr(
    node: dict,
    scope: dict,
    ctx: dict | None,
    base_dir: Path,
) -> Any:
    """Вычислить выражение."""
    kind = node["kind"]

    if kind == "string":
        chunks: list[str] = []
        for part in node["parts"]:
            if part[0] == "lit":
                chunks.append(part[1])
            else:
                chunks.append(_to_str(_lookup_ref(part[1], scope, ctx)))
        return "".join(chunks)

    if kind in {"int", "float", "bool"}:
        return node["value"]

    if kind == "null":
        return None

    if kind == "array":
        return [eval_expr(item, scope, ctx, base_dir) for item in node["items"]]

    if kind == "object":
        return eval_block(node["body"], scope, ctx, base_dir)

    if kind == "call":
        name = node["name"]
        if name not in scope:
            raise ParseError(f"E006 ParseError: unknown function '{name}'")
        fn = scope[name]
        if not isinstance(fn, Function):
            raise ParseError(
                f"E006 ParseError: '{name}' is not a function "
                f"({type(fn).__name__})"
            )
        positional = [
            eval_expr(arg, scope, ctx, base_dir)
            for arg in node["positional"]
        ]
        named_body = node.get("named")
        named = (
            eval_block(named_body, scope, ctx, base_dir)
            if named_body is not None
            else None
        )
        return call_value(fn, positional, named, ctx, base_dir)

    if kind == "import":
        path = eval_import_path(node, scope, ctx)
        is_glob = node.get("glob", False)
        if is_glob:
            from .resolver import resolve_glob_import
            value = resolve_glob_import(path, base_dir, ctx)
        else:
            value = resolve_import(path, base_dir, ctx)
        # Модуль без параметров вообще (``() =>``) — значение, а не функция:
        # так ``models: import ./models/{name}.dl`` даёт словарь моделей.
        # Модуль с ``$`` остаётся функцией (контекст передаётся при вызове).
        if isinstance(value, Function) and not value.params:
            return call_value(value, [], None, ctx, base_dir)
        return value

    if kind == "ref":
        return _lookup_ref(node["path"], scope, ctx)

    raise ParseError(f"E006 ParseError: unknown expression '{kind}'")


def eval_import_path(
    node: dict,
    scope: dict,
    ctx: dict | None,
) -> str:
    """Собрать путь импорта с интерполяцией ``{expr}``."""
    parts = node.get("parts")
    if not parts:
        return node["path"]
    chunks: list[str] = []
    for part in parts:
        if part[0] == "lit":
            chunks.append(part[1])
        else:
            chunks.append(_to_str(_lookup_ref(part[1], scope, ctx)))
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Документы
# ---------------------------------------------------------------------------


def evaluate(
    ast: dict,
    base_dir: Path | str | None = None,
    context: dict | None = None,
) -> Any:
    """Вычислить документ DL.

    ``config`` → dict, ``module`` → :class:`Function`, ``schema`` → описание
    классов (``{"kind": "schema", "classes": [...]}``).
    """
    directory = as_path(base_dir)
    kind = ast.get("kind")

    if kind == "config":
        params = ast.get("params") or []
        fn = Function(params=params, body=ast.get("body") or [], base_dir=directory)
        return call_value(fn, [], None, context, directory)

    if kind == "module":
        return Function(
            params=ast.get("params") or [],
            body=ast.get("body") or [],
            base_dir=directory,
        )

    if kind == "schema":
        return {"kind": "schema", "classes": list(ast.get("body") or [])}

    raise ParseError(f"E006 ParseError: unknown document kind '{kind}'")


def evaluate_file(path: Path | str, context: dict | None = None) -> Any:
    """Прочитать и вычислить файл DL."""
    from .parser import parse

    source = Path(path)
    ast = parse(source.read_text(encoding="utf-8"), str(source))
    return evaluate(ast, source.parent, context)


def evaluate_settings(ast: dict, base_dir: Path | str | None = None) -> dict:
    """Вычислить ``settings.dl`` и вернуть контекст.

    Модуль вызывается с пустым контекстом; инструкции ``$.x: value`` пишут в
    него, поэтому результатом является сам контекст.
    """
    directory = as_path(base_dir)
    value = evaluate(ast, directory)
    if not isinstance(value, Function):
        raise ParseError(
            "E006 ParseError: settings document must be a module with '$'"
        )
    ctx: dict = {}
    call_value(value, [], None, ctx, directory)
    return ctx


def evaluate_settings_file(path: Path | str) -> dict:
    """Прочитать и вычислить ``settings.dl``."""
    from .parser import parse

    source = Path(path)
    ast = parse(source.read_text(encoding="utf-8"), str(source))
    return evaluate_settings(ast, source.parent)


__all__ = [
    "Function",
    "call_value",
    "eval_block",
    "eval_expr",
    "evaluate",
    "evaluate_file",
    "evaluate_settings",
    "evaluate_settings_file",
]
