"""Garde-fou sans affichage pour les données des nœuds HyperTreeList."""

import ast
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "teamworks" / "Ctrl" / "CTRL_Questionnaire.py"


def test_hypertreelist_questionnaire_uses_setpydata():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    ctrl = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CTRL"
        and any(
            isinstance(base, ast.Attribute)
            and isinstance(base.value, ast.Name)
            and base.value.id == "HTL"
            and base.attr == "HyperTreeList"
            for base in node.bases
        )
    )
    updates = [
        node for node in ast.walk(ctrl)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and node.func.attr in ("SetItemData", "SetPyData")
    ]
    assert len(updates) == 2, "Les nœuds catégorie/question doivent conserver leurs données"
    assert all(node.func.attr == "SetPyData" for node in updates)
    assert {
        (ast.unparse(node.args[0]), ast.unparse(node.args[1])) for node in updates
    } == {
        ("brancheCategorie", "IDcategorie"),
        ("brancheQuestion", "track.IDquestion"),
    }
