"""Garde-fou du socle commun : aucune couche UI dans domain/, application/, infrastructure/.

Les couches communes ne doivent importer ni wxPython, ni PySide6/PyQt, ni
ObjectListView. Les imports du code historique `teamworks.*` sont interdits
sauf exceptions explicitement listées (dette historique, sans dépendance UI).
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON_LAYERS = ("domain", "application", "infrastructure")
UI_ROOTS = {"wx", "PySide6", "PyQt5", "PyQt6", "ObjectListView"}

# Exceptions historiques : présentes avant le socle commun ; le module importé
# (teamworks.Utils.UTILS_Diagnostic_performance) n'importe ni wx ni Qt.
HISTORICAL_TEAMWORKS_IMPORTS = {
    "infrastructure/persistence/ccns_data_reader.py",
    "infrastructure/persistence/person_reader.py",
}


def _imported_roots(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0], node.lineno
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0], node.lineno


def _common_files():
    for layer in COMMON_LAYERS:
        yield from sorted((ROOT / layer).rglob("*.py"))


def test_common_layers_do_not_import_ui_toolkits():
    offenders = [
        f"{path.relative_to(ROOT).as_posix()}:{lineno} importe {root}"
        for path in _common_files()
        for root, lineno in _imported_roots(path)
        if root in UI_ROOTS
    ]
    assert offenders == []


def test_common_layers_do_not_import_legacy_teamworks_outside_documented_exceptions():
    offenders = [
        f"{rel}:{lineno} importe teamworks"
        for path in _common_files()
        for rel in [path.relative_to(ROOT).as_posix()]
        for root, lineno in _imported_roots(path)
        if root == "teamworks" and rel not in HISTORICAL_TEAMWORKS_IMPORTS
    ]
    assert offenders == []
