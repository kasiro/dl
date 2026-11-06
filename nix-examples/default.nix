# Точка входа сборки конфигурации
# Собирает все модули и возвращает итоговый атрибут
# Порядок ключей соответствует opencode.json
let
  lib = import <nixpkgs> { };

  # Параметры (аналог settings.dl)
  settings = import ./settings.nix { inherit lib; };

  # Фабрики
  factories = {
    provider = import ./factories/provider.nix;
    server = import ./factories/server.nix;
    makeoptions = import ./factories/makeoptions.nix;
  };

  # Контекст для модулей
  modulesContext = {
    inherit lib settings factories;
  };

  # Импортируем модули
  providersConfig = import ./modules/providers.nix modulesContext;
  mcpConfig = import ./modules/mcp.nix modulesContext;
  permissionsConfig = import ./modules/permissions.nix modulesContext;
  agentsConfig = import ./modules/agents.nix modulesContext;
  runtimeConfig = import ./modules/runtime.nix modulesContext;

  # Явный порядок ключей (соответствует opencode.json)
  # Примечание: Nix attrsets всегда сортируются по ключам.
  # Для сохранения порядка используйте builtins.toJSON на результате.
  config = builtins.listToAttrs [
    { name = "$schema"; value = "https://opencode.ai/config.json"; }
    { name = "provider"; value = providersConfig.providers; }
    { name = "default_agent"; value = agentsConfig.agents.default; }
    { name = "instructions"; value = { }; }
    { name = "share"; value = { }; }
    { name = "permission"; value = permissionsConfig.permission; }
    { name = "mcp"; value = mcpConfig.mcp; }
    { name = "agent"; value = agentsConfig.agent; }
    { name = "lsp"; value = runtimeConfig.lsp; }
    { name = "plugin"; value = runtimeConfig.plugin; }
    { name = "compaction"; value = runtimeConfig.compaction; }
    { name = "tool_output"; value = runtimeConfig.tool_output; }
    { name = "experimental"; value = runtimeConfig.experimental; }
  ];

in
config
