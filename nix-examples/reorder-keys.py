#!/usr/bin/env python3
"""
Переупорядочивает ключи JSON в порядке как в opencode.json.
Читает из stdin, выводит в stdout.

Порядок ключей верхнего уровня:
1. $schema
2. provider
3. default_agent
4. instructions
5. share
6. permission
7. mcp
8. agent
9. lsp
10. plugin
11. compaction
12. tool_output
13. experimental

Остальные ключи добавляются в конце в исходном порядке.
"""

import json
import sys
from collections import OrderedDict

# Порядок ключей верхнего уровня
KEY_ORDER = [
    "$schema",
    "provider",
    "default_agent",
    "instructions",
    "share",
    "permission",
    "mcp",
    "agent",
    "lsp",
    "plugin",
    "compaction",
    "tool_output",
    "experimental",
]

# Порядок ключей внутри config (для совместимости с opencode.json)
CONFIG_KEY_ORDER = [
    "permission",
    "agent",
    "agents",
    "lsp",
    "plugin",
    "compaction",
    "tool_output",
    "experimental",
]


def reorder_dict(data, key_order):
    """Переупорядочивает ключи словаря согласно заданному порядку."""
    if not isinstance(data, dict):
        return data

    result = OrderedDict()

    # Сначала ключи из порядка
    for key in key_order:
        if key in data:
            result[key] = reorder_value(data[key])

    # Затем остальные ключи в исходном порядке
    for key in data:
        if key not in result:
            result[key] = reorder_value(data[key])

    return result


def reorder_value(value):
    """Рекурсивно обрабатывает значение."""
    if isinstance(value, dict):
        # Для вложенных объектов используем рекурсию без специального порядка
        return reorder_dict(value, [])
    elif isinstance(value, list):
        return [reorder_value(item) for item in value]
    else:
        return value


def reorder_config(data):
    """Специальная обработка для config (внутри config свой порядок)."""
    if not isinstance(data, dict):
        return data

    result = OrderedDict()

    # Сначала ключи из порядка config
    for key in CONFIG_KEY_ORDER:
        if key in data:
            result[key] = reorder_value(data[key])

    # Затем остальные ключи в исходном порядке
    for key in data:
        if key not in result:
            result[key] = reorder_value(data[key])

    return result


def main():
    # Чтение JSON из stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("Error: Input must be a JSON object", file=sys.stderr)
        sys.exit(1)

    # Переупорядочивание ключей верхнего уровня
    result = OrderedDict()

    # Сначала ключи из основного порядка
    for key in KEY_ORDER:
        if key in data:
            value = data[key]
            # Особая обработка для config
            if key == "config" and isinstance(value, dict):
                result[key] = reorder_config(value)
            else:
                result[key] = reorder_value(value)

    # Затем остальные ключи в исходном порядке
    for key in data:
        if key not in result:
            value = data[key]
            # Особая обработка для config
            if key == "config" and isinstance(value, dict):
                result[key] = reorder_config(value)
            else:
                result[key] = reorder_value(value)

    # Вывод JSON с отступом 2 пробела
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
