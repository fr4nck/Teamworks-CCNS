from __future__ import annotations

import ast
from pathlib import Path

import pytest


DIALOG_FILES = (
    Path("teamworks/Dlg/DLG_Saisie_candidat_core.py"),
    Path("teamworks/Dlg/DLG_Saisie_candidature_core.py"),
    Path("teamworks/Dlg/DLG_Saisie_emploi_core.py"),
    Path("teamworks/Dlg/DLG_Statistiques.py"),
)


def _dialog(path: Path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Dialog")


def _attr(node, owner, name):
    return isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == owner and node.attr == name


def _has_root_sizer_contract(function):
    nodes = list(ast.walk(function))
    has_box = any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "sizer_dialog" for target in node.targets)
        and isinstance(node.value, ast.Call)
        and _attr(node.value.func, "wx", "BoxSizer")
        and len(node.value.args) == 1
        and _attr(node.value.args[0], "wx", "VERTICAL")
        for node in nodes
    )
    has_add = any(
        isinstance(node, ast.Call)
        and _attr(node.func, "sizer_dialog", "Add")
        and len(node.args) >= 3
        and _attr(node.args[0], "self", "panel")
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == 1
        and _attr(node.args[2], "wx", "EXPAND")
        for node in nodes
    )
    has_set = any(
        isinstance(node, ast.Call)
        and _attr(node.func, "self", "SetSizer")
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "sizer_dialog"
        for node in nodes
    )
    return has_box and has_add and has_set


@pytest.mark.parametrize("path", DIALOG_FILES)
def test_dialog_root_panel_is_managed_by_expanding_sizer(path):
    dialog = _dialog(path)
    methods = [node for node in dialog.body if isinstance(node, ast.FunctionDef)]
    assert any(_has_root_sizer_contract(method) for method in methods)
