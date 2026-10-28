"""Validate Qt import/export bridges without importing the wx-era GestionDB module."""

import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace

from infrastructure.persistence.legacy_mysql_schema import activate_legacy_mysql_schema
from infrastructure.persistence.legacy_sql_batch import execute_legacy_batch
from infrastructure.persistence.legacy_table_transfer import (
    legacy_select_all_query,
    legacy_mysql_columns_query,
    plan_legacy_table_transfer,
)


SOURCE = Path(__file__).resolve().parents[1] / "teamworks/GestionDB.py"


def _legacy_method(name, **dependencies):
    parsed = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    cls = next(x for x in parsed.body if isinstance(x, ast.ClassDef) and x.name == "DB")
    fn = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == name)
    namespace = {
        "Chemins": SimpleNamespace(GetStaticPath=lambda path: path),
        "activate_legacy_mysql_schema": activate_legacy_mysql_schema,
        "execute_legacy_batch": execute_legacy_batch,
        "legacy_select_all_query": legacy_select_all_query,
        "legacy_mysql_columns_query": legacy_mysql_columns_query,
        "plan_legacy_table_transfer": plan_legacy_table_transfer,
        "sqlite3": sqlite3,
        "_": lambda text: text,
    }
    namespace.update(dependencies)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace[name]


class _MySqlSourceCursor:
    description = (("id",), ("name",))

    def __init__(self):
        self.executed = []
        self.last_sql = ""

    def execute(self, sql):
        self.executed.append(sql)
        self.last_sql = sql

    def fetchall(self):
        if self.last_sql.startswith("SHOW COLUMNS"):
            return [(("id", "INTEGER")), (("name", "VARCHAR(30)"))]
        return [(1, "Alice"), (2, "Bob")]


class _MySqlSourceConnection:
    def __init__(self):
        self.cursor_object = _MySqlSourceCursor()
        self.was_closed = False

    def cursor(self):
        return self.cursor_object

    def close(self):
        self.was_closed = True


def test_importation_table_from_mysql_uses_common_schema_and_preserves_commit():
    source = _MySqlSourceConnection()
    destination = sqlite3.connect(":memory:")
    try:
        destination.execute("CREATE TABLE demo (id INTEGER, name TEXT)")
        method = _legacy_method(
            "Importation_table",
            os=SimpleNamespace(path=SimpleNamespace(isfile=lambda _: True)),
            GetConnexionReseau=lambda _: (source, "source_tdata"),
            GetChampsTable=lambda name: {"id": "INTEGER", "name": "VARCHAR(30)"},
        )
        adapter = SimpleNamespace(
            cursor=destination.cursor(), connexion=destination, isNetwork=False
        )
        result = method(adapter, "demo", nomFichierdefault="legacy-ref", mode="network")
        assert result == (True, None)
        assert source.cursor_object.executed[0] == "USE \x60source_tdata\x60;"
        assert destination.execute("SELECT id, name FROM demo").fetchall() == [
            (1, "Alice"), (2, "Bob")
        ]
        assert not destination.in_transaction
    finally:
        destination.close()


def test_importation_table_reseau_keeps_local_destination_and_closes_source():
    source = _MySqlSourceConnection()
    destination = sqlite3.connect(":memory:")
    try:
        destination.execute("CREATE TABLE demo (id INTEGER, name TEXT)")
        method = _legacy_method(
            "Importation_table_reseau",
            GetConnexionReseau=lambda _: (source, "source_tdata"),
        )
        adapter = SimpleNamespace(cursor=destination.cursor(), connexion=destination)
        assert method(adapter, "demo", nomFichier="legacy-ref") == (True, None)
        assert source.cursor_object.executed[0] == "USE \x60source_tdata\x60;"
        assert destination.execute("SELECT id, name FROM demo").fetchall() == [
            (1, "Alice"), (2, "Bob")
        ]
        assert not destination.in_transaction
        assert source.was_closed is True
    finally:
        destination.close()


def test_importation_table_sql_failure_returns_error_without_commit():
    source = _MySqlSourceConnection()

    class BrokenCursor:
        def executemany(self, *_):
            raise sqlite3.OperationalError("simulated import failure")

    class Destination:
        def commit(self):
            raise AssertionError("Commit must not run after a failed batch")

    method = _legacy_method(
        "Importation_table",
        os=SimpleNamespace(path=SimpleNamespace(isfile=lambda _: True)),
        GetConnexionReseau=lambda _: (source, "source_tdata"),
        GetChampsTable=lambda _: {"id": "INTEGER", "name": "VARCHAR(30)"},
    )
    adapter = SimpleNamespace(cursor=BrokenCursor(), connexion=Destination(), isNetwork=False)
    success, details = method(adapter, "demo", nomFichierdefault="legacy-ref", mode="network")
    assert success is False
    assert "simulated import failure" in details


def test_exportation_vers_defaut_preserves_schema_rows_and_durable_commit(tmp_path):
    dest = tmp_path / "export.dat"
    method = _legacy_method(
        "Exportation_vers_base_defaut",
        Tables=SimpleNamespace(
            DB_DATA={"demo": [("id", "INTEGER"), ("name", "VARCHAR(30)")]}
        ),
    )

    class Source:
        isNetwork = False

        def GetListeChamps2(self, name):
            assert name == "demo"
            return [("id", "INTEGER"), ("name", "VARCHAR(30)")]

        def ExecuterReq(self, query):
            assert query == "SELECT * FROM demo"

        def ResultatReq(self):
            return [(3, "Carol"), (4, "Diane")]

    assert method(Source(), "demo", nomFichierdefault=str(dest)) is None
    with sqlite3.connect(dest) as reopened:
        assert reopened.execute("SELECT id, name FROM demo ORDER BY id").fetchall() == [
            (3, "Carol"), (4, "Diane")
        ]


def test_import_export_bridges_keep_clear_boundaries():
    parsed = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(x for x in parsed.body if isinstance(x, ast.ClassDef) and x.name == "DB")
    for name in ("Importation_table", "Importation_table_reseau", "Exportation_vers_base_defaut"):
        fn = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == name)
        call_names = [
            node.func.id for node in ast.walk(fn)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert "execute_legacy_batch" in call_names
        if name != "Exportation_vers_base_defaut":
            assert "activate_legacy_mysql_schema" in call_names
        # No direct cursor.executemany in the migrated procedures.
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "executemany"
            for node in ast.walk(fn)
        )


def test_import_export_bridges_do_not_add_a_new_database_driver():
    imports = ast.parse(SOURCE.read_text(encoding="utf-8")).body
    direct_modules = set()
    for node in imports:
        if isinstance(node, ast.Import):
            direct_modules.update(alias.name for alias in node.names)
    assert "psycopg" not in direct_modules
    assert "psycopg2" not in direct_modules


def test_import_export_bridges_plan_all_table_transfer_sql_in_infrastructure():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "DB")
    for name in ("Importation_table", "Importation_table_reseau", "Exportation_vers_base_defaut"):
        fn = next(node for node in cls.body
                  if isinstance(node, ast.FunctionDef) and node.name == name)
        helper_calls = {
            node.func.id for node in ast.walk(fn)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "legacy_select_all_query" in helper_calls
        assert "plan_legacy_table_transfer" in helper_calls
        if name == "Importation_table_reseau":
            assert "legacy_mysql_columns_query" in helper_calls


def test_importation_table_rejects_unsafe_table_name_before_select():
    source = _MySqlSourceConnection()
    destination = sqlite3.connect(":memory:")
    try:
        method = _legacy_method(
            "Importation_table",
            GetConnexionReseau=lambda _: (source, "source_tdata"),
        )
        adapter = SimpleNamespace(
            cursor=destination.cursor(), connexion=destination, isNetwork=False
        )
        import pytest
        with pytest.raises(ValueError, match="Invalid legacy SQL identifier"):
            method(adapter, "demo; DROP TABLE personnel",
                   nomFichierdefault="legacy-ref", mode="network")
        assert source.cursor_object.executed == ["USE \x60source_tdata\x60;"]
    finally:
        destination.close()
