#!/usr/bin/env python3
"""Тонкая CLI-обёртка над ``dl.schema_gen`` (совместимость).

Использование:
    python3 tools/gen_schema.py <input.json> <output.schema>

Вся логика конвертации живёт в пакете: ``dl/schema_gen.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Запуск напрямую (python3 tools/gen_schema.py) — корень репозитория в sys.path.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dl.errors import DLError  # noqa: E402
from dl.schema_gen import SchemaConverter  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "использование: gen_schema.py <input.json> <output.schema>",
            file=sys.stderr,
        )
        return 2

    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    try:
        schema = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"E013 SchemaGenerateError: {error}", file=sys.stderr)
        return 1

    source_url = schema.get("$id") or "https://opencode.ai/config.json"

    converter = SchemaConverter(schema)
    try:
        text, class_count = converter.convert(source_url)
    except DLError as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception as error:  # noqa: BLE001 - CLI-обёртка
        print(f"E013 SchemaGenerateError: {error}", file=sys.stderr)
        return 1

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")

    print(f"записано: {dst} ({len(text.encode())} байт)", file=sys.stderr)
    print(f"классов: {class_count}", file=sys.stderr)
    if converter.notes:
        print("не сконвертировано:", file=sys.stderr)
        for note in converter.notes:
            print(f"  - {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
