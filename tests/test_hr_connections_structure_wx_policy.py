# -*- coding: utf-8 -*-
"""Gardes statiques du raccordement CRH-10B au paramétrage Teamworks."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Teamworks.py"
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Organismes_connexions_rh.py"
FACTORY = ROOT / "application" / "bootstrap" / "hr_connections_structure_factory.py"
REQUEST = ROOT / "application" / "services" / "hr_connections" / "structure_profile_actions.py"


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


def _imported_modules(path):
    modules = []
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


def test_shell_adds_connections_menu_without_modifying_core_menu_source():
    source = _source(SHELL)

    assert 'self.dictInfosMenu["menu_parametrage"]["ctrl"]' in source
    assert 'self.dictInfosMenu["connexions_rh"]' in source
    assert "Organismes && connexions RH" in source
    assert "class MyFrame(_BaseMyFrame):" in source
    assert "CORE.MyFrame = MyFrame" in source


def test_connections_dialog_is_imported_only_from_explicit_menu_handler():
    tree = _tree(SHELL)
    handler = _find_method(tree, "MyFrame", "On_param_connexions_rh")

    lazy_imports = [
        alias.name
        for node in ast.walk(handler)
        if isinstance(node, ast.ImportFrom) and node.module == "Dlg"
        for alias in node.names
    ]
    assert "DLG_Organismes_connexions_rh" in lazy_imports

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "Dlg":
            assert all(alias.name != "DLG_Organismes_connexions_rh" for alias in node.names)


def test_dialogue_ne_choisit_ni_persistance_ni_transport_externe():
    imported = _imported_modules(DIALOG)
    for forbidden in (
        "GestionDB",
        "sqlite3",
        "infrastructure.persistence",
        "requests",
        "urllib",
        "webbrowser",
        "socket",
        "subprocess",
    ):
        assert all(
            module != forbidden and not module.startswith(forbidden + ".")
            for module in imported
        )

    source = _source(DIALOG)
    assert "SecretStore" not in source
    assert "CredentialBinding" not in source
    assert "wx.TE_PASSWORD" not in source


def test_structure_screen_does_not_offer_profile_deletion_or_fake_api_toggle():
    source = _source(DIALOG)

    assert "delete_profile" not in source
    assert "remove_profile" not in source
    assert "OnDelete" not in source
    assert "API, dépôt, synchronisation" in source
    assert "Ajouter" in source
    assert "Modifier" in source


def test_request_does_not_accept_free_form_connector_capabilities():
    tree = _tree(REQUEST)
    request_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "StructureConnectionProfileRequest"
    )
    annotated_fields = {
        node.target.id
        for node in request_class.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }

    assert "capabilities" not in annotated_fields
    assert "structure_ref" not in annotated_fields


def test_structure_runtime_factory_remains_ui_agnostic():
    source = _source(FACTORY)

    for token in (
        "import wx",
        "from Dlg",
        "from Ctrl",
        "webbrowser",
        "requests",
    ):
        assert token not in source
