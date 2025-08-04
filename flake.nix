{
  description = "Python dev shell with pyrefly and ruff";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { nixpkgs }:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in
    {
      devShells.default = pkgs.mkShell {
        buildInputs = [
          pkgs.python313
          pkgs.ruff
          pkgs.pyrefly
          pkgs.uv
        ];
      };
    };
}
