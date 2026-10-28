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
    # DB_DATA contains 57 tables; other dictionaries are separate catalogs.
    # Iterate every declaration below, without hiding any invalid entry.
    assert len(data.keys) >= 50
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
                if sql.startswith("ALTER TABLE demo DROP COLUMN cible"):
                    raise RuntimeError("injected failure before native ALTER")
                return cursor.execute(sql)

        with pytest.raises(RuntimeError, match="injected failure before native ALTER"):
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



def test_native_drop_preserves_unrelated_schema_objects_and_foreign_keys():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript("""
            CREATE TABLE parent (id INTEGER PRIMARY KEY);
            CREATE TABLE audit (demo_id INTEGER);
            CREATE TABLE demo (
                id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id),
                obsolete TEXT, email TEXT UNIQUE NOT NULL,
                state TEXT CHECK(state IN ('ok', 'hold'))
            );
            CREATE INDEX idx_demo_parent ON demo(parent_id);
            CREATE TRIGGER tr_demo_state AFTER UPDATE OF state ON demo
            BEGIN INSERT INTO audit(demo_id) VALUES (NEW.id); END;
            CREATE VIEW vw_demo AS SELECT id, email FROM demo;
            INSERT INTO parent VALUES (1);
            INSERT INTO demo VALUES (10, 1, 'discard', 'a@example.fr', 'ok');
        """)
        objects_before = connection.execute(
            "SELECT type,name,sql FROM sqlite_master "
            "WHERE (tbl_name='demo' AND type IN ('index','trigger')) "
            "OR name='vw_demo' ORDER BY type,name"
        ).fetchall()
        foreign_keys_before = connection.execute(
            "PRAGMA foreign_key_list(demo)"
        ).fetchall()

        assert drop_legacy_sqlite_column(
            connection.cursor(), "demo", "obsolete",
            [(row[1], row[2]) for row in connection.execute(
                "PRAGMA table_info('demo')"
            )],
        )
        assert connection.execute("SELECT * FROM demo").fetchall() == [
            (10, 1, "a@example.fr", "ok")
        ]
        assert connection.execute(
            "SELECT type,name,sql FROM sqlite_master "
            "WHERE (tbl_name='demo' AND type IN ('index','trigger')) "
            "OR name='vw_demo' ORDER BY type,name"
        ).fetchall() == objects_before
        assert connection.execute("PRAGMA foreign_key_list(demo)").fetchall() == foreign_keys_before
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)

        # The unique index, CHECK constraint, trigger and view remain usable.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO demo VALUES (11,1,'a@example.fr','ok')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE demo SET state='invalid' WHERE id=10"
            )
        connection.execute("UPDATE demo SET state='hold' WHERE id=10")
        assert connection.execute("SELECT * FROM audit").fetchall() == [(10,)]
        assert connection.execute("SELECT email FROM vw_demo").fetchall() == [
            ("a@example.fr",)
        ]
    finally:
        connection.close()


@pytest.mark.parametrize("dependent_object", (
    "CREATE INDEX ix_obsolete ON demo(obsolete)",
    "CREATE VIEW vw_obsolete AS SELECT obsolete FROM demo",
    "CREATE TRIGGER tr_obsolete AFTER UPDATE ON demo "
    "BEGIN INSERT INTO audit(value) VALUES (NEW.obsolete); END",
    "CREATE INDEX ix_partial ON demo(keep) WHERE obsolete IS NOT NULL",
))
def test_native_drop_refuses_referenced_columns_and_leaves_schema_intact(dependent_object):
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, obsolete TEXT, keep TEXT)")
        connection.execute("CREATE TABLE audit (value TEXT)")
        connection.execute(dependent_object)
        connection.execute("INSERT INTO demo VALUES (1,'X','Y')")
        connection.commit()
        original_schema = connection.execute(
            "SELECT type,name,sql FROM sqlite_master ORDER BY name"
        ).fetchall()
        with pytest.raises(sqlite3.OperationalError):
            drop_legacy_sqlite_column(
                connection.cursor(), "demo", "obsolete",
                [("id","INTEGER"), ("obsolete","TEXT"), ("keep","TEXT")]
            )
        assert connection.execute(
            "SELECT type,name,sql FROM sqlite_master ORDER BY name"
        ).fetchall() == original_schema
        assert connection.execute("SELECT * FROM demo").fetchall() == [(1,"X","Y")]
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    finally:
        connection.close()


@pytest.mark.parametrize("definition,column", (
    ("CREATE TABLE demo (id INTEGER PRIMARY KEY, obsolete TEXT, keep TEXT)", "id"),
    ("CREATE TABLE demo (id INTEGER, obsolete TEXT UNIQUE, keep TEXT)", "obsolete"),
    ("CREATE TABLE demo (id INTEGER, obsolete TEXT, keep TEXT CHECK(obsolete <> 'X'))", "obsolete"),
))
def test_native_drop_refuses_primary_unique_or_check_dependent_columns(definition, column):
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(definition)
        initial_schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name='demo'"
        ).fetchone()
        with pytest.raises(sqlite3.OperationalError):
            drop_legacy_sqlite_column(
                connection.cursor(), "demo", column,
                [("id","INTEGER"), ("obsolete","TEXT"), ("keep","TEXT")]
            )
        assert connection.execute(
            "SELECT sql FROM sqlite_master WHERE name='demo'"
        ).fetchone() == initial_schema
    finally:
        connection.close()


def test_native_drop_fails_closed_on_old_sqlite_without_running_sql(monkeypatch):
    from infrastructure.persistence import legacy_sqlite_column_migration as migration

    class NoSQL:
        def execute(self, statement):
            pytest.fail("Legacy destructive SQL must not execute: " + statement)

    monkeypatch.setattr(migration.sqlite3, "sqlite_version_info", (3, 34, 1))
    with pytest.raises(RuntimeError, match="3.35"):
        migration.drop_legacy_sqlite_column(
            NoSQL(), "demo", "obsolete",
            [("id","INTEGER"), ("obsolete","TEXT")]
        )


def test_native_drop_rolls_back_nested_ddl_without_affecting_outer_edits():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE demo (id INTEGER, obsolete TEXT, keep TEXT)")
        connection.execute("INSERT INTO demo VALUES (1,'a','b')")
        connection.commit()
        connection.execute("UPDATE demo SET keep='changed' WHERE id=1")
        # ALTER fails because a partial index still references obsolete.
        connection.execute(
            "CREATE INDEX ix_dep ON demo(keep) WHERE obsolete IS NOT NULL"
        )
        with pytest.raises(sqlite3.OperationalError):
            drop_legacy_sqlite_column(
                connection.cursor(), "demo", "obsolete",
                [("id","INTEGER"), ("obsolete","TEXT"), ("keep","TEXT")]
            )
        assert connection.in_transaction
        assert connection.execute("SELECT keep FROM demo").fetchall() == [
            ("changed",)
        ]
        connection.rollback()
        assert connection.execute("SELECT keep FROM demo").fetchall() == [("b",)]
    finally:
        connection.close()
