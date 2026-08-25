from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Utils" / "UTILS_Sauvegarde.py"


def _sauvegarde_function():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TARGET))
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "Sauvegarde")


def test_destination_copy_failure_cannot_be_reported_as_success():
    source = TARGET.read_text(encoding="utf-8")
    assert "except OSError as err:" in source
    assert "Echec de la copie de sauvegarde" in source
    assert "La sauvegarde n'a pas pu être copiée" in source

    function = _sauvegarde_function()
    handlers = [node for node in ast.walk(function) if isinstance(node, ast.ExceptHandler)]
    matching = []
    for handler in handlers:
        handler_source = ast.get_source_segment(source, handler) or ""
        if "Echec de la copie de sauvegarde" in handler_source:
            matching.append(handler)
    assert len(matching) == 1
    assert any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Constant)
        and node.value.value is False
        for node in ast.walk(matching[0])
    )


def test_legacy_silent_copy_failure_is_gone():
    source = TARGET.read_text(encoding="utf-8")
    assert "Le repertoire de destination de sauvegarde n'existe pas." not in source
