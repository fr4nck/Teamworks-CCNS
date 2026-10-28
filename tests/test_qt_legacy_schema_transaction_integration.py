"""Qt legacy adapter checks for MySQL schema activation and SQL batch commits."""

import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.persistence.legacy_mysql_schema import activate_legacy_mysql_schema
from infrastructure.persistence.legacy_sql_batch import execute_legacy_batch


SOURCE = Path(__file__).resolve().parents[1] / "teamworks/GestionDB.py"


def _extract(name, *, method=True, **dependencies):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    parent = next(n for n in tree.body
                  if isinstance(n, ast.ClassDef) and n.name == "DB") if method else tree
    fn = next(n for n in parent.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = dict(dependencies)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace[name]


def _open_network(*, name="sport_tdata", create=False):
    statements = []

    class Cursor:
        def execute(self, sql):
            statements.append(sql)

    cursor = Cursor()

    class Connection:
        def cursor(self):
            return cursor

    opener = _extract(
        "OuvertureFichierReseau",
        GetConnexionReseau=lambda _: (Connection(), name),
        activate_legacy_mysql_schema=activate_legacy_mysql_schema,
        UTILS_MySQL=SimpleNamespace(ConsommerDiagnosticConnexion=lambda err: None),
    )
    adapter = SimpleNamespace(modeCreation=create)
    opener(adapter, "legacy-reference", "TDATA")
    return statements, adapter


def test_legacy_mysql_opener_selects_schema_without_creation():
    sql, adapter = _open_network()
    assert adapter.echec == 0
    assert sql == ["USE \x60sport_tdata\x60;"]


def test_legacy_mysql_opener_creates_schema_before_selection():
    sql, adapter = _open_network(create=True)
    assert adapter.echec == 0
    assert sql == [
        "CREATE DATABASE IF NOT EXISTS \x60sport_tdata\x60 CHARSET utf8 COLLATE utf8_unicode_ci;",
        "USE \x60sport_tdata\x60;",
    ]


def test_legacy_mysql_opener_preserves_tdata_sentinel():
    sql, adapter = _open_network(name="_tdata")
    assert adapter.echec == 0
    assert sql == []


def test_legacy_mysql_opener_rejects_unsafe_schema_before_sql(capsys):
    sql, adapter = _open_network(name="rh;DROP DATABASE prod", create=True)
    assert sql == []
    assert adapter.echec == 1
    assert isinstance(adapter.erreur, ValueError)
    assert "DROP" not in capsys.readouterr().out


@pytest.mark.parametrize("network,query,expected", [
    (True, "INSERT INTO demo VALUES (?)", "INSERT INTO demo VALUES (%s)"),
    (False, "INSERT INTO demo VALUES (%s)", "INSERT INTO demo VALUES (?)"),
])
def test_legacy_batch_reuses_engine_commit_boundary(network, query, expected):
    history = []

    class Cursor:
        def executemany(self, sql, rows):
            history.append(("execute", sql, rows))

    class Connection:
        def commit(self):
            history.append(("commit",))

    execute = _extract("Executermany", execute_legacy_batch=execute_legacy_batch)
    adapter = SimpleNamespace(cursor=Cursor(), connexion=Connection(), isNetwork=network)
    assert execute(adapter, query, [(3,)], commit=True) is None
    assert history == [("execute", expected, [(3,)]), ("commit",)]


def test_legacy_batch_does_not_commit_when_disabled():
    history = []

    class Cursor:
        def executemany(self, *_):
            history.append("execute")

    class Connection:
        def commit(self):
            history.append("commit")

    execute = _extract("Executermany", execute_legacy_batch=execute_legacy_batch)
    adapter = SimpleNamespace(cursor=Cursor(), connexion=Connection(), isNetwork=True)
    execute(adapter, "INSERT INTO demo VALUES (?)", [(4,)], commit=False)
    assert history == ["execute"]


def test_legacy_batch_sqlite_rollback_still_belongs_to_caller():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE demo (n INTEGER)")
        execute = _extract("Executermany", execute_legacy_batch=execute_legacy_batch)
        adapter = SimpleNamespace(
            cursor=connection.cursor(), connexion=connection, isNetwork=False
        )
        execute(adapter, "INSERT INTO demo VALUES (%s)", [(7,), (8,)], commit=False)
        assert connection.in_transaction
        assert connection.execute("SELECT n FROM demo").fetchall() == [(7,), (8,)]
        connection.rollback()
        assert connection.execute("SELECT n FROM demo").fetchall() == []
    finally:
        connection.close()


def test_legacy_mysql_probe_uses_common_schema_selection():
    method = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(n for n in method.body if isinstance(n, ast.FunctionDef)
              and n.name == "TestConnexionMySQL")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name)
             and n.func.id == "activate_legacy_mysql_schema"]
    assert len(calls) == 1
    assert len(calls[0].args) == 2
    assert not calls[0].keywords


def test_schema_and_batch_bridges_call_engine_without_inline_sql():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    db = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "DB")
    for method, expected in (
        ("OuvertureFichierReseau", "activate_legacy_mysql_schema"),
        ("Executermany", "execute_legacy_batch"),
    ):
        fn = next(n for n in db.body if isinstance(n, ast.FunctionDef)
                  and n.name == method)
        functions = [n.func.id for n in ast.walk(fn)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        assert functions.count(expected) == 1
