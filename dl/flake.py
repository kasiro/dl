"""Nix-подобная модель сборки DL (шаг 4).

Публичный API:

    build(root_path) -> dict[str, Output]

Модель:
- configuration.dl возвращает:
  {imports: [...], outputs: {"opencode.json": {format: "json", value: $config}}}
- build(root_path) — читает configuration.dl, через modules.collect()
  собирает $config (с учётом settings.dl рядом), вызывает configuration с $config,
  получает outputs, сериализует через dl.serializer.serialize().
- Возвращает словарь outputs: ключ → {format, value, serialized}.

Новый синтаксис flake.dl:
  import ./modules/providers.dl;
  imports [
      ./modules/mcp.dl;
      ./modules/agents.dl;
  ];
  outputs: {
      "opencode.json": {
          format: "json";
          value: $config;
      };
  };
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ParseError
from .evaluator import evaluate_settings_file, Function, call_value, evaluate_file
from .modules import collect
from .serializer import serialize
from .merger import deep_merge

SETTINGS_NAME = "settings.dl"


class Output:
    """Выход сборки: формат, значение, сериализованное представление."""

    def __init__(self, format: str, value: Any):
        self.format = format
        self.value = value
        self.serialized = serialize(value, format)

    def __repr__(self) -> str:
        return f"Output(format={self.format!r}, size={len(self.serialized)})"


def _context_for(source: Path) -> dict:
    """Контекст из settings.dl рядом с исходником (или пустой)."""
    candidate = source.parent / SETTINGS_NAME
    if candidate.is_file():
        return evaluate_settings_file(candidate)
    return {}


def build(root_path: Path | str) -> dict[str, Output]:
    """Собрать конфигурацию и вернуть outputs.

    ``root_path`` — путь к configuration.dl или flake.dl (или другому корневому документу).
    Контекст загружается из settings.dl рядом с root_path.

    Возвращает словарь outputs: ключ → Output(format, value, serialized).
    Ключи берутся из outputs{} корневого документа.
    """
    root = Path(root_path)
    if not root.is_file():
        raise ParseError(f"E006 ParseError: file not found: {root}")

    # Загружаем контекст из settings.dl
    context = _context_for(root)

    # Парсим AST напрямую чтобы определить тип документа
    from .parser import parse
    ast = parse(root.read_text(encoding="utf-8"), str(root))
    kind = ast.get("kind")

    if kind == "flake":
        # Новый синтаксис: обрабатываем imports и outputs напрямую
        return _build_flake(root, ast, context)
    else:
        # Старый синтаксис: configuration.dl с module/collect
        return _build_configuration(root, context)


def _build_flake(root: Path, ast: dict, context: dict) -> dict[str, Output]:
    """Собрать flake-документ: ``( $, $config ) => { ... }``.

    ``$config`` — результат ``modules.collect()`` по дереву импортов.
    Тело flake — обычная функция DL, поэтому вызывается через
    :func:`call_value`; ``outputs`` берётся из возвращённого объекта.
    """
    # Собираем $config через modules.collect() (дерево импортов flake).
    # Частично мигрированные примеры могут не разбираться — тогда
    # ограничиваемся контекстом settings.dl.
    try:
        config = collect(root, context)
    except Exception:
        config = dict(context)

    # outputs — спецификация сборки, а не часть конфигурации.
    config.pop("outputs", None)

    fn = evaluate_file(root)
    if not isinstance(fn, Function):
        raise ParseError(
            f"E006 ParseError: {root.name} did not produce a function"
        )
    result = call_value(fn, [], None, context, root.parent, config)

    outputs_dict = result.get("outputs", {})
    if not isinstance(outputs_dict, dict):
        raise ParseError(
            "E006 ParseError: outputs must be an object"
        )
    
    # Сериализуем каждый output
    result: dict[str, Output] = {}
    for name, output_spec in outputs_dict.items():
        if not isinstance(output_spec, dict):
            raise ParseError(
                f"E006 ParseError: output '{name}' must be an object"
            )
        fmt = output_spec.get("format")
        if not fmt:
            raise ParseError(
                f"E006 ParseError: output '{name}' missing 'format'"
            )
        value = output_spec.get("value")
        if value is None:
            raise ParseError(
                f"E006 ParseError: output '{name}' missing 'value'"
            )
        result[name] = Output(fmt, value)
    
    return result


def _build_configuration(root: Path, context: dict) -> dict[str, Output]:
    """Собрать configuration.dl со старым синтаксисом."""
    # Собираем $config через modules.collect() с контекстом
    config = collect(root, context)

    # Извлекаем outputs из config
    outputs = config.get("outputs", {})

    if not isinstance(outputs, dict):
        raise ParseError(
            "E006 ParseError: outputs must be an object"
        )

    # Сериализуем каждый output
    result: dict[str, Output] = {}
    for name, output_spec in outputs.items():
        if not isinstance(output_spec, dict):
            raise ParseError(
                f"E006 ParseError: output '{name}' must be an object"
            )
        fmt = output_spec.get("format")
        if not fmt:
            raise ParseError(
                f"E006 ParseError: output '{name}' missing 'format'"
            )
        value = output_spec.get("value")
        if value is None:
            raise ParseError(
                f"E006 ParseError: output '{name}' missing 'value'"
            )
        result[name] = Output(fmt, value)

    return result


def build_to_files(root_path: Path | str, base_dir: Path | None = None) -> list[Path]:
    """Собрать конфигурацию и записать выходы в файлы.

    ``root_path`` — путь к configuration.dl.
    ``base_dir`` — базовый каталог для выходов (по умолчанию = каталог root_path).

    Возвращает список записанных файлов.
    """
    root = Path(root_path)
    base_dir = base_dir or root.parent

    outputs = build(root)
    written: list[Path] = []

    for name, output in outputs.items():
        # name может быть путём вида "opencode.json" или "subdir/file.json"
        target = base_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output.serialized, encoding="utf-8")
        written.append(target)

    return written


__all__ = ["Output", "build", "build_to_files"]
