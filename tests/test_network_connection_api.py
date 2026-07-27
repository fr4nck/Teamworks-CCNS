import ast
from pathlib import Path


SOURCE_PATH = Path("teamworks/Dlg/DLG_Saisie_param_reseau.py")


def parse_source() -> ast.Module:
    return ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))


def test_testconnexion_keeps_none_as_default():
    tree = parse_source()
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "TestConnexion"
    )

    assert len(function.args.defaults) == 1
    assert isinstance(function.args.defaults[0], ast.Constant)
    assert function.args.defaults[0].value is None


def test_testconnexion_initializes_a_fresh_mapping():
    tree = parse_source()
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "TestConnexion"
    )

    assignments = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
    ]

    assert any(
        any(isinstance(target, ast.Name) and target.id == "dictValeurs" for target in assignment.targets)
        and isinstance(assignment.value, ast.Dict)
        for assignment in assignments
    )
