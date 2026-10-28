"""SQLite real-schema tests for safe, additive Teamworks table repair."""

import ast
import sqlite3
from pathlib import Path

import pytest

from infrastructure.persistence.legacy_sqlite_table_repair import (
    repair_legacy_sqlite_table,
)


ROOT = Path(__file__).resolve().parents[1]


def _columns(connection):
    return [(x[1], x[2]) for x in connection.execute("PRAGMA table_info(demo)")]


def _desired(*extra):
    return [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("parent_id", "INTEGER"),
        ("nom", "VARCHAR(100)"),
        *extra,
    ]


def test_repair_adds_missing_columns_preserving_schema_and_data():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript("""
            CREATE TABLE parent (id INTEGER PRIMARY KEY);
            CREATE TABLE audit (event TEXT);
            CREATE TABLE demo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER REFERENCES parent(id),
                nom VARCHAR(100) UNIQUE NOT NULL
            );
            CREATE INDEX ix_demo_parent ON demo(parent_id);
            CREATE TRIGGER tr_demo_update AFTER UPDATE OF nom ON demo
            BEGIN INSERT INTO audit(event) VALUES (NEW.nom); END;
            CREATE VIEW vw_demo AS SELECT id,nom FROM demo;
            INSERT INTO parent VALUES (1);
            INSERT INTO demo(parent_id,nom) VALUES (1,'Alice');
        """)
        before = connection.execute(
            "SELECT type,name,sql FROM sqlite_master "
            "WHERE name IN ('ix_demo_parent','tr_demo_update','vw_demo') "
            "ORDER BY name"
        ).fetchall()
        fk = connection.execute("PRAGMA foreign_key_list(demo)").fetchall()
        added = repair_legacy_sqlite_table(
            connection.cursor(), "demo",
            _desired(("complement", "LONGBLOB"), ("compteur", "BIGINT")),
        )
        assert added == ("complement", "compteur")
        assert _columns(connection)[-2:] == [
            ("complement", "BLOB"), ("compteur", "INTEGER")
        ]
        assert connection.execute(
            "SELECT id,parent_id,nom,complement,compteur FROM demo"
        ).fetchall() == [(1, 1, "Alice", None, None)]
        assert connection.execute(
            "SELECT type,name,sql FROM sqlite_master "
            "WHERE name IN ('ix_demo_parent','tr_demo_update','vw_demo') "
            "ORDER BY name"
        ).fetchall() == before
        assert connection.execute("PRAGMA foreign_key_list(demo)").fetchall() == fk
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO demo(parent_id,nom) VALUES (1,'Alice')")
        connection.execute("UPDATE demo SET nom='Alicia' WHERE id=1")
        assert connection.execute("SELECT event FROM audit").fetchall() == [
            ("Alicia",)
        ]
        assert connection.execute("SELECT nom FROM vw_demo").fetchall() == [
            ("Alicia",)
        ]
    finally:
        connection.close()


def test_repair_is_noop_for_matching_schema_and_preserves_extra_columns():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            "CREATE TABLE demo (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " parent_id INTEGER, nom VARCHAR(100), extension TEXT)"
        )
        conn.commit()
        assert repair_legacy_sqlite_table(
            conn.cursor(), "demo", _desired()
        ) == ()
        assert "extension" in [item[0] for item in _columns(conn)]
        assert not conn.in_transaction
    finally:
        conn.close()


def test_repair_rollback_all_additions_on_failure_after_first_alter():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            "CREATE TABLE demo (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " parent_id INTEGER, nom VARCHAR(100))"
        )
        conn.execute("INSERT INTO demo(parent_id,nom) VALUES (3,'Present')")
        conn.commit()
        cursor = conn.cursor()
        class FailSecond:
            def execute(self, sql, params=()):
                if sql.startswith("ALTER TABLE demo ADD deux"):
                    raise RuntimeError("injected second ALTER failure")
                return cursor.execute(sql, params)
            def fetchone(self):
                return cursor.fetchone()
            def fetchall(self):
                return cursor.fetchall()
        with pytest.raises(RuntimeError, match="second ALTER failure"):
            repair_legacy_sqlite_table(
                FailSecond(), "demo",
                _desired(("un", "TEXT"), ("deux", "TEXT"))
            )
        assert [x[0] for x in _columns(conn)] == ["id", "parent_id", "nom"]
        assert conn.execute("SELECT id,parent_id,nom FROM demo").fetchall() == [
            (1, 3, "Present")
        ]
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    finally:
        conn.close()


def test_repair_does_not_commit_an_outer_transaction():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            "CREATE TABLE demo (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " parent_id INTEGER, nom VARCHAR(100))"
        )
        conn.execute("INSERT INTO demo(parent_id,nom) VALUES (3,'Alice')")
        conn.commit()
        conn.execute("UPDATE demo SET nom='Bob' WHERE id=1")
        assert conn.in_transaction
        assert repair_legacy_sqlite_table(
            conn.cursor(), "demo", _desired(("nouveau", "TEXT"))
        ) == ("nouveau",)
        assert conn.in_transaction
        conn.rollback()
        assert [x[0] for x in _columns(conn)] == ["id", "parent_id", "nom"]
        assert conn.execute("SELECT nom FROM demo").fetchall() == [("Alice",)]
    finally:
        conn.close()


@pytest.mark.parametrize("descriptor", [
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("id", "INTEGER"),
    ("id", "BIGINT"),
])
def test_repair_refuses_incompatible_existing_key_without_modifying_schema(descriptor):
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE demo (id TEXT, parent_id INTEGER, nom VARCHAR(100))")
        before = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name='demo'"
        ).fetchone()
        with pytest.raises(ValueError, match="definition differs"):
            repair_legacy_sqlite_table(conn.cursor(), "demo", [
                descriptor, ("parent_id", "INTEGER"), ("nom", "VARCHAR(100)"),
            ])
        assert conn.execute(
            "SELECT sql FROM sqlite_master WHERE name='demo'"
        ).fetchone() == before
    finally:
        conn.close()


def test_repair_refuses_missing_primary_key_without_any_mutation():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE demo (parent_id INTEGER, nom VARCHAR(100))")
        with pytest.raises(ValueError, match="key requires"):
            repair_legacy_sqlite_table(conn.cursor(), "demo", _desired())
        assert [x[0] for x in _columns(conn)] == ["parent_id", "nom"]
    finally:
        conn.close()


def test_repair_refuses_missing_table_without_creating_it():
    conn = sqlite3.connect(":memory:")
    try:
        with pytest.raises(ValueError, match="table is missing"):
            repair_legacy_sqlite_table(
                conn.cursor(), "demo", [("id", "INTEGER")]
            )
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='demo'"
        ).fetchall() == []
    finally:
        conn.close()


@pytest.mark.parametrize("table,field", [
    ("demo; DROP TABLE parent", "nom"), ("demo", "other; DROP TABLE demo"),
])
def test_repair_rejects_untrusted_sql_identifiers(table, field):
    conn = sqlite3.connect(":memory:")
    try:
        with pytest.raises(ValueError, match="identifier"):
            repair_legacy_sqlite_table(
                conn.cursor(), table, [(field, "TEXT")]
            )
    finally:
        conn.close()


def test_repair_rejects_duplicate_columns_case_insensitively():
    conn = sqlite3.connect(":memory:")
    try:
        with pytest.raises(ValueError, match="Duplicate"):
            repair_legacy_sqlite_table(
                conn.cursor(), "demo",
                [("nom", "TEXT"), ("NOM", "TEXT")]
            )
    finally:
        conn.close()


def test_repair_fails_closed_on_invalid_type_and_preserves_schema():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE demo (id INTEGER)")
        with pytest.raises(ValueError, match="column type"):
            repair_legacy_sqlite_table(
                conn.cursor(), "demo",
                [("id", "INTEGER"), ("x", "TEXT; DROP TABLE demo")]
            )
        assert _columns(conn) == [("id", "INTEGER")]
    finally:
        conn.close()


def test_repair_module_does_not_import_wx_qt_or_drivers():
    p = ROOT / "infrastructure" / "persistence" / "legacy_sqlite_table_repair.py"
    tree = ast.parse(p.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any(name.split(".")[0] in {
        "wx", "wxPython", "PySide6", "PyQt5", "PyQt6",
        "mysql", "MySQLdb", "psycopg", "teamworks",
    } for name in imports)
