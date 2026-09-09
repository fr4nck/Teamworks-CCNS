from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path("teamworks/Dlg/DLG_Saisie_champs_publipostage.py")


def _load_importation():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOURCE))
    helper = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_nullable_db_text"
    )
    dialog = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Dialog"
    )
    method = next(
        node for node in dialog.body
        if isinstance(node, ast.FunctionDef) and node.name == "Importation"
    )
    module = ast.Module(body=[helper, method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["Importation"]


def test_sql_null_text_fields_are_empty_before_textctrl_setvalue():
    calls = []

    class FakeTextCtrl:
        def SetValue(self, value):
            if not isinstance(value, str):
                raise TypeError("TextEntry.SetValue(): argument 1 has unexpected type")
            calls.append(value)

    class FakeDB:
        def ExecuterReq(self, req):
            self.req = req

        def ResultatReq(self):
            return [(7, "contrat", None, None, None)]

        def Close(self):
            pass

    class FakeGestionDB:
        @staticmethod
        def DB():
            return FakeDB()

    class FakeDialog:
        IDchamp = 7
        text_nom = FakeTextCtrl()
        text_defaut = FakeTextCtrl()
        text_motCle = FakeTextCtrl()
        ancienMotcle = "sentinel"

    importation = _load_importation()
    importation.__globals__["GestionDB"] = FakeGestionDB
    dialog = FakeDialog()
    importation(dialog)

    assert calls == ["", "", ""]
    assert dialog.ancienMotcle == ""


def test_nullable_text_helper_does_not_hide_unexpected_non_text_types():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOURCE))
    helper = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_nullable_db_text"
    )
    module = ast.Module(body=[helper], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    normalize = namespace["_nullable_db_text"]

    assert normalize(None) == ""
    assert normalize("texte") == "texte"
    assert normalize(123) == 123
