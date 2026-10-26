"""Отчёт о сборке DL: дерево этапов и файлов в реальном времени.

Дерево рисуется в ``stderr`` (stdout компилятора не меняется). В терминале
используется :class:`rich.live.Live` с частотой 10 кадров в секунду; при
перенаправленном выводе или ``enabled=False`` дерево печатается один раз в
конце, без анимации.

Доступ из глубины компилятора (``Resolver.load``) — через контекстную
переменную::

    from .report import get_reporter

    reporter = get_reporter()
    if reporter is not None:
        reporter.file_start(path)

Один файл (по абсолютному пути) показывается в дереве один раз: повторные
обращения увеличивают счётчик ``uses`` (в подписи — ``×N``), не меняя
вложенность и статус уже завершённого узла. Без установленного репортёра
все обращения — no-op.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.tree import Tree

RUNNING = "running"
OK = "ok"
CACHED = "cached"
ERROR = "error"

_GLYPHS: dict[str, tuple[str, str]] = {
    RUNNING: ("⋯", "yellow"),
    OK: ("✓", "green"),
    CACHED: ("○", "dim"),
    ERROR: ("✗", "red"),
}

REFRESH_PER_SECOND = 10


def _one_line(message: str) -> str:
    """Первая строка сообщения: дерево не должно «разъезжаться»."""
    lines = str(message).strip().splitlines()
    return lines[0] if lines else ""


@dataclass
class _Node:
    """Узел внутренней модели дерева."""

    key: str
    label: str
    status: str = RUNNING
    detail: str = ""
    error: str = ""
    uses: int = 1
    children: list["_Node"] = field(default_factory=list)


class BuildReporter:
    """Модель дерева сборки и её отрисовка через ``rich``."""

    def __init__(
        self,
        console: Console | None = None,
        *,
        enabled: bool = True,
    ) -> None:
        self.console = console if console is not None else Console(stderr=True)
        self.enabled = enabled
        self._root = _Node(key="", label="")
        self._stages: dict[str, _Node] = {}
        # Один файл — один узел: реестр по абсолютному пути.
        self._nodes: dict[str, _Node] = {}
        self._stack: list[_Node] = []
        self._base_dir: Path | None = None
        self._started = False
        self._finished = False
        self._live: Live | None = None

    # ── пути ──────────────────────────────────────────────────────────────

    def display(self, path: str | os.PathLike[str]) -> str:
        """Путь относительно каталога исходника (вне его — с ``../``)."""
        candidate = Path(path)
        if self._base_dir is None:
            return candidate.name
        try:
            return os.path.relpath(candidate.resolve(), self._base_dir)
        except ValueError:  # разные диски (Windows)
            return candidate.name

    @staticmethod
    def _key(path: str | os.PathLike[str]) -> str:
        return str(Path(path).resolve())

    # ── события ───────────────────────────────────────────────────────────

    def start(
        self,
        source: str | os.PathLike[str],
        target: str | os.PathLike[str] | None = None,
    ) -> None:
        """Задать корень дерева: ``source → target``."""
        self._started = True
        self._base_dir = Path(source).resolve().parent
        destination = "?" if target is None else self.display(target)
        self._root.label = f"{self.display(source)} → {destination}"
        if self.enabled and self.console.is_terminal:
            live = Live(
                self._render(),
                console=self.console,
                refresh_per_second=REFRESH_PER_SECOND,
                transient=True,
            )
            live.start()
            self._live = live

    def stage(self, key: str, label: str) -> None:
        """Добавить этап сборки (``parse``, ``schema``, ``validate``, ...)."""
        node = _Node(key=key, label=label, status=RUNNING)
        self._root.children.append(node)
        self._stages[key] = node
        self._refresh()

    def stage_done(self, key: str, detail: str = "") -> None:
        """Отметить этап успешным, при необходимости — с пояснением."""
        node = self._stages.get(key)
        if node is None:
            return
        node.detail = detail
        if node.status != ERROR:
            node.status = OK
        self._refresh()

    def stage_error(self, key: str, message: str) -> None:
        """Отметить этап ошибочным."""
        node = self._stages.get(key)
        if node is None:
            return
        node.status = ERROR
        node.error = str(message)
        self._refresh()

    def file_start(
        self,
        path: str | os.PathLike[str],
        cached: bool = False,
    ) -> None:
        """Открыть файл; вложенность — по стеку открытых файлов.

        Повторный файл не дублируется: у существующего узла растёт ``uses``,
        позиция в дереве и статус не меняются.
        """
        key = self._key(path)
        existing = self._nodes.get(key)
        if existing is not None:
            existing.uses += 1
            self._stack.append(existing)
            self._refresh()
            return

        node = _Node(
            key=key,
            label=self.display(path),
            status=CACHED if cached else RUNNING,
        )
        self._nodes[key] = node
        parent = self._stack[-1] if self._stack else self._root
        parent.children.append(node)
        self._stack.append(node)
        self._refresh()

    def file_end(
        self,
        path: str | os.PathLike[str],
        error: BaseException | str | None = None,
    ) -> None:
        """Закрыть файл; ошибка помечает узел красным.

        Уже завершённый узел (``ok``/``cached``/``error``) без новой ошибки
        свой статус не меняет.
        """
        key = self._key(path)
        node: _Node | None = None
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index].key == key:
                node = self._stack[index]
                del self._stack[index:]
                break
        if node is None:
            return
        if error is not None:
            node.status = ERROR
            node.error = str(error)
        elif node.status == RUNNING:
            node.status = OK
        self._refresh()

    def fail(self, message: str) -> None:
        """Пометить сборку ошибочной (корень и незавершённые этапы)."""
        text = str(message)
        for node in self._walk(self._root):
            if node is not self._root and node.status == RUNNING:
                node.status = ERROR
                if not node.error:
                    node.error = text
        self._root.status = ERROR
        # Текст уже виден на упавшем узле — у корня не дублируем.
        self._root.error = "" if self._has_error(text) else text
        self._refresh()

    def _walk(self, node: _Node) -> Iterator[_Node]:
        yield node
        for child in node.children:
            yield from self._walk(child)

    def _has_error(self, text: str) -> bool:
        return any(
            node.status == ERROR and node.error == text
            for node in self._walk(self._root)
        )

    def finish(self) -> None:
        """Остановить Live и напечатать финальное дерево (идемпотентно)."""
        if self._finished:
            return
        self._finished = True
        if self._live is not None:
            self._live.stop()
            self._live = None
        if not self._started:
            return
        self.console.print(self._render())

    # ── отрисовка ─────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._render())

    def _render(self) -> Tree:
        label = Text(self._root.label)
        if self._root.status == ERROR:
            label.append(" ✗", style="red")
            if self._root.error:
                label.append(" " + _one_line(self._root.error), style="red")
        tree = Tree(label)
        for child in self._root.children:
            tree.add(self._render_node(child))
        return tree

    def _render_node(self, node: _Node) -> Tree:
        tree = Tree(self._node_text(node))
        for child in node.children:
            tree.add(self._render_node(child))
        return tree

    @staticmethod
    def _node_text(node: _Node) -> Text:
        text = Text(node.label)
        if node.uses > 1:
            text.append(f" ×{node.uses}")
        if node.detail:
            text.append(" " + node.detail)
        glyph, style = _GLYPHS[node.status]
        text.append(" " + glyph, style=style)
        if node.status == CACHED:
            text.append(" cached", style="dim")
        if node.status == ERROR and node.error:
            text.append(" " + _one_line(node.error), style="red")
        return text


# ── модульная точка доступа ────────────────────────────────────────────────

_reporter: ContextVar[BuildReporter | None] = ContextVar(
    "dl.build_reporter", default=None
)


def get_reporter() -> BuildReporter | None:
    """Текущий репортёр или ``None`` (тогда все события — no-op)."""
    return _reporter.get()


def set_reporter(
    reporter: BuildReporter | None,
) -> Token[BuildReporter | None]:
    """Установить репортёр для текущего контекста."""
    return _reporter.set(reporter)


def reset_reporter(token: Token[BuildReporter | None]) -> None:
    """Вернуть предыдущий репортёр (по токену ``set_reporter``)."""
    _reporter.reset(token)


__all__ = [
    "BuildReporter",
    "CACHED",
    "ERROR",
    "OK",
    "RUNNING",
    "get_reporter",
    "reset_reporter",
    "set_reporter",
]
