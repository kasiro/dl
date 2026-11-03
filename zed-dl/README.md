# DL Language Support для Zed

Расширение для подсветки синтаксиса и LSP-поддержки языка конфигурации DL.

## Структура

```
zed-dl/
├── extension.toml              # Манифест расширения (TOML)
├── Cargo.toml                  # Rust-крейт расширения (wasm)
├── src/
│   └── lib.rs                  # Запуск language server (uv run dl-lsp)
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

## Language Server (LSP)

Расширение подключает LSP-сервер проекта DL (`dl_lsp/`, entry point `dl-lsp`): диагностики при открытии/изменении файла и hover с типом/значением ключа или переменной.

### Как это работает

В актуальном формате Zed секция `language_servers` в `extension.toml` задаёт только метаданные — команду запуска в манифесте указать нельзя:

```toml
[language_servers.dl-lsp]
name = "DL LSP"
languages = ["DL"]   # имя из languages/dl/config.toml
```

Команда запускается из Rust-части расширения (`src/lib.rs`, метод `language_server_command`):

```rust
Ok(Command {
    command: "uv".to_string(),
    args: vec!["run".to_string(), "dl-lsp".to_string()],
    env: vec![],
})
```

Zed сам запускает процесс с `cwd` = корень worktree, поэтому `uv run` находит `pyproject.toml` проекта DL и entry point `dl-lsp`. **LSP работает, когда открытый `.dl`-файл лежит в worktree с корнем в `/home/kasiro/Документы/dl`** (или в подкаталоге этого проекта).

### Требования для LSP

- `uv` в PATH (LSP-сервер запускается через `uv run dl-lsp`)
- Проект DL с собранным окружением: `uv sync` в корне `/home/kasiro/Документы/dl`
- Rust с target `wasm32-wasip2` (Zed компилирует Rust-часть расширения при установке dev extension):

```bash
rustup target add wasm32-wasip2
```

> **Примечание (2026-10-29):** Rust-часть (`src/lib.rs`) проверена host-сборкой (cargo build — ок), но wasm-сборка пока не работает: toolchain `stable` в `~/.rustup` установлена нестандартно (нет manifest-файла, `rustup target add` падает с «Missing manifest», линковка сломана из-за несовпадения nix store-путей). Для сборки dev extension нужно переустановить toolchain:
>
> ```bash
> rustup toolchain install stable
> rustup default stable
> rustup target add wasm32-wasip2
> ```

### Диагностика

Если LSP не стартует: `zed: open log` — искать ошибки запуска `dl-lsp`. Проверить вручную:

```bash
cd /home/kasiro/Документы/dl
uv run dl-lsp   # сервер ждёт LSP-сообщений на stdin/stdout
```

## Требования

- Zed Editor (последняя версия)
- Node.js (для генерации парсера, если потребуется)
- `uv` + собранное окружение проекта DL (для LSP)
- Rust + target `wasm32-wasip2` (для сборки Rust-части расширения)

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
- ✅ LSP-сервер подключён (`uv run dl-lsp`, cwd = корень worktree)
- ⚠️ Zed не установлен в системе (сэр установит самостоятельно)
