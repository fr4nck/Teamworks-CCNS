import ast
from pathlib import Path


SOURCE_PATH = Path("teamworks/Utils/UTILS_Parametres.py")
REQUIRED_FUNCTIONS = {
    "ParametresCategorie",
    "Parametres",
    "TestParametre",
}


def parse_source() -> ast.Module:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    return ast.parse(source)


def test_public_parameter_api_is_preserved():
    tree = parse_source()
    functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert REQUIRED_FUNCTIONS <= functions


def test_parameter_module_no_longer_depends_on_six():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "import six" not in source
    assert "six." not in source


def test_parameter_module_declares_utf8_source():
    first_lines = SOURCE_PATH.read_text(encoding="utf-8").splitlines()[:2]

    assert any("coding: utf-8" in line for line in first_lines)
