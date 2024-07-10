let
    pkgs = import <nixpkgs> {};
in pkgs.mkShell {
    packages = with pkgs; [
        python312
        (poetry.override { python3 = python312; })
    ];
}