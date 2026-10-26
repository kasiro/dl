"""LSP-сервер для языка DL.

Поддерживаемые методы:
- textDocument/diagnostic — парсинг файла, возврат Diagnostic
- textDocument/publishDiagnostics — автоотправка при изменении
- textDocument/hover — показать тип/значение для ключа или переменной
- textDocument/completion — заглушка (отложено)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken
from pygls.lsp.server import LanguageServer
from lsprotocol.types import (
    CompletionList,
    CompletionOptions,
    CompletionParams,
    Diagnostic,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    Position,
    PublishDiagnosticsParams,
    Range,
    TextDocumentSyncKind,
)

from dl.errors import DLError
from dl.parser import parse

# ---------------------------------------------------------------------------
# Логирование
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Сервер
# ---------------------------------------------------------------------------

server = LanguageServer(
    name="dl-lsp",
    version="0.1.0",
)


def _lark_error_to_diagnostic(
    error: LarkError,
    source: str,
) -> Diagnostic:
    """Преобразовать ошибку Lark в Diagnostic.

    LarkError может быть:
    - UnexpectedCharacters: неожиданная лексема
    - UnexpectedToken: неожиданная лексема в контексте
    - ParseError: общая ошибка парсинга
    """
    # Позиция в символах
    pos = error.pos_in_stream if hasattr(error, "pos_in_stream") and error.pos_in_stream is not None else 0

    # Вычислить строку и колонку
    line = source[:pos].count("\n")
    line_start = source.rfind("\n", 0, pos) + 1
    col = pos - line_start

    # Диапазон: одна позиция (ошибка в точке)
    start = Position(line=line, character=col)
    end = Position(line=line, character=col + 1)

    # Сообщение: код ошибки + текст
    code = getattr(error, "code", "E001")
    if isinstance(error, (UnexpectedCharacters, UnexpectedToken)):
        msg = f"Syntax error: {error}"
        code = "E001"
    else:
        msg = str(error)

    return Diagnostic(
        range=Range(start=start, end=end),
        message=msg,
        code=code,
        source="dl",
        severity=1,  # Error
    )


def _dl_error_to_diagnostic(
    error: DLError,
    source: str,
) -> Diagnostic:
    """Преобразовать ошибку DL в Diagnostic.

    DLError может содержать позицию в args или быть без позиции.
    """
    # Попытка извлечь позицию из args
    # Формат args может быть: (message, filename, line, col) или (message,)
    args = error.args if error.args else ()

    if len(args) >= 4:
        # Есть позиция
        _, _, line, col = args[0], args[1] if len(args) > 1 else 0, args[2] if len(args) > 2 else 0, args[3] if len(args) > 3 else 0
        start = Position(line=int(line) - 1, character=int(col))
        end = Position(line=int(line) - 1, character=int(col) + 1)
    else:
        # Нет позиции — ставим в начало
        start = Position(line=0, character=0)
        end = Position(line=0, character=1)

    return Diagnostic(
        range=Range(start=start, end=end),
        message=str(error),
        code=error.code,
        source="dl",
        severity=1,  # Error
    )


def _parse_and_get_diagnostics(source: str, uri: str) -> list[Diagnostic]:
    """Распарсить источник и вернуть список Diagnostic."""
    diagnostics: list[Diagnostic] = []

    try:
        parse(source, filename=uri)
    except LarkError as e:
        logger.debug("LarkError при парсинге %s: %s", uri, e)
        diagnostics.append(_lark_error_to_diagnostic(e, source))
    except DLError as e:
        logger.debug("DLError при парсинге %s: %s", uri, e)
        diagnostics.append(_dl_error_to_diagnostic(e, source))
    except Exception as e:
        logger.exception("Неожиданная ошибка при парсинге %s: %s", uri, e)
        diagnostics.append(
            Diagnostic(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=1),
                ),
                message=f"Internal error: {e}",
                code="E000",
                source="dl",
                severity=1,
            )
        )

    return diagnostics


def _position_in_source(pos: Position, source: str) -> int:
    """Преобразовать Position в смещение в символах."""
    lines = source.split("\n")
    offset = 0
    for i in range(pos.line):
        offset += len(lines[i]) + 1  # +1 для \n
    offset += pos.character
    return offset


def _get_hover_info(source: str, pos: Position, uri: str) -> Hover | None:
    """Получить информацию для Hover.

    Пока простая реализация: показать AST-ноду в позиции.
    """
    try:
        ast = parse(source, filename=uri)

        # Попытка найти ноду в позиции
        # Для простоты: показать корневой тип AST
        kind = ast.get("kind", "unknown")
        fmt = ast.get("format")

        content = f"**DL Document**\n\nKind: `{kind}`"
        if fmt:
            content += f"\nFormat: `{fmt}`"

        return Hover(
            contents=MarkupContent(kind=MarkupKind.MARKDOWN, value=content),
            range=Range(
                start=Position(line=pos.line, character=0),
                end=Position(line=pos.line, character=len(source.split("\n")[pos.line]) if pos.line < len(source.split("\n")) else 0),
            ),
        )
    except Exception as e:
        logger.debug("Hover error: %s", e)
        return None


# ---------------------------------------------------------------------------
# Обработчики событий
# ---------------------------------------------------------------------------


@server.feature("textDocument/diagnostic")
def lsp_diagnostic(params: Any) -> list[Diagnostic]:
    """textDocument/diagnostic — парсинг файла, возврат Diagnostic."""
    uri = params.text_document.uri
    source = params.text_document.text

    logger.debug("Diagnostic запрос для %s", uri)
    return _parse_and_get_diagnostics(source, uri)


@server.feature("textDocument/didOpen")
def did_open(params: DidOpenTextDocumentParams) -> None:
    """Открытие документа — распарсить и отправить diagnostics."""
    uri = params.text_document.uri
    source = params.text_document.text

    logger.debug("Document opened: %s", uri)
    diagnostics = _parse_and_get_diagnostics(source, uri)

    server.publish_diagnostics(
        PublishDiagnosticsParams(
            uri=uri,
            diagnostics=diagnostics,
        )
    )


@server.feature("textDocument/didChange")
def did_change(params: DidChangeTextDocumentParams) -> None:
    """Изменение документа — распарсить и отправить diagnostics."""
    uri = params.text_document.uri
    # Изменения могут быть инкрементальными, но для простоты берём весь текст
    # из последнего изменения или полного содержимого (зависит от клиента)
    # Для надёжности: клиент должен прислать полный текст в sync=full

    if params.content_changes:
        # Берём последнее изменение как полный текст (если клиент шлёт full sync)
        source = params.content_changes[-1].text

        logger.debug("Document changed: %s", uri)
        diagnostics = _parse_and_get_diagnostics(source, uri)

        server.publish_diagnostics(
            PublishDiagnosticsParams(
                uri=uri,
                diagnostics=diagnostics,
            )
        )


@server.feature("textDocument/hover")
def hover(params: HoverParams) -> Hover | None:
    """textDocument/hover — показать тип/значение для ключа или переменной."""
    uri = params.text_document.uri
    position = params.position

    # Получить документ из сервера (кэш)
    doc = server.workspace.get_text_document(uri)
    source = doc.source

    logger.debug("Hover запрос для %s на позиции %s", uri, position)
    return _get_hover_info(source, position, uri)


@server.feature(
    "textDocument/completion",
    CompletionOptions(
        trigger_characters=[".", "$", "{", '"'],
        resolve_provider=False,
    ),
)
def completion(params: CompletionParams) -> CompletionList:
    """textDocument/completion — заглушка (отложено)."""
    logger.debug("Completion запрос (заглушка)")
    return CompletionList(
        is_incomplete=True,
        items=[],
    )


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------


def main() -> None:
    """Запустить LSP-сервер через stdin/stdout."""
    logger.info("Запуск dl-lsp сервера v0.1.0")
    try:
        server.start_io()
    except Exception as e:
        logger.exception("Критическая ошибка сервера: %s", e)
        raise
