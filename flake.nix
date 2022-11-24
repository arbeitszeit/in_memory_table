{
  description = "Python package for dealing with indexed data in memory";

  inputs = { flake-utils.url = "github:numtide/flake-utils"; };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3.withPackages
          (p: [ p.black p.isort p.flake8 p.mypy p.pytest p.setuptools ]);
      in {
        packages.default = python.pkgs.callPackage ./package.nix { };
        devShells.default = pkgs.mkShell { packages = [ python pkgs.nixfmt ]; };
      });
}
