"""Qt DDL bridges: synthetic MySQL, actual SQLite and rollback preservation."""

import ast
import sqlite3
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.persistence.legacy_table_ddl import (
    legacy_add_column_query,
    legacy_change_mysql_column_query,
    legacy_create_index_query,
    legacy_create_table_query,
    legacy_drop_mysql_column_query,
)
from infrastructure.persistence.legacy_sqlite_column_migration import (
    drop_legacy_sqlite_column,
)


SOURCE = Path(__file__).resolve().parents[1] / "teamworks" / "GestionDB.py"


def _legacy_method(name, **dependencies):
    parsed = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    cls = next(x for x in parsed.body if isinstance(x, ast.ClassDef) and x.name == "DB")
    method = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == name)
    context = {
        "legacy_create_table_query": legacy_create_table_query,
        "legacy_add_column_query": legacy_add_column_query,
        "legacy_drop_mysql_column_query": legacy_drop_mysql_column_query,
        "legacy_change_mysql_column_query": legacy_change_mysql_column_query,
        "legacy_create_index_query": legacy_create_index_query,
        "drop_legacy_sqlite_column": drop_legacy_sqlite_column,
        "DiagnosticPerformance": SimpleNamespace(mesurer=lambda *_a, **_k: nullcontext()),
        "_": lambda x: x,
    }
    context.update(dependencies)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), "exec"), context)
    return context[name]


def test_qt_creation_table_delegates_to_shared_sqlite_ddl():
    connection = sqlite3.connect(":memory:")
    try:
        db = SimpleNamespace(isNetwork=False, cursor=connection.cursor())
        _legacy_method("CreationTable")(
            db, "demo", {"demo": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID", "Identifier"),
                ("nom", "VARCHAR(100)", "Name", "Name"),
            ]}
        )
        connection.execute("INSERT INTO demo (nom) VALUES (?)", ("Alice",))
        assert connection.execute("SELECT id, nom FROM demo").fetchall() == [(1, "Alice")]
    finally:
        connection.close()


def test_qt_creation_tables_preserves_status_and_catches_sql_errors():
    executed, statuses = [], []

    class Cursor:
        def execute(self, sql):
            executed.append(sql)
            if sql.startswith("CREATE TABLE broken"):
                raise sqlite3.OperationalError("creation refused")

    db = SimpleNamespace(isNetwork=False, cursor=Cursor())
    screen = SimpleNamespace(SetStatusText=lambda value: statuses.append(value))
    _legacy_method("CreationTables")(
        db,
        {"demo": [("id", "INTEGER")], "broken": [("id", "INTEGER")]},
        fenetreParente=screen,
    )
    assert executed == [
        "CREATE TABLE demo (id INTEGER)", "CREATE TABLE broken (id INTEGER)"
    ]
    assert len(statuses) == 2


def test_qt_creation_tables_mysql_uses_existing_type_conversions():
    executed = []
    db = SimpleNamespace(isNetwork=True, cursor=SimpleNamespace(
        execute=lambda sql: executed.append(sql)
    ))
    _legacy_method("CreationTables")(
        db, {"demo": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("prix", "FLOAT"),
            ("date", "DATE"),
            ("note", "VARCHAR(50000)"),
        ]},
    )
    assert executed == [
        "CREATE TABLE demo (id INTEGER PRIMARY KEY AUTO_INCREMENT, prix REAL, date VARCHAR(10), note MEDIUMTEXT)"
    ]


def test_qt_sqlite_drop_keeps_rows_without_implicit_commit():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE demo (id INTEGER, removed TEXT, keep TEXT)")
        connection.execute("INSERT INTO demo VALUES (1, 'x', 'ok')")
        connection.commit()

        class DB:
            isNetwork = False
            cursor = connection.cursor()

            def GetListeChamps2(self, _name):
                return [(x[1], x[2]) for x in connection.execute(
                    "PRAGMA table_info('demo')"
                )]

        _legacy_method("SupprChamp")(DB(), "demo", "removed")
        assert [x[1] for x in connection.execute(
            "PRAGMA table_info('demo')"
        )] == ["id", "keep"]
        assert connection.execute("SELECT id, keep FROM demo").fetchall() == [(1, "ok")]
        assert not connection.in_transaction
    finally:
        connection.close()


def test_qt_sqlite_drop_reconstruction_failure_rolls_back():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE demo (id INTEGER, removed TEXT, keep TEXT)")
        connection.execute("INSERT INTO demo VALUES (1, 'x', 'ok')")
        connection.commit()
        cursor = connection.cursor()

        class FaultyCursor:
            def execute(self, sql):
                if sql.startswith("CREATE TABLE demo("):
                    raise RuntimeError("failure after DROP")
                return cursor.execute(sql)

        class DB:
            isNetwork = False
            cursor = FaultyCursor()

            def GetListeChamps2(self, _name):
                return [(x[1], x[2]) for x in connection.execute(
                    "PRAGMA table_info('demo')"
                )]

        with pytest.raises(RuntimeError, match="failure after DROP"):
            _legacy_method("SupprChamp")(DB(), "demo", "removed")
        assert connection.execute("SELECT * FROM demo").fetchall() == [(1, "x", "ok")]
        assert [x[1] for x in connection.execute("PRAGMA table_info('demo')")] == [
            "id", "removed", "keep"
        ]
    finally:
        connection.close()


def test_qt_mysql_drop_add_and_change_preserve_historical_commit_calls():
    commands, committed = [], []

    class Fake:
        isNetwork = True
        def ExecuterReq(self, query):
            commands.append(query)
        def Commit(self):
            committed.append("commit")

    fake = Fake()
    _legacy_method("SupprChamp")(fake, "demo", "old")
    _legacy_method("AjoutChamp")(fake, "demo", "extra", "TEXT")
    _legacy_method("ConversionTypeChamp")(fake, "demo", "extra", "FLOAT")
    assert commands == [
        "ALTER TABLE demo DROP old;",
        "ALTER TABLE demo ADD extra TEXT;",
        "ALTER TABLE demo CHANGE extra extra FLOAT;",
    ]
    assert committed == ["commit", "commit"]


def test_qt_create_index_uses_shared_ddl_only_when_table_exists():
    queries, commits = [], []

    class Fake:
        def IsTableExists(self, _table):
            return True
        def ExecuterReq(self, query):
            queries.append(query)
        def Commit(self):
            commits.append(1)

    _legacy_method("CreationIndex", Tables=SimpleNamespace(
        DB_INDEX={"idx_demo": {"table": "demo", "champ": "name"}}
    ))(Fake(), "idx_demo")
    assert queries == ["CREATE INDEX idx_demo ON demo (name);"]
    assert commits == [1]


def test_qt_ddl_calls_have_no_inline_schema_construction_in_migrated_paths():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "DB")
    mappings = {
        "CreationTables": "legacy_create_table_query",
        "CreationTable": "legacy_create_table_query",
        "SupprChamp": "drop_legacy_sqlite_column",
        "AjoutChamp": "legacy_add_column_query",
        "ConversionTypeChamp": "legacy_change_mysql_column_query",
        "CreationIndex": "legacy_create_index_query",
    }
    for name, expected in mappings.items():
        method = next(x for x in cls.body
                      if isinstance(x, ast.FunctionDef) and x.name == name)
        calls = [x.func.id for x in ast.walk(method)
                 if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)]
        assert expected in calls
