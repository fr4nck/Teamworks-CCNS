import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path("teamworks/Dlg/DLG_Saisie_champs_publipostage.py")


@pytest.mark.parametrize("values", [
    (None, None, None),
    ("Nom", "CLE", "Valeur"),
    ("", "CLE", None),
])
def test_importation_preserves_text_and_normalizes_sql_null(values):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    dialog_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Dialog"
    )
    method = next(
        node for node in dialog_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "Importation"
    )
    module = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(module)

    class TextControl:
        def SetValue(self, value):
            assert isinstance(value, str)
            self.value = value

    class Database:
        def ExecuterReq(self, query):
            pass

        def ResultatReq(self):
            return [(7, "contrat", *values)]

        def Close(self):
            pass

    namespace = {"GestionDB": SimpleNamespace(DB=Database)}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    dialog = SimpleNamespace(
        IDchamp=7,
        text_nom=TextControl(),
        text_defaut=TextControl(),
        text_motCle=TextControl(),
        ancienMotcle="sentinel",
    )
    namespace["Importation"](dialog)
    expected = ["" if value is None else value for value in values]
    assert dialog.text_nom.value == expected[0]
    assert dialog.text_motCle.value == expected[1]
    assert dialog.text_defaut.value == expected[2]
    assert dialog.ancienMotcle == expected[1]
