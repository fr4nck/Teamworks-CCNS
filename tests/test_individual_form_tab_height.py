# -*- coding: utf-8 -*-
"""Hauteur des onglets de la fiche individuelle (wx.Notebook natif sous MSW).

wxMSW ne calcule la hauteur des onglets qu'à leur création, ou à un changement
de police, avec le dernier padding reçu. Le padding appliqué par le thème à
l'affichage laissait donc des onglets de 20 px : la mesure réelle est faite par
le smoke Windows ``smoke_secondary_person_dialog.py``.
"""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAZY = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_lazy.py"
PERSON_SMOKE = ROOT / "tools" / "smoke_secondary_person_dialog.py"


def _lazy_notebook():
    tree = ast.parse(LAZY.read_text(encoding="utf-8"))
    return next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LazyNotebook"
    )


def _method(cls, name):
    return next(
        node for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _called_lines(function, attribute):
    return [
        node.lineno for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attribute
    ]


def test_tab_padding_is_set_before_the_first_tab_exists():
    init = _method(_lazy_notebook(), "__init__")
    padding_lines = _called_lines(init, "SetPadding")
    add_page_lines = _called_lines(init, "AddPage")
    assert padding_lines, "le padding des onglets doit être fixé à la construction"
    assert add_page_lines
    assert min(padding_lines) < min(add_page_lines)


def test_theme_padding_cannot_lower_the_tab_height():
    source = LAZY.read_text(encoding="utf-8")
    set_padding = _method(_lazy_notebook(), "SetPadding")
    body = ast.get_source_segment(source, set_padding)
    assert "max(padding.height, minimum)" in body
    assert "PADDING_VERTICAL_ONGLETS = 12" in source
    assert "self.FromDIP(PADDING_VERTICAL_ONGLETS)" in source


def test_windows_smoke_measures_the_native_tab_height():
    smoke = PERSON_SMOKE.read_text(encoding="utf-8")
    assert "TCM_GETITEMRECT" in smoke
    assert "TEAMWORKS_SMOKE_PERSON_TAB_METRICS" in smoke
