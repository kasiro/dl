"""Модульный режим DL v2.2 (шаг 2).

Публичный API:

    collect(root_path, settings=None) -> dict config

Модель:

* корневой документ (``module`` или ``config``) — :class:`Function`;
* ``collect`` рекурсивно обходит дерево ``import``-ов корневого модуля
  (дети на месте родителя, порядок по появлению в теле);
* каждый модуль вызывается с ``($, $config)``; ``$`` — контекст (копия
  ``settings``), ``$config`` — накапливаемая конфигурация;
* результаты сливаются через :func:`dl.merger.deep_merge` — поздний
  переопределяет ранний (первый этап слияния);
* вложенные ``import``-ы внутри модулей обходятся так же;
* цикл в дереве импортов — ``E004``.

``import`` внутри тела модуля по новой семантике возвращает
:class:`Function` — вызов явный; ``collect`` при этом сливает результаты
всех модулей дерева независимо от того, вызвал ли родитель ребёнка сам.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import CircularImportError, ParseError
from .evaluator import Function, call_value, evaluate_file
from .merger import deep_merge
from .resolver import resolve_import


def _iter_statements(body: list[dict]):
    """Все инструкции тела в порядке появления (включая вложенные объекты)."""
    for stmt in body:
        yield stmt
        kind = stmt.get("kind")
        if kind in {"field", "spread", "expr", "let"}:
            yield from _iter_expr_statements(stmt.get("value"))


def _iter_outputs_statements(outputs: dict):
    """Инструкции из outputs блока."""
    # outputs - это dict вида {"opencode.json": {format: "json", value: {...}}}
    # Нужно извлечь value из каждого output и обойти их
    for output_name, output_spec in outputs.items():
        if isinstance(output_spec, dict):
            value = output_spec.get("value")
            if isinstance(value, dict) and value.get("kind") == "object":
                yield from _iter_statements(value.get("body") or [])


def _iter_expr_statements(node: Any):
    """Инструкции вложенных объектных литералов в выражении (по порядку)."""
    if not isinstance(node, dict):
        return
    if node.get("kind") == "object":
        yield from _iter_statements(node.get("body") or [])


def _collect_imports(fn: Function) -> list[dict]:
    """Import-узлы AST тела модуля в порядке появления.

    Обходятся инструкции тела (включая тела вложенных объектных литералов):
    ``import``/``imports`` — напрямую; ``let``/поле/spread/вызов-инструкция —
    через выражения (вызовы, массивы, объекты). Первый найденный import в
    каждой ветке завершает обход вниз (вложенные import-ы найдёт обход тела
    импортированного модуля).
    """
    found: list[dict] = []

    def walk_expr(node: Any) -> None:
        if not isinstance(node, dict):
            return
        kind = node.get("kind")
        if kind == "import":
            found.append(node)
            return
        if kind == "call":
            for arg in node.get("positional") or []:
                walk_expr(arg)
            for stmt in node.get("named") or []:
                walk_stmt(stmt)
        elif kind == "array":
            for item in node.get("items") or []:
                walk_expr(item)
        elif kind == "object":
            for stmt in node.get("body") or []:
                walk_stmt(stmt)

    def walk_stmt(stmt: dict) -> None:
        kind = stmt.get("kind")
        if kind == "import":
            value = stmt.get("value")
            if isinstance(value, dict):
                walk_expr(value)
        elif kind == "imports":
            for value in stmt.get("values") or []:
                walk_expr(value)
        elif kind == "let":
            # Не обходим import внутри let — это библиотеки/фабрики, не модули
            value = stmt.get("value")
            if value and value.get("kind") != "import":
                walk_expr(value)
        elif kind == "field":
            walk_expr(stmt.get("value"))
        elif kind == "spread":
            walk_expr(stmt.get("value"))
        elif kind == "expr":
            walk_expr(stmt.get("value"))

    for stmt in fn.body or []:
        walk_stmt(stmt)
    return found


def _import_path(node: dict, base_dir: Path) -> Path:
    """Абсолютный путь import-узла (литеральные пути; интерполяция не
    поддерживается на этапе обхода — сегменты с ``{expr}`` требуют scope)."""
    path = node.get("path") or ""
    if node.get("parts"):
        raise ParseError(
            "E006 ParseError: interpolated import paths are not supported "
            f"in module collection: {path}"
        )
    if node.get("glob"):
        raise ParseError(
            "E006 ParseError: glob imports are not supported "
            f"in module collection: {path}"
        )
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.resolve()


def collect(root_path: Path | str, settings: dict | None = None) -> dict:
    """Собрать конфигурацию из дерева импортов корневого модуля.

    Двухфазное вычисление (Nix-модель, шаг 3):
    - Проход 1: $config = {}, вызывает модули, собирает их вклад (игнорируя
      ссылки на $config — они подставляются как пустой объект).
    - Проход 2: $config = результат прохода 1, пересчитывает модули с полным
      $config.
    Для ациклических зависимостей достаточно. Циклы → E004.

    ``root_path`` — путь к корневому документу (``module`` или ``config``).
    ``settings`` — начальная конфигурация/контекст (например, из
    ``settings.dl``); модули получают копию как ``$`` и как начальный
    ``$config``.

    Возвращает накопленный ``config``: копия ``settings`` + deep_merge
    результатов всех модулей дерева (префиксный DFS: родитель, затем дети
    в порядке появления import-ов; поздний переопределяет ранний).
    """
    root = Path(root_path)
    if not root.is_file():
        raise ParseError(f"E006 ParseError: file not found: {root}")

    ctx: dict = dict(settings) if settings else {}

    value = evaluate_file(root)
    if not isinstance(value, Function):
        raise ParseError(
            f"E006 ParseError: {root.name} did not produce a module"
        )

    # Сбор списка всех модулей дерева (префиксный DFS)
    all_modules: list[tuple[Function, str]] = []
    visited: set[str] = set()

    def collect_modules(fn: Function, key: str) -> None:
        if key in visited:
            raise CircularImportError(
                f"E004 CircularImportError: circular import "
                f"{key} (module collection)"
            )
        visited.add(key)
        all_modules.append((fn, key))
        try:
            for node in _collect_imports(fn):
                child_path = _import_path(node, Path(fn.base_dir))
                child = resolve_import(
                    str(child_path), child_path.parent, ctx
                )
                if not isinstance(child, Function):
                    raise ParseError(
                        "E006 ParseError: imported document is not a module: "
                        f"{child_path}"
                    )
                collect_modules(child, str(child_path))
        finally:
            visited.discard(key)

    collect_modules(value, str(root.resolve()))

    # Проход 1: config = {} (пустой), собираем вклад всех модулей
    config_pass1: dict = dict(settings) if settings else {}
    visited_pass1: set[str] = set()

    def visit_pass1(fn: Function, key: str) -> None:
        if key in visited_pass1:
            return  # уже обработано в этом проходе
        visited_pass1.add(key)
        result = call_value(fn, [], None, ctx, fn.base_dir, config_pass1)
        if not isinstance(result, dict):
            raise ParseError(
                "E006 ParseError: module must produce an object, "
                f"got {type(result).__name__}"
            )
        deep_merge(config_pass1, result)

    for fn, key in all_modules:
        visit_pass1(fn, key)

    # Проход 2: config = результат прохода 1, пересчитываем с полным $config
    config: dict = dict(config_pass1)
    visited_pass2: set[str] = set()

    def visit_pass2(fn: Function, key: str) -> None:
        if key in visited_pass2:
            return  # уже обработано в этом проходе
        visited_pass2.add(key)
        result = call_value(fn, [], None, ctx, fn.base_dir, config)
        if not isinstance(result, dict):
            raise ParseError(
                "E006 ParseError: module must produce an object, "
                f"got {type(result).__name__}"
            )
        deep_merge(config, result)

    for fn, key in all_modules:
        visit_pass2(fn, key)

    return config


__all__ = ["collect"]
