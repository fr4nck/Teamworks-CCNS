# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def _function(path, name, class_name=None):
    text = _source(path)
    tree = ast.parse(text)
    nodes = tree.body
    if class_name is not None:
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
        nodes = cls.body
    func = next(node for node in nodes if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)
    lines = text.splitlines()
    return "\n".join(lines[func.lineno - 1:func.end_lineno])


def test_dpae_due_ignores_unused_legacy_contract_fields():
    body = _function("teamworks/Dlg/DLG_Edition_DUE.py", "Import_Donnees", "Dialog")
    assert "SELECT IDpersonne, IDtype, date_debut, date_fin, essai" in body
    assert "FROM contrats_class" not in body
    assert "FROM valeurs_point" not in body
    assert "if not contrats:" in body


def test_dpae_due_guards_failed_database_openings():
    import_body = _function("teamworks/Dlg/DLG_Edition_DUE.py", "Import_Donnees", "Dialog")
    edit_body = _function("teamworks/Dlg/DLG_Edition_DUE.py", "OnCellChange", "Grid")
    due_body = _function("teamworks/Ctrl/CTRL_Page_contrats_core.py", "OnBoutonDue", "Panel_Contrats")
    validation_body = _function("teamworks/Ctrl/CTRL_Creation_contrat_p6.py", "Validation", "Page")
    for body in (import_body, edit_body, due_body, validation_body):
        assert "_database_ready(DB)" in body


def test_contract_validation_checks_db_before_schema_and_cursor_paths():
    body = _function("teamworks/Ctrl/CTRL_Creation_contrat_p6.py", "Validation", "Page")
    assert body.index("_database_ready(DB)") < body.index("EnsureContractEngineColumns(DB)")
    assert "Le contrat n'a pas été enregistré" in body


def test_due_status_changes_ui_only_after_database_commit_block():
    body = _function("teamworks/Ctrl/CTRL_Page_contrats_core.py", "OnBoutonDue", "Panel_Contrats")
    assert body.index("DB.Commit()") < body.index("SetItem(index, 5, etatDue)")
    assert "rollback" in body
