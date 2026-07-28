# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHEMINS = ROOT / "teamworks" / "Chemins.py"
GESTION_DB = ROOT / "teamworks" / "GestionDB.py"
FONCTIONS_PERSO = ROOT / "teamworks" / "FonctionsPerso.py"


def test_sqlite_compatibility_decodes_only_byte_paths():
    source = CHEMINS.read_text(encoding="utf-8")
    assert "if isinstance(database, bytes):" in source
    assert 'database = database.decode("utf-8")' in source
    assert "return _SQLITE_CONNECT_ORIGINAL(database, *args, **kwargs)" in source


def test_sqlite_compatibility_is_idempotent():
    source = CHEMINS.read_text(encoding="utf-8")
    assert 'getattr(sqlite3.connect, "_teamworks_text_paths", False)' in source
    assert "_sqlite_connect_text_path._teamworks_text_paths = True" in source


def test_legacy_byte_path_calls_are_covered_by_early_chemins_import():
    gestion = GESTION_DB.read_text(encoding="iso-8859-15")
    fonctions = FONCTIONS_PERSO.read_text(encoding="iso-8859-15")

    assert gestion.index("import Chemins") < gestion.index("import sqlite3")
    assert fonctions.index("import Chemins") < fonctions.index("import sqlite3")
    assert "sqlite3.connect(nomFichier.encode('utf-8'))" in gestion
    assert "sqlite3.connect(nomFichier.encode('utf-8'))" in fonctions


def test_text_paths_and_sqlite_special_names_are_not_rewritten():
    source = CHEMINS.read_text(encoding="utf-8")
    assert "if isinstance(database, bytes):" in source
    assert "else:" not in source.split("if isinstance(database, bytes):", 1)[1].split(
        "return _SQLITE_CONNECT_ORIGINAL", 1
    )[0]
