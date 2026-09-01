# -*- coding: utf-8 -*-
"""Gardes statiques du raccordement Protection sociale à la fiche salarié.

Ces tests n'importent volontairement ni wxPython ni le runtime Teamworks : ils
verrouillent la frontière de composition et restent exécutables dans le socle CI.
"""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAZY = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_lazy.py"
RUNTIME = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_protection_sociale_runtime.py"
PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_protection_sociale.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path), filename=str(path))


def _find_method(tree, class_name, method_name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


def test_protection_sociale_reste_le_dernier_onglet_lazy():
    source = _source(LAZY)
    recrutement = source.index('(\"pageCandidatures\", _(u\"Recrutement\")')
    protection = source.index('(\"pageProtectionSociale\", _(u\"Protection sociale\")')

    assert protection > recrutement


def test_runtime_rh_n_est_pas_importe_au_chargement_de_la_fiche():
    tree = _tree(LAZY)

    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(alias.name != "CTRL_Page_protection_sociale_runtime" for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module == "Ctrl":
            assert all(alias.name != "CTRL_Page_protection_sociale_runtime" for alias in node.names)


def test_factory_charge_le_runtime_uniquement_a_l_ouverture_de_l_onglet():
    tree = _tree(LAZY)
    factory = _find_method(tree, "LazyNotebook", "_create_protection_sociale_page")

    imports = [
        alias.name
        for node in ast.walk(factory)
        if isinstance(node, ast.ImportFrom) and node.module == "Ctrl"
        for alias in node.names
    ]
    assert "CTRL_Page_protection_sociale_runtime" in imports

    source = _source(LAZY)
    assert '("pageProtectionSociale", _(u"Protection sociale"), self.img8,\n             self._create_protection_sociale_page)' in source


def test_runtime_preserve_la_fiche_si_la_synthese_rh_echoue():
    source = _source(RUNTIME)
    tree = _tree(RUNTIME)
    init = _find_method(tree, "Panel", "__init__")

    handlers = [handler for node in ast.walk(init) if isinstance(node, ast.Try) for handler in node.handlers]
    assert any(
        isinstance(handler.type, ast.Name) and handler.type.id == "Exception"
        for handler in handlers
        if handler.type is not None
    )
    assert "summary = build_employee_protection_summary(IDpersonne)" in source
    assert "load_error = error" in source
    assert "load_error=load_error" in source


def test_raccordement_ui_ne_reintroduit_pas_un_store_sqlite_local():
    for path in (LAZY, RUNTIME, PAGE):
        source = _source(path).lower()
        assert "import sqlite3" not in source
        assert "sqlite3.connect" not in source
