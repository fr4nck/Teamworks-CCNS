# -*- coding: utf-8 -*-
"""Gardes statiques CRH-20 des actions de protection sociale wxPython."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_protection_sociale.py"
RUNTIME = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_protection_sociale_runtime.py"
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Protection_sociale_action.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path), filename=str(path))


def _find_method(tree, class_name, method_name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


def test_page_expose_uniquement_les_trois_intentions_controlees():
    source = _source(PAGE)

    assert "self.bouton_ajouter" in source
    assert "self.bouton_cloturer" in source
    assert "self.bouton_nouvelle_periode" in source
    assert "def OnAjouter" in source
    assert "def OnCloturer" in source
    assert "def OnNouvellePeriode" in source

    for forbidden in (
        "GestionDB",
        "Repository",
        "DELETE FROM",
        "UPDATE tw_hr_",
        "requests.",
        "webbrowser",
    ):
        assert forbidden not in source


def test_actions_runtime_reste_importe_uniquement_au_premier_clic():
    tree = _tree(RUNTIME)

    top_level_imports = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            top_level_imports.append(node.module or "")
    assert "application.bootstrap.employee_protection_actions_factory" not in top_level_imports

    method = _find_method(tree, "Panel", "_get_actions_runtime")
    local_imports = [
        node.module
        for node in ast.walk(method)
        if isinstance(node, ast.ImportFrom)
    ]
    assert "application.bootstrap.employee_protection_actions_factory" in local_imports


def test_dialogue_ne_connait_ni_structure_ni_persistance():
    source = _source(DIALOG)

    for forbidden in (
        "GestionDB",
        "sqlite3",
        "Repository",
        "structure_ref",
        "record_id",
        "requests.",
        "webbrowser",
        "SecretStore",
        "password",
        "token",
    ):
        assert forbidden not in source

    assert "EmployeeProtectionCreateRequest" in source
    assert 'source="teamworks-ui"' in source


def test_runtime_n_expose_aucune_edition_ou_suppression_libre():
    source = _source(RUNTIME)

    assert "runtime.register(" in source
    assert "runtime.end(" in source
    assert "runtime.supersede(" in source
    for forbidden in (
        "runtime.delete(",
        "runtime.remove(",
        "runtime.edit(",
        "runtime.update(",
    ):
        assert forbidden not in source


def test_echec_action_ne_rend_pas_la_fiche_inutilisable():
    source = _source(RUNTIME)

    assert "except Exception as exc:" in source
    assert "_show_action_error(" in source
    assert "self.SetUnavailable(" in source
    assert "La fiche salarié reste utilisable." in source
