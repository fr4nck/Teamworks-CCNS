# -*- coding: utf-8 -*-
import ast
import importlib
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
CHEMINS = TEAMWORKS / "Chemins.py"
GESTION_DB = TEAMWORKS / "GestionDB.py"
FONCTIONS_PERSO = TEAMWORKS / "FonctionsPerso.py"


def test_sqlite_compatibility_decodes_only_byte_paths():
    source = CHEMINS.read_text(encoding="utf-8")
    assert "if isinstance(database, bytes):" in source
    assert 'database = database.decode("utf-8")' in source
    assert "return _SQLITE_CONNECT_ORIGINAL(database, *args, **kwargs)" in source


def test_sqlite_compatibility_is_idempotent():
    source = CHEMINS.read_text(encoding="utf-8")
    assert 'getattr(_SQLITE_CONNECT_CURRENT, "_teamworks_text_paths", False)' in source
    assert "_sqlite_connect_text_path._teamworks_text_paths = True" in source
    assert "_teamworks_original_connect" in source


def test_sqlite_compatibility_survives_module_reload():
    original_connect = sqlite3.connect
    sys.path.insert(0, str(TEAMWORKS))
    sys.modules.pop("Chemins", None)
    try:
        module = importlib.import_module("Chemins")
        importlib.reload(module)
        connection = sqlite3.connect(":memory:")
        connection.close()
    finally:
        sqlite3.connect = original_connect
        sys.modules.pop("Chemins", None)
        if sys.path and sys.path[0] == str(TEAMWORKS):
            sys.path.pop(0)


def test_runtime_sqlite_calls_use_native_text_paths():
    gestion = GESTION_DB.read_text(encoding="utf-8")
    fonctions = FONCTIONS_PERSO.read_text(encoding="utf-8")
    sqlite_engine = (
        ROOT / "infrastructure" / "persistence" / "legacy_sqlite_connection.py"
    ).read_text(encoding="utf-8")

    # Chemins reste importe tot pour les extensions historiques utilisant des
    # chemins bytes. Le runtime Teamworks, lui, ne doit jamais les encoder.
    assert gestion.index("import Chemins") < gestion.index("import sqlite3")
    assert fonctions.index("import Chemins") < fonctions.index("import sqlite3")

    db_tree = ast.parse(gestion)
    db_class = next(
        node for node in db_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "DB"
    )
    open_method = next(
        node for node in db_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "OuvertureFichierLocal"
    )
    bridge_calls = [
        node for node in ast.walk(open_method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "open_legacy_sqlite"
    ]
    assert len(bridge_calls) == 1
    assert len(bridge_calls[0].args) == 1
    assert isinstance(bridge_calls[0].args[0], ast.Name)
    assert bridge_calls[0].args[0].id == "nomFichier"

    engine_tree = ast.parse(sqlite_engine)
    engine_open = next(
        node for node in engine_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "open_legacy_sqlite"
    )
    connect_calls = [
        node for node in ast.walk(engine_open)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "connect"
    ]
    assert len(connect_calls) == 1
    assert len(connect_calls[0].args) == 1
    assert isinstance(connect_calls[0].args[0], ast.Name)
    assert connect_calls[0].args[0].id == "path"

    # Le connecteur injecte est sqlite3.connect, sans conversion texte -> bytes.
    defaults = dict(zip(engine_open.args.kwonlyargs, engine_open.args.kw_defaults))
    connect_arg = next(key for key in defaults if key.arg == "connect")
    default_connect = defaults[connect_arg]
    assert isinstance(default_connect, ast.Attribute)
    assert default_connect.attr == "connect"
    assert isinstance(default_connect.value, ast.Name)
    assert default_connect.value.id == "sqlite3"

    assert "sqlite3.connect(nomFichierdefault)" in gestion
    assert "sqlite3.connect(nomFichier)" in fonctions
    assert "sqlite3.connect(nomFichier.encode('utf-8'))" not in gestion
    assert "sqlite3.connect(nomFichierdefault.encode('utf-8'))" not in gestion
    assert "sqlite3.connect(nomFichier.encode('utf-8'))" not in fonctions
    assert "connect(path.encode(" not in sqlite_engine


def test_text_paths_and_sqlite_special_names_are_not_rewritten():
    source = CHEMINS.read_text(encoding="utf-8")
    assert "if isinstance(database, bytes):" in source
    assert "else:" not in source.split("if isinstance(database, bytes):", 1)[1].split(
        "return _SQLITE_CONNECT_ORIGINAL", 1
    )[0]
