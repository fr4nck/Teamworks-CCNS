"""Qt GestionDB delegates SQLite table repair to a lossless core helper."""

import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.persistence.legacy_sqlite_table_repair import (
    repair_legacy_sqlite_table,
)


SOURCE = Path(__file__).resolve().parents[1] / "teamworks" / "GestionDB.py"


def _repair_method(catalog):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "DB")
    method = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "ReparationTable"
    )
    scope = {
        "Tables": SimpleNamespace(DB_DATA=catalog),
        "repair_legacy_sqlite_table": repair_legacy_sqlite_table,
    }
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), "exec"), scope)
    return scope["ReparationTable"]


def test_legacy_repair_adds_only_missing_columns_and_keeps_index_and_trigger(capsys):
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript("""
            CREATE TABLE demo (id INTEGER PRIMARY KEY AUTOINCREMENT, nom VARCHAR(100));
            CREATE TABLE audit (event TEXT);
            CREATE INDEX ix_demo_nom ON demo(nom);
            CREATE TRIGGER tr_demo_nom AFTER UPDATE OF nom ON demo
              BEGIN INSERT INTO audit(event) VALUES (NEW.nom); END;
            INSERT INTO demo (nom) VALUES ('Alice');
        """)
        rows_before = conn.execute("SELECT * FROM demo").fetchall()
        objects_before = conn.execute(
            "SELECT name,sql FROM sqlite_master "
            "WHERE name IN ('ix_demo_nom','tr_demo_nom') ORDER BY name"
        ).fetchall()
        catalog = {"demo": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nom", "VARCHAR(100)"),
            ("mail", "VARCHAR(200)"),
        ]}
        facade = SimpleNamespace(cursor=conn.cursor(), isNetwork=False)
        assert _repair_method(catalog)(facade, "demo") is None
        assert "terminee" in capsys.readouterr().out
        assert conn.execute(
            "SELECT id,nom FROM demo"
        ).fetchall() == rows_before
        assert conn.execute(
            "SELECT name,sql FROM sqlite_master "
            "WHERE name IN ('ix_demo_nom','tr_demo_nom') ORDER BY name"
        ).fetchall() == objects_before
        assert [x[1] for x in conn.execute("PRAGMA table_info(demo)")] == [
            "id", "nom", "mail"
        ]
        conn.execute("UPDATE demo SET nom='Alicia' WHERE id=1")
        assert conn.execute("SELECT event FROM audit").fetchall() == [("Alicia",)]
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    finally:
        conn.close()


def test_legacy_repair_refuses_type_mismatch_without_deleting_rows():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, nom TEXT)")
        conn.execute("INSERT INTO demo VALUES (42, 'Historique')")
        conn.commit()
        catalog = {"demo": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nom", "VARCHAR(100)"),
        ]}
        with pytest.raises(ValueError, match="definition differs"):
            _repair_method(catalog)(
                SimpleNamespace(cursor=conn.cursor(), isNetwork=False), "demo"
            )
        assert conn.execute("SELECT * FROM demo").fetchall() == [
            (42, "Historique")
        ]
        assert [x[1] for x in conn.execute("PRAGMA table_info(demo)")] == [
            "id", "nom"
        ]
    finally:
        conn.close()


def test_network_repair_is_still_disabled():
    class RefuseSQL:
        def execute(self, *_args):
            pytest.fail("No MySQL repair should be introduced by this lot")

    catalog = {"demo": [("id", "INTEGER")]}
    assert _repair_method(catalog)(
        SimpleNamespace(cursor=RefuseSQL(), isNetwork=True), "demo"
    ) is None


def test_bridge_does_not_construct_sql_or_call_executescript():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "DB")
    method = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "ReparationTable"
    )
    calls = [
        n.func.id for n in ast.walk(method)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    assert calls.count("repair_legacy_sqlite_table") == 1
    assert not any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr in {"executescript", "commit", "executemany"}
        for n in ast.walk(method)
    )
