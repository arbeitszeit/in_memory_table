{ buildPythonPackage, setuptools, mypy, pytestCheckHook }:
buildPythonPackage {
  name = "in_memory_table";
  version = "0.1";
  src = ./.;
  format = "pyproject";
  buildInputs = [ setuptools mypy pytestCheckHook ];
}
