#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Garde-fous du cycle de rendu wxPython sous Windows.

Ces tests restent volontairement indépendants d'un serveur d'affichage : ils
vérifient le contrat structurel du moteur de thème sans instancier wx.App.
"""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "Utils" / "UTILS_Theme.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))


def _function(name):
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("fonction absente : %s" % name)


def _calls(node, name):
    return [
        item for item in ast.walk(node)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == name
    ]


def _attributes_called(node):
    return {
        item.func.attr
        for item in ast.walk(node)
        if isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute)
    }


def test_recursive_theme_walk_ne_repeint_pas_chaque_enfant():
    walker = _function("_apply_window_tree")
    called_attributes = _attributes_called(walker)
    assert "Layout" not in called_attributes
    assert "Refresh" not in called_attributes
    assert _calls(walker, "_apply_window_tree")


def test_apply_to_window_finalise_la_surface_une_seule_fois():
    apply_function = _function("apply_to_window")
    called_attributes = _attributes_called(apply_function)
    assert "Layout" in called_attributes
    assert "Refresh" in called_attributes
    assert not _calls(apply_function, "apply_to_window")
    assert _calls(apply_function, "_apply_window_tree")


def test_show_false_ne_declenche_plus_un_rethemage_de_destruction():
    source = SOURCE.read_text(encoding="utf-8")
    assert "def _show_requested(args, kwargs):" in source
    assert "if _show_requested(args, kwargs):" in source

    installer = _function("install_auto_theming")
    themed_show = next(
        node for node in installer.body
        if isinstance(node, ast.FunctionDef) and node.name == "themed_show"
    )
    conditional = next(node for node in themed_show.body if isinstance(node, ast.If))
    assert isinstance(conditional.test, ast.Call)
    assert isinstance(conditional.test.func, ast.Name)
    assert conditional.test.func.id == "_show_requested"
