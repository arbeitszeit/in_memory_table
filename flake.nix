{
  description = "A very basic flake";

  outputs = { self, nixpkgs }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
      python = pkgs.python3.withPackages
        (p: [ p.black p.isort p.flake8 p.mypy p.pytest p.setuptools ]);
    in {
      packages.x86_64-linux.default = python.pkgs.callPackage ./package.nix { };
      devShells.x86_64-linux.default = pkgs.mkShell {
        packages =
          [ python pkgs.cargo pkgs.rustc pkgs.rustfmt pkgs.clippy pkgs.nixfmt ];
      };
    };
}
