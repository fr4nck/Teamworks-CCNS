"""Regression tests for MySQL schema selection without a real server."""

import ast
from pathlib import Path

import pytest

from infrastructure.persistence.legacy_mysql_schema import (
    activate_legacy_mysql_schema,
    mysql_schema_commands,
    quote_mysql_schema_name,
)


def test_standard_schema_is_selected_without_creation():
    assert mysql_schema_commands("association_tdata") == (
        "USE \x60association_tdata\x60;",
    )


def test_creation_preserves_legacy_order_and_charset():
    assert mysql_schema_commands("association_tphotos", allow_creation=True) == (
        "CREATE DATABASE IF NOT EXISTS \x60association_tphotos\x60 CHARSET utf8 COLLATE utf8_unicode_ci;",
        "USE \x60association_tphotos\x60;",
    )


def test_missing_and_sentinel_names_preserve_legacy_no_use_behavior():
    assert mysql_schema_commands("") == ()
    assert mysql_schema_commands(None) == ()
    assert mysql_schema_commands("_tdata") == ()
    assert mysql_schema_commands("_tdata", allow_creation=True) == (
        "CREATE DATABASE IF NOT EXISTS \x60_tdata\x60 CHARSET utf8 COLLATE utf8_unicode_ci;",
    )


def test_non_ascii_hyphens_and_escaped_quote_remain_safe_identifiers():
    assert quote_mysql_schema_name("equipe-\u00e9t\u00e9") == "\x60equipe-\u00e9t\u00e9\x60"
    assert quote_mysql_schema_name("name\x60part") == "\x60name\x60\x60part\x60"


@pytest.mark.parametrize(
    "name",
    (
        3, "x" * 65, " association", "association ", "bad/name",
        "bad\\name", "bad.name", "rh;DROP DATABASE equipe", "line\nname",
        "\x00", "name\r", "a\tb", "bad\x7fname",
    ),
)
def test_invalid_schema_names_fail_before_sql_or_echo(name):
    with pytest.raises(ValueError, match="Invalid MySQL schema name") as err:
        quote_mysql_schema_name(name)
    assert "DROP" not in str(err.value)


def test_invalid_create_name_fails_before_using_cursor():
    class NoSQL:
        def execute(self, *_):
            pytest.fail("No SQL may run for empty-name creation")

    with pytest.raises(ValueError):
        activate_legacy_mysql_schema(NoSQL(), "", allow_creation=True)


def test_schema_activation_uses_existing_cursor_without_transactions():
    events = []

    class Cursor:
        def execute(self, query):
            events.append(query)

    activate_legacy_mysql_schema(Cursor(), "rh_tdata", allow_creation=True)
    assert events == [
        "CREATE DATABASE IF NOT EXISTS \x60rh_tdata\x60 CHARSET utf8 COLLATE utf8_unicode_ci;",
        "USE \x60rh_tdata\x60;",
    ]


def test_schema_activation_stops_on_sql_failure_without_implicit_rollback():
    events = []

    class Cursor:
        def execute(self, query):
            events.append(query)
            if query.startswith("CREATE DATABASE"):
                raise RuntimeError("mysql error")

    with pytest.raises(RuntimeError, match="mysql error"):
        activate_legacy_mysql_schema(Cursor(), "rh_tdata", allow_creation=True)
    assert len(events) == 1


def test_schema_module_does_not_import_gui_or_database_drivers():
    path = Path(__file__).resolve().parents[1] / "infrastructure/persistence/legacy_mysql_schema.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any(
        name.split(".")[0] in {
            "wx", "wxPython", "PySide6", "PyQt6", "MySQLdb",
            "mysql", "GestionDB", "teamworks",
        } for name in imports
    )
