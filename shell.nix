let
    pkgs = import <nixpkgs> {};
in pkgs.mkShell {
    packages = with pkgs; [
        python312
        ruff
        (poetry.override { python3 = python312; })
    ];
}