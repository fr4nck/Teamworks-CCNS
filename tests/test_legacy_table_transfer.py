"""The legacy transfer SQL compiler is deterministic and toolkit-agnostic."""

import ast
import sqlite3
from pathlib import Path

import pytest

from infrastructure.persistence.legacy_table_transfer import (
    legacy_mysql_columns_query,
    legacy_select_all_query,
    plan_legacy_table_transfer,
)


ROOT = Path(__file__).resolve().parents[1]


def test_import_projects_only_compatible_columns_in_source_order():
    plan = plan_legacy_table_transfer(
        "personnes", ["IDpersonne", "absent", "nom", "prenom"],
        destination_is_network=False,
        destination_columns={"IDpersonne": "INTEGER", "prenom": "VARCHAR", "nom": "VARCHAR"},
    )
    assert plan.columns == ("IDpersonne", "nom", "prenom")
    assert plan.select_query == "SELECT IDpersonne, nom, prenom FROM personnes"
    assert plan.insert_query == "INSERT INTO personnes (IDpersonne, nom, prenom) VALUES (?, ?, ?)"


def test_mysql_destination_uses_mysql_bind_placeholders():
    plan = plan_legacy_table_transfer(
        "contrats", ["IDcontrat", "IDpersonne", "date_debut"],
        destination_is_network=True,
    )
    assert plan.insert_query == (
        "INSERT INTO contrats (IDcontrat, IDpersonne, date_debut) VALUES (%s, %s, %s)"
    )


def test_historical_source_queries_are_preserved():
    assert legacy_select_all_query("contrats") == "SELECT * FROM contrats"
    assert legacy_mysql_columns_query("contrats") == "SHOW COLUMNS FROM contrats;"


def test_sqlite_source_copy_uses_real_connection_and_no_implicit_commit():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE source (id INTEGER, texte TEXT, ignored INTEGER)")
        connection.execute("CREATE TABLE cible (id INTEGER, texte TEXT)")
        connection.executemany(
            "INSERT INTO source VALUES (?, ?, ?)",
            [(1, "\u00c9t\u00e9", 99), (2, None, 100)],
        )
        plan = plan_legacy_table_transfer(
            "source", ["id", "texte", "ignored"],
            destination_is_network=False,
            destination_columns=("id", "texte"),
        )
        rows = connection.execute(plan.select_query).fetchall()
        # A destination table name can be selected by the caller: plans must
        # not silently mutate a source name or execute anything themselves.
        insert = plan_legacy_table_transfer(
            "cible", plan.columns, destination_is_network=False
        ).insert_query
        connection.executemany(insert, rows)
        assert connection.in_transaction
        assert connection.execute("SELECT * FROM cible").fetchall() == [
            (1, "\u00c9t\u00e9"), (2, None)
        ]
        connection.rollback()
        assert connection.execute("SELECT * FROM cible").fetchall() == []
    finally:
        connection.close()


@pytest.mark.parametrize(
    "name",
    (
        "", "bad-name", "bad.name", "bad/table", "x; DROP TABLE personnes",
        "col name", "col\na", "\u00e9t\u00e9", None, 1,
    ),
)
def test_malformed_table_names_fail_before_sql(name):
    with pytest.raises(ValueError, match="Invalid legacy SQL identifier"):
        legacy_select_all_query(name)
    with pytest.raises(ValueError, match="Invalid legacy SQL identifier"):
        legacy_mysql_columns_query(name)
    with pytest.raises(ValueError, match="Invalid legacy SQL identifier"):
        plan_legacy_table_transfer(name, ["id"], destination_is_network=False)


@pytest.mark.parametrize("column", ("x y", "a;b", "data.x", "a\x00b", None))
def test_malformed_columns_are_not_interpolated(column):
    with pytest.raises(ValueError, match="Invalid legacy SQL identifier"):
        plan_legacy_table_transfer("demo", ["id", column], destination_is_network=True)


def test_missing_projection_fails_before_execution():
    with pytest.raises(ValueError, match="No compatible legacy table columns"):
        plan_legacy_table_transfer(
            "demo", ["id"], destination_is_network=False,
            destination_columns={"other": "TEXT"},
        )


def test_all_declared_teamworks_legacy_table_identifiers_are_compatible():
    """Check the catalog rather than assuming all historical names are safe."""
    catalog = ROOT / "teamworks" / "Data" / "DATA_Tables.py"
    tree = ast.parse(catalog.read_text(encoding="utf-8"))
    data_dict = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "DB_DATA"
                for target in node.targets)
    )
    assert isinstance(data_dict, ast.Dict)
    assert len(data_dict.keys) >= 50
    for key, value in zip(data_dict.keys, data_dict.values):
        table = ast.literal_eval(key)
        assert legacy_select_all_query(table).startswith("SELECT * FROM ")
        if isinstance(value, ast.List):
            column_names = [
                ast.literal_eval(element.elts[0])
                for element in value.elts
                if isinstance(element, ast.Tuple)
            ]
            if column_names:
                plan_legacy_table_transfer(
                    table, column_names, destination_is_network=False
                )


def test_transfer_compiler_does_not_import_gui_or_drivers():
    path = ROOT / "infrastructure" / "persistence" / "legacy_table_transfer.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    assert not any(name.split(".")[0] in {
        "wx", "wxPython", "PySide6", "PyQt5", "PyQt6",
        "mysql", "MySQLdb", "psycopg", "teamworks",
    } for name in names)
