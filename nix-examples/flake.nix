# Точка входа flake
# Аналог flake.dl
{
  description = "DL Nix examples — модульная конфигурация OpenCode";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:

    let
      lib = nixpkgs.lib;

      # Импортируем основную конфигурацию
      config = import ./default.nix;

    in
    {
      # Формат вывода: JSON (аналог opencode.json из DL)
      packages.x86_64-linux.default = nixpkgs.runCommand "opencode-config.json"
        {
          nativeBuildInputs = [ nixpkgs.jq ];
        }
        ''
          cat <<EOF > $out
          ${builtins.toJSON config}
          EOF
        '';

      # Dev shell для тестирования
      devShells.x86_64-linux.default = nixpkgs.mkShell {
        packages = [
          nixpkgs.jq
          nixpkgs.nix
        ];
        shellHook = ''
          echo "DL Nix examples loaded"
          echo "Config: nix eval .#packages.x86_64-linux.default"
        '';
      };
    };
}
