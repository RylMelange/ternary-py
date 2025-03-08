let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (p: with p; [
      pygame
    ]))
  ];
  shellHook = ''
    alias terun='python main.py'
  '';
}

