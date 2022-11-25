{ buildPythonPackage, setuptools, mypy, pytestCheckHook }:
buildPythonPackage {
  name = "in_memory_table";
  version = "1.0.0";
  src = ./.;
  format = "pyproject";
  buildInputs = [ setuptools mypy pytestCheckHook ];
}
