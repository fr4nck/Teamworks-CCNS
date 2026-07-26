import ast
from pathlib import Path


SOURCE_PATH = Path("teamworks/Ctrl/CTRL_Gadget_pb_personnes.py")


def parse_source() -> ast.Module:
    return ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))


def test_gadget_no_longer_depends_on_six():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "import six" not in source
    assert "six." not in source


def test_gadget_uses_isinstance_for_text_nodes():
    tree = parse_source()
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
    ]

    assert calls


def test_gadget_declares_utf8_source():
    first_lines = SOURCE_PATH.read_text(encoding="utf-8").splitlines()[:2]

    assert any("coding: utf-8" in line for line in first_lines)
