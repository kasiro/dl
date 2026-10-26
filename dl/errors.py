"""Ошибки DL v2.1.

Каждый класс несёт код из спецификации (раздел 9) в атрибуте ``code`` и в
тексте сообщения. Имена классов повторяют раздел 9.1; ``ModuleNotFoundError``
намеренно перекрывает встроенное исключение — это ошибка DL (E002).
"""

from __future__ import annotations


class DLError(Exception):
    """Базовый класс ошибок DL."""

    code = "E000"
    name = "DLError"


class SyntaxError(DLError):  # noqa: A001 - имя из спецификации
    code = "E001"
    name = "SyntaxError"


class ModuleNotFoundError(DLError):  # noqa: A001 - имя из спецификации
    code = "E002"
    name = "ModuleNotFoundError"


class ConflictError(DLError):
    code = "E003"
    name = "ConflictError"


class CircularImportError(DLError):
    code = "E004"
    name = "CircularImportError"


class FormatNotFoundError(DLError):
    code = "E005"
    name = "FormatNotFoundError"


class ParseError(DLError):
    code = "E006"
    name = "ParseError"


class NotOverridableKey(DLError):
    code = "E007"
    name = "NotOverridableKey"


class DLContextError(DLError):
    code = "E008"
    name = "NoContext"


class UnknownParameterError(DLError):
    code = "E009"
    name = "UnknownParameter"


class MissingParameterError(DLError):
    code = "E010"
    name = "MissingParameter"


class TypeMismatchError(DLError):
    code = "E011"
    name = "TypeMismatch"


class SchemaFetchError(DLError):
    code = "E012"
    name = "SchemaFetchError"


class SchemaGenerateError(DLError):
    code = "E013"
    name = "SchemaGenerateError"


class GlobParameterizedModule(DLError):
    code = "E014"
    name = "GlobParameterizedModule"
