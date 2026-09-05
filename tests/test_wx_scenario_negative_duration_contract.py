from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "teamworks" / "Dlg" / "DLG_Scenario.py"


def _operation_heures(class_name: str):
    source = SCENARIO.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(SCENARIO))
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == "OperationHeures":
                    method = ast.FunctionDef(
                        name=child.name,
                        args=child.args,
                        body=child.body,
                        decorator_list=[],
                        returns=child.returns,
                        type_comment=child.type_comment,
                    )
                    compiled = ast.Module(body=[method], type_ignores=[])
                    ast.fix_missing_locations(compiled)
                    namespace = {}
                    exec(compile(compiled, str(SCENARIO), "exec"), namespace)
                    return namespace["OperationHeures"]
    raise AssertionError(f"{class_name}.OperationHeures introuvable")


def _assert_duration_contract(class_name: str):
    operation = _operation_heures(class_name)
    assert operation(object(), "+00:00", "+00:30", "soustraction") == "-0:30"
    assert operation(object(), "+02:00", "+00:30", "soustraction") == "+1:30"
    assert operation(object(), "+00:30", "+02:00", "soustraction") == "-1:30"
    assert operation(object(), "+10:00", "+02:30", "addition") == "+12:30"


def test_tableau_conserve_le_signe_et_les_resultats_historiques_valides():
    _assert_duration_contract("Tableau")


def test_get_dict_colonnes_conserve_le_meme_contrat_de_duree():
    _assert_duration_contract("GetDictColonnes")
