from __future__ import annotations

import ast
from pathlib import Path

from teamworks.Utils.UTILS_Duration import operation_heures_wx


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
                    namespace = {"operation_heures_wx": operation_heures_wx}
                    exec(compile(compiled, str(SCENARIO), "exec"), namespace)
                    return namespace["OperationHeures"]
    raise AssertionError(f"{class_name}.OperationHeures introuvable")


def _assert_duration_contract(class_name: str):
    operation = _operation_heures(class_name)
    assert operation(object(), "+00:00", "+00:30", "soustraction") == "-0:30"
    assert operation(object(), "+02:00", "+00:30", "soustraction") == "+1:30"
    assert operation(object(), "+00:30", "+02:00", "soustraction") == "-1:30"
    assert operation(object(), "+10:00", "+02:30", "addition") == "+12:30"
    assert operation(object(), None, None, "addition") == "+0:00"
    assert operation(object(), "+30:00", "+15:00", "addition") == "+45:00"


def test_tableau_conserve_le_signe_et_les_resultats_historiques_valides():
    _assert_duration_contract("Tableau")


def test_get_dict_colonnes_conserve_le_meme_contrat_de_duree():
    _assert_duration_contract("GetDictColonnes")


def test_operation_heures_delegue_au_metier_commun():
    source = SCENARIO.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(SCENARIO))
    methods = []
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name in {"Tableau", "GetDictColonnes"}:
            methods.extend(
                child
                for child in node.body
                if isinstance(child, ast.FunctionDef) and child.name == "OperationHeures"
            )
    assert len(methods) == 2
    for method in methods:
        calls = [
            node.func.id
            for node in ast.walk(method)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert "operation_heures_wx" in calls
