# Точка входа модулей
# Импортирует все модули конфигурации
{ lib
, config
, settings
, factories
, ...
}:

{
  imports = [
    ./providers.nix
    ./mcp.nix
    ./permissions.nix
    ./agents.nix
    ./runtime.nix
  ];
}
