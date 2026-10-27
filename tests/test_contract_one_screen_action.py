# -*- coding: utf-8 -*-
"""Comportement du bouton Valider sans wx ni base de données."""
import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks/Dlg/DLG_Creation_contrat.py"


def _handler():
    source = DIALOG.read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
               and node.name == "Dialog")
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                  and node.name == "Onbouton_suite")
    namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[method], type_ignores=[],
    )), str(DIALOG), "exec"), namespace)
    return namespace["Onbouton_suite"]


class _Dialog:
    def __init__(self, form_valid=True, database_valid=True):
        self._enregistrement_en_cours = False
        self.events = []
        self.form_valid = form_valid
        self.database_valid = database_valid
        self.page6 = SimpleNamespace(Validation=self._save)

    def ValidationPages(self):
        self.events.append("business")
        return self.form_valid

    def _save(self):
        self.events.append("transaction")
        return self.database_valid

    def Terminer(self):
        self.events.append("close")


def test_valid_contract_is_saved_before_closing():
    dialog = _Dialog()
    _handler()(dialog, None)
    assert dialog.events == ["business", "transaction", "close"]
    assert dialog._enregistrement_en_cours is False


def test_invalid_contract_never_reaches_database_write():
    dialog = _Dialog(form_valid=False)
    _handler()(dialog, None)
    assert dialog.events == ["business"]
    assert dialog._enregistrement_en_cours is False


def test_failed_database_write_keeps_dialog_open():
    dialog = _Dialog(database_valid=False)
    _handler()(dialog, None)
    assert dialog.events == ["business", "transaction"]
    assert dialog._enregistrement_en_cours is False


def test_double_click_guard_prevents_reentry():
    dialog = _Dialog()
    dialog._enregistrement_en_cours = True
    _handler()(dialog, None)
    assert dialog.events == []
