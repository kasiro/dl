# DL Language Support для Zed

Расширение для подсветки синтаксиса языка конфигурации DL.

## Структура

```
zed-dl/
├── extension.toml              # Манифест расширения (TOML)
├── languages/dl/
│   ├── config.toml             # Конфигурация языка
│   ├── highlights.scm          # Подсветка синтаксиса
│   ├── brackets.scm            # Парные скобки
│   ├── indents.scm             # Отступы
│   └── outline.scm             # Структура документа
└── tree-sitter-dl/
    ├── grammar.js              # Tree-sitter грамматика
    ├── package.json            # Зависимости
    ├── src/
    │   ├── parser.c            # Сгенерированный парсер
    │   └── node-types.json     # Типы узлов
    └── bindings/
```

## Установка

1. Откройте Zed
2. Откройте палитру команд: `Ctrl+Shift+P` (Linux/Windows) или `Cmd+Shift+P` (macOS)
3. Введите: `zed: install dev extension`
4. Выберите папку `zed-dl/` (или файл `extension.toml`) из этой папки
5. Расширение будет установлено в режиме разработки

## Проверка

Откройте любой `.dl` файл из `examples/` — должна работать подсветка синтаксиса.

## Требования

- Zed Editor (последняя версия)
- Node.js (для генерации парсера, если потребуется)

## Разработка

### Локальная грамматика

Грамматика загружается из локального git-репозитория через `file://` URL:

```toml
[grammars.dl]
repository = "file:///home/kasiro/Документы/dl/zed-dl/tree-sitter-dl"
rev = "03b6cb0c65b21036c2827160947607094a48f961"
```

**Важно:** `rev` должен быть хешем коммита (не веткой). После изменений в грамматике:

```bash
cd tree-sitter-dl
git add .
git commit -m "Описание изменений"
# Обновить rev в extension.toml на новый хеш
```

### Перегенерация парсера

После изменений в `grammar.js`:

```bash
cd tree-sitter-dl
npx tree-sitter generate
git add .
git commit -m "Регенерация парсера"
```

### Проверка парсера

```bash
cd tree-sitter-dl
npx tree-sitter parse ../../examples/configuration.dl
```

## Статус

- ✅ Grammar.js создан на основе grammar.lark
- ✅ Парсер сгенерирован без ошибок
- ✅ Тестовый parse `configuration.dl` — успешно
- ⚠️ Zed не установлен в системе (сэр установит самостоятельно)
