"""DDL extraction, real SQLite rollback and compatibility with catalog types."""

import ast
import sqlite3
from pathlib import Path

import pytest

from infrastructure.persistence.legacy_table_ddl import (
    legacy_add_column_query,
    legacy_change_mysql_column_query,
    legacy_create_index_query,
    legacy_create_table_query,
    legacy_drop_mysql_column_query,
)
from infrastructure.persistence.legacy_sqlite_column_migration import drop_legacy_sqlite_column


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("network,expected", [
    (False, "CREATE TABLE demo (id INTEGER PRIMARY KEY AUTOINCREMENT, photo BLOB, large INTEGER, taux FLOAT, date DATE, long_txt VARCHAR(30000))"),
    (True, "CREATE TABLE demo (id INTEGER PRIMARY KEY AUTO_INCREMENT, photo LONGBLOB, large BIGINT, taux REAL, date VARCHAR(10), long_txt MEDIUMTEXT)"),
])
def test_create_table_preserves_historical_sqlite_mysql_types(network, expected):
    descriptions = [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("photo", "LONGBLOB"), ("large", "BIGINT"),
        ("taux", "FLOAT"), ("date", "DATE"), ("long_txt", "VARCHAR(30000)"),
    ]
    assert legacy_create_table_query("demo", descriptions, is_network=network) == expected


@pytest.mark.parametrize("size,expected", [
    (255, "VARCHAR(255)"), (256, "TEXT(256)"),
    (20000, "TEXT(20000)"), (20001, "MEDIUMTEXT"),
])
def test_varchar_thresholds_match_legacy_logic(size, expected):
    assert legacy_create_table_query(
        "demo", [("champ", "VARCHAR(%d)" % size)], is_network=True,
    ) == "CREATE TABLE demo (champ %s)" % expected


def test_alter_and_index_queries_keep_original_column_types():
    assert legacy_add_column_query("t", "c", "LONGBLOB") == "ALTER TABLE t ADD c LONGBLOB;"
    assert legacy_add_column_query("t", "c", "DATE") == "ALTER TABLE t ADD c DATE;"
    assert legacy_drop_mysql_column_query("t", "c") == "ALTER TABLE t DROP c;"
    assert legacy_change_mysql_column_query("t", "c", "FLOAT") == "ALTER TABLE t CHANGE c c FLOAT;"
    assert legacy_create_index_query("ix_c", "t", "c") == "CREATE INDEX ix_c ON t (c);"


@pytest.mark.parametrize("name", [
    "", "bad-name", "bad.name", "bad/table", "a; DROP TABLE t", "col name", None,
])
def test_table_identifiers_do_not_accept_untrusted_sql(name):
    with pytest.raises(ValueError, match="Invalid legacy SQL identifier"):
        legacy_create_table_query(name, [("x", "INTEGER")], is_network=False)
    with pytest.raises(ValueError, match="Invalid legacy SQL identifier"):
        legacy_add_column_query("demo", name, "TEXT")


@pytest.mark.parametrize("type_name", [
    "TEXT; DROP TABLE demo", "TEXT --", "VARCHAR(5)\nSELECT",
    "TEXT;", "", None,
])
def test_unsafe_column_types_fail_before_sql(type_name):
    with pytest.raises(ValueError, match="Invalid legacy column type"):
        legacy_create_table_query("demo", [("x", type_name)], is_network=False)


def test_empty_catalogue_entry_is_rejected():
    with pytest.raises(ValueError, match="without columns"):
        legacy_create_table_query("demo", [], is_network=False)


def test_declared_catalog_tables_are_valid_for_both_dialects():
    tree = ast.parse(
        (ROOT / "teamworks" / "Data" / "DATA_Tables.py").read_text(encoding="utf-8")
    )
    data = next(
        n.value for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "DB_DATA"
                for target in n.targets)
    )
    assert isinstance(data, ast.Dict)
    assert len(data.keys) >= 70
    for key, value in zip(data.keys, data.values):
        assert isinstance(value, ast.List)
        name = ast.literal_eval(key)
        descriptions = [
            tuple(ast.literal_eval(entry.elts[i]) for i in (0, 1))
            for entry in value.elts
        ]
        assert legacy_create_table_query(
            name, descriptions, is_network=False
        ).startswith("CREATE TABLE ")
        assert legacy_create_table_query(
            name, descriptions, is_network=True
        ).startswith("CREATE TABLE ")


def test_create_and_add_column_execute_on_actual_sqlite():
    database = sqlite3.connect(":memory:")
    try:
        database.execute(legacy_create_table_query(
            "demo", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                     ("nom", "VARCHAR(42)")], is_network=False,
        ))
        database.execute(legacy_add_column_query("demo", "email", "VARCHAR(42)"))
        database.execute(legacy_create_index_query("ix_email", "demo", "email"))
        assert [row[1] for row in database.execute(
            "PRAGMA table_info('demo')"
        )] == ["id", "nom", "email"]
    finally:
        database.close()


def _column_info(connection):
    return [(row[1], row[2]) for row in connection.execute("PRAGMA table_info('demo')")]


def test_drop_column_failure_rolls_back_schema_and_rows():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE demo (id INTEGER, cible TEXT, reste TEXT)")
        connection.execute("INSERT INTO demo VALUES (1, 'X', 'Y')")
        connection.commit()
        previous_columns = _column_info(connection)
        cursor = connection.cursor()

        class FailingCursor:
            def execute(self, sql):
                if sql.startswith("CREATE TABLE demo("):
                    raise RuntimeError("injected failure after DROP")
                return cursor.execute(sql)

        with pytest.raises(RuntimeError, match="injected failure"):
            drop_legacy_sqlite_column(
                FailingCursor(), "demo", "cible", previous_columns
            )
        assert _column_info(connection) == previous_columns
        assert connection.execute("SELECT * FROM demo").fetchall() == [(1, "X", "Y")]
        assert connection.execute(
            "SELECT name FROM sqlite_temp_master WHERE type='table'"
        ).fetchall() == []
    finally:
        connection.close()


def test_drop_column_preserves_enclosing_transaction_and_explicit_rollback():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE demo (id INTEGER, cible TEXT, reste TEXT)")
        connection.execute("INSERT INTO demo VALUES (1, 'X', 'Y')")
        connection.commit()
        connection.execute("INSERT INTO demo VALUES (2, 'A', 'B')")
        assert connection.in_transaction
        assert drop_legacy_sqlite_column(
            connection.cursor(), "demo", "cible", _column_info(connection),
        )
        assert connection.in_transaction
        assert connection.execute("SELECT id, reste FROM demo").fetchall() == [
            (1, "Y"), (2, "B")
        ]
        connection.rollback()
        assert [row[1] for row in connection.execute(
            "PRAGMA table_info('demo')"
        )] == ["id", "cible", "reste"]
        assert connection.execute("SELECT * FROM demo").fetchall() == [(1, "X", "Y")]
    finally:
        connection.close()


def test_drop_column_nonsuccess_does_not_issue_sql():
    class RejectSQL:
        def execute(self, sql):
            raise AssertionError("Unexpected SQL: %s" % sql)

    cursor = RejectSQL()
    assert drop_legacy_sqlite_column(
        cursor, "demo", "missing", [("id", "INTEGER"), ("a", "TEXT")]
    ) is False
    assert drop_legacy_sqlite_column(
        cursor, "demo", "id", [("id", "INTEGER")]
    ) is False


def test_drop_column_success_keeps_order_and_nulls():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE demo (id INTEGER, cible TEXT, reste TEXT)")
        connection.executemany("INSERT INTO demo VALUES (?, ?, ?)", [
            (1, "X", None), (2, "Y", "Z")
        ])
        connection.commit()
        assert drop_legacy_sqlite_column(
            connection.cursor(), "demo", "cible", _column_info(connection)
        )
        assert connection.execute("SELECT * FROM demo").fetchall() == [
            (1, None), (2, "Z")
        ]
    finally:
        connection.close()


def test_new_ddl_modules_have_no_ui_or_database_driver_imports():
    for name in ("legacy_table_ddl.py", "legacy_sqlite_column_migration.py"):
        tree = ast.parse(
            (ROOT / "infrastructure" / "persistence" / name).read_text(encoding="utf-8")
        )
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        assert not any(name.split(".")[0] in {
            "wx", "wxPython", "PySide6", "PyQt6",
            "mysql", "MySQLdb", "teamworks", "psycopg",
        } for name in imports)
