# -*- coding: utf-8 -*-
"""Guarde-fou statique pour les gestionnaires wxPython liés par ``self.Bind``."""

from __future__ import annotations

import ast
import tokenize
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"


def _read_python(path: Path) -> str:
    with tokenize.open(path) as stream:
        return stream.read()


def _missing_handlers(path: Path) -> list[str]:
    tree = ast.parse(_read_python(path), filename=str(path))
    missing: list[str] = []
    for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        methods = {
            node.name
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for node in ast.walk(class_node):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Attribute) and node.func.attr == "Bind"):
                continue
            if len(node.args) < 2:
                continue
            handler = node.args[1]
            if (
                isinstance(handler, ast.Attribute)
                and isinstance(handler.value, ast.Name)
                and handler.value.id == "self"
                and handler.attr not in methods
            ):
                missing.append(
                    f"{path.relative_to(ROOT)}:{node.lineno} "
                    f"{class_node.name}.{handler.attr}"
                )
    return missing


def test_all_bound_self_handlers_exist():
    missing: list[str] = []
    for path in sorted(TEAMWORKS.rglob("*.py")):
        try:
            missing.extend(_missing_handlers(path))
        except (SyntaxError, UnicodeDecodeError):
            # Les inventaires de compilation dédiés couvrent déjà ces fichiers.
            continue
    assert not missing, "Gestionnaires wxPython absents :\n" + "\n".join(missing)
