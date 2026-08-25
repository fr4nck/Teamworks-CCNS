# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _calls(path):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    ]


def _call_name(call):
    try:
        return ast.unparse(call.func)
    except Exception:
        return ""


def test_persisted_parameters_are_decoded_without_eval():
    path = "teamworks/Utils/UTILS_Parametres.py"
    names = {_call_name(call) for call in _calls(path)}
    assert "eval" not in names
    assert "ast.literal_eval" in names


def test_whitelisted_procedures_are_invoked_without_exec():
    path = "teamworks/Utils/UTILS_Procedures.py"
    names = {_call_name(call) for call in _calls(path)}
    assert "exec" not in names
    source = (ROOT / path).read_text(encoding="utf-8")
    assert "globals().get(code)" in source
    assert "callable(procedure)" in source
