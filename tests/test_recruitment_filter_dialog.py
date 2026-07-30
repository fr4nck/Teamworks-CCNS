from __future__ import annotations

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Dlg" / "DLG_Filtre_recrutement.py"


def _load_choice_resolver():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TARGET))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "ResoudreListeChoix"
    )
    module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(TARGET), "exec"), namespace)
    return source, namespace, namespace["ResoudreListeChoix"]


def test_recruitment_choice_lists_do_not_depend_on_exec_locals():
    source, namespace, resolver = _load_choice_resolver()
    expected = [(1, "Animation"), (2, "Sport")]
    namespace["GetListeChoix_test"] = lambda: expected

    assert resolver("test") == expected
    assert 'exec("liste = GetListeChoix_' not in source


def test_unknown_recruitment_choice_list_is_rejected_explicitly():
    _, _, resolver = _load_choice_resolver()

    with pytest.raises(ValueError, match="Liste de choix inconnue"):
        resolver("absente")
