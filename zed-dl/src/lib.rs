use zed_extension_api as zed;
use zed_extension_api::{Command, Extension, LanguageServerId, Worktree};

struct DlExtension;

impl Extension for DlExtension {
    fn new() -> Self {
        DlExtension
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        _worktree: &Worktree,
    ) -> Result<Command, String> {
        // Zed запускает процесс language server с cwd = корень worktree,
        // поэтому `uv run` находит pyproject.toml проекта DL и entry point dl-lsp.
        Ok(Command {
            command: "uv".to_string(),
            args: vec!["run".to_string(), "dl-lsp".to_string()],
            env: vec![],
        })
    }
}

zed::register_extension!(DlExtension);
