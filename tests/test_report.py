"""Тесты дерева сборки (dl.report) и флага ``--no-progress``."""

from __future__ import annotations

import shutil
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from dl.cli import main
from dl.report import (
    CACHED,
    ERROR,
    BuildReporter,
    get_reporter,
    set_reporter,
)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def make_reporter(**kwargs) -> tuple[BuildReporter, StringIO]:
    """Репортёр с неинтерактивным консольным потоком (без Live)."""
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=100)
    return BuildReporter(console=console, **kwargs), stream


def nonempty(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


# ──────────────────────────── успешная сборка ───────────────────────────────


def test_successful_tree_order_and_statuses(tmp_path: Path):
    source = tmp_path / "configuration.dl"
    target = tmp_path / "opencode.json"
    reporter, stream = make_reporter()

    reporter.start(source, target)
    reporter.file_start(source)
    reporter.file_end(source)
    reporter.stage("schema", "schema")
    reporter.stage_done("schema", "config.schema")
    reporter.stage("validate", "validate")
    reporter.stage_done("validate", "Config")
    reporter.stage("write", "write")
    reporter.stage_done("write", "opencode.json")
    reporter.finish()

    text = stream.getvalue()
    lines = nonempty(text)

    assert lines[0] == "configuration.dl → opencode.json"
    assert lines[1].endswith("configuration.dl ✓")
    assert "schema config.schema ✓" in text
    assert "validate Config ✓" in text
    assert "write opencode.json ✓" in text

    order = [
        text.index("configuration.dl ✓"),
        text.index("schema config.schema ✓"),
        text.index("validate Config ✓"),
        text.index("write opencode.json ✓"),
    ]
    assert order == sorted(order)
    # дерево напечатано ровно один раз
    assert text.count("configuration.dl → opencode.json") == 1


# ───────────────────────────── вложенность ──────────────────────────────────


def test_import_nesting_follows_file_stack(tmp_path: Path):
    source = tmp_path / "configuration.dl"
    first = tmp_path / "providers" / "a.dl"
    second = tmp_path / "providers" / "b.dl"
    reporter, stream = make_reporter()

    reporter.start(source, tmp_path / "out.json")
    reporter.file_start(source)
    reporter.file_start(first)
    reporter.file_start(second)
    reporter.file_end(second)
    reporter.file_end(first)
    reporter.file_end(source)
    reporter.finish()

    lines = nonempty(stream.getvalue())
    line_a = next(line for line in lines if "providers/a.dl" in line)
    line_b = next(line for line in lines if "providers/b.dl" in line)

    # b вложен глубже a и идёт после него
    assert len(line_b) - len(line_b.lstrip()) > len(line_a) - len(line_a.lstrip())
    assert lines.index(line_a) < lines.index(line_b)
    assert line_a.endswith("✓") and line_b.endswith("✓")


# ──────────────────────────────── cached ────────────────────────────────────


def test_cached_import_is_marked(tmp_path: Path):
    source = tmp_path / "configuration.dl"
    module = tmp_path / "providers" / "cached.dl"
    reporter, stream = make_reporter()

    reporter.start(source, tmp_path / "out.json")
    reporter.file_start(source)
    reporter.file_start(module, cached=True)
    reporter.file_end(module)
    reporter.file_end(source)
    reporter.finish()

    text = stream.getvalue()
    assert "providers/cached.dl ○ cached" in text
    assert "✓ cached" not in text


# ──────────────────────────────── ошибка ────────────────────────────────────


def test_error_node_and_tree_still_printed(tmp_path: Path):
    source = tmp_path / "configuration.dl"
    reporter, stream = make_reporter()

    reporter.start(source, tmp_path / "out.json")
    reporter.file_start(source)
    reporter.file_end(source)
    reporter.stage("validate", "validate")
    reporter.stage_error("validate", "E011 TypeMismatch: boom")
    reporter.fail("E011 TypeMismatch: boom")
    reporter.finish()

    text = stream.getvalue()

    assert "validate ✗" in text
    assert "E011 TypeMismatch: boom" in text
    assert reporter._stages["validate"].status == "error"
    assert nonempty(text)  # дерево напечатано

    # глиф действительно красный (проверяем на терминальной консоли)
    colored = StringIO()
    fancy = Console(file=colored, force_terminal=True, width=100)
    fancy.print(reporter._node_text(reporter._stages["validate"]))
    assert "\x1b[31m" in colored.getvalue()


def test_finish_in_finally_prints_tree(tmp_path: Path):
    reporter, stream = make_reporter()
    reporter.start(tmp_path / "configuration.dl", tmp_path / "out.json")
    reporter.file_start(tmp_path / "configuration.dl")

    with pytest.raises(RuntimeError):
        try:
            raise RuntimeError("boom")
        except RuntimeError as error:
            reporter.file_end(tmp_path / "configuration.dl", error=error)
            reporter.fail("boom")
            raise
        finally:
            reporter.finish()

    text = stream.getvalue()
    assert "configuration.dl ✗" in text
    assert "boom" in text


def test_finish_is_idempotent(tmp_path: Path):
    reporter, stream = make_reporter()
    reporter.start(tmp_path / "configuration.dl", tmp_path / "out.json")
    reporter.finish()
    reporter.finish()

    assert stream.getvalue().count("configuration.dl") == 1


def test_disabled_reporter_has_no_live(tmp_path: Path):
    reporter, stream = make_reporter(enabled=False)
    reporter.start(tmp_path / "configuration.dl", tmp_path / "out.json")
    reporter.file_start(tmp_path / "configuration.dl")
    reporter.file_end(tmp_path / "configuration.dl")

    assert reporter._live is None
    reporter.finish()

    assert "configuration.dl ✓" in stream.getvalue()


# ────────────────────────── контекстная переменная ──────────────────────────


def test_reporter_context_default_is_none():
    assert get_reporter() is None
    reporter, _ = make_reporter()
    token = set_reporter(reporter)
    assert get_reporter() is reporter
    from dl.report import reset_reporter

    reset_reporter(token)
    assert get_reporter() is None


# ─────────────────────────────── CLI-флаг ──────────────────────────────────


def test_cli_compile_no_progress(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    copy = tmp_path / "examples"
    shutil.copytree(EXAMPLES, copy)
    monkeypatch.chdir(tmp_path)
    capsys.readouterr()

    code = main(["compile", "examples/configuration.dl", "--no-progress"])
    captured = capsys.readouterr()

    assert code == 0
    assert "Compiled:" in captured.out
    # --no-progress полностью отключает дерево: stderr пуст (ни дерева, ни ANSI)
    assert captured.err == ""
    assert (copy / "opencode.json").is_file()


# ───────────────────────── уникальность путей ──────────────────────────────


def test_repeated_import_is_one_node_with_uses(tmp_path: Path):
    source = tmp_path / "configuration.dl"
    module = tmp_path / "providers" / "shared.dl"
    reporter, stream = make_reporter()

    reporter.start(source, tmp_path / "out.json")
    reporter.file_start(source)
    for _ in range(4):
        reporter.file_start(module)
        reporter.file_end(module)
    reporter.file_end(source)
    reporter.finish()

    lines = nonempty(stream.getvalue())
    module_lines = [line for line in lines if "providers/shared.dl" in line]

    # один и тот же путь — ровно одна строка дерева
    assert len(module_lines) == 1
    assert "×4" in module_lines[0]
    assert module_lines[0].endswith("✓")

    node = reporter._nodes[str(module.resolve())]
    assert node.uses == 4
    assert node.status == "ok"
    # вложенность не изменилась: узел остался ребёнком корневого файла
    root_node = reporter._root.children[0]
    assert node in root_node.children
    assert len(root_node.children) == 1


def test_repeated_start_does_not_reset_completed_status(tmp_path: Path):
    module = tmp_path / "cached.dl"
    reporter, _ = make_reporter(enabled=False)
    reporter.start(tmp_path / "configuration.dl", tmp_path / "out.json")

    reporter.file_start(module, cached=True)
    reporter.file_end(module)
    node = reporter._nodes[str(module.resolve())]
    assert node.status == CACHED

    reporter.file_start(module)
    assert node.status == CACHED  # повторный старт не сбрасывает статус
    reporter.file_end(module)
    assert node.status == CACHED  # и повторный end тоже
    assert node.uses == 2


def test_repeated_end_does_not_clear_error(tmp_path: Path):
    module = tmp_path / "broken.dl"
    reporter, _ = make_reporter(enabled=False)
    reporter.start(tmp_path / "configuration.dl", tmp_path / "out.json")

    reporter.file_start(module)
    reporter.file_end(module, error="E006 boom")
    node = reporter._nodes[str(module.resolve())]
    assert node.status == ERROR

    reporter.file_start(module)
    reporter.file_end(module)
    assert node.status == ERROR
    assert node.error == "E006 boom"
    assert node.uses == 2
