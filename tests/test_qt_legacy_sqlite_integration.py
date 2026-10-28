"""Prove the old GestionDB API delegates to the headless SQLite engine."""

import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.persistence.legacy_connection_lifecycle import (
    close_if_connected,
    commit_if_connected,
)
from infrastructure.persistence.legacy_sqlite_connection import open_legacy_sqlite


SOURCE = Path(__file__).resolve().parents[1] / "teamworks/GestionDB.py"


def _method(name: str, **dependencies):
    module = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    db = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "DB")
    method = next(node for node in db.body if isinstance(node, ast.FunctionDef) and node.name == name)
    context = dict(dependencies)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), "exec"), context)
    return context[name]


def test_read_only_sqlite_open_does_not_create_missing_database(tmp_path):
    opener = _method("OuvertureFichierLocal", open_legacy_sqlite=open_legacy_sqlite)
    database = tmp_path / "missing.dat"
    holder = SimpleNamespace(modeCreation=False)
    opener(holder, str(database))
    assert holder.echec == 1
    assert not database.exists()
    assert not hasattr(holder, "connexion")


def test_explicit_creation_and_commit_through_legacy_api(tmp_path):
    opener = _method("OuvertureFichierLocal", open_legacy_sqlite=open_legacy_sqlite)
    committer = _method("Commit", commit_if_connected=commit_if_connected)
    registry = {17: []}
    closer = _method("Close", close_if_connected=close_if_connected, DICT_CONNEXIONS=registry)
    database = tmp_path / "created.dat"
    holder = SimpleNamespace(modeCreation=True, IDconnexion=17)
    opener(holder, str(database))
    assert holder.echec == 0
    holder.cursor.execute("CREATE TABLE demo (id INTEGER)")
    holder.cursor.execute("INSERT INTO demo VALUES (9)")
    committer(holder)
    closer(holder)
    assert 17 not in registry
    with pytest.raises(sqlite3.ProgrammingError):
        holder.connexion.execute("SELECT 1")
    with sqlite3.connect(database) as check:
        assert check.execute("SELECT id FROM demo").fetchall() == [(9,)]


def test_sqlite_adapter_keeps_legacy_error_reporting_and_status(capsys):
    problem = RuntimeError("simulated connector failure")
    def fail_connection(_name, *, allow_creation):
        assert allow_creation
        raise problem

    opener = _method("OuvertureFichierLocal", open_legacy_sqlite=fail_connection)
    holder = SimpleNamespace(modeCreation=True)
    opener(holder, "broken.dat")
    assert holder.echec == 1
    assert holder.erreur is problem
    assert "simulated connector failure" in capsys.readouterr().out


def test_legacy_close_always_untracks_failed_connection():
    closer = _method("Close", close_if_connected=close_if_connected, DICT_CONNEXIONS={42: ["attempt"]})
    registry = closer.__globals__["DICT_CONNEXIONS"]
    closer(SimpleNamespace(IDconnexion=42))
    assert registry == {}


def test_legacy_committer_keeps_missing_connection_error():
    committer = _method("Commit", commit_if_connected=commit_if_connected)
    with pytest.raises(AttributeError):
        committer(SimpleNamespace())


def test_sqlite_open_and_close_are_delegated_without_inline_driver_calls():
    source = SOURCE.read_text(encoding="utf-8")
    assert "from infrastructure.persistence.legacy_sqlite_connection import open_legacy_sqlite" in source
    assert "from infrastructure.persistence.legacy_connection_lifecycle import commit_if_connected, close_if_connected" in source
    assert "self.connexion = sqlite3.connect(nomFichier)" not in source
    assert "self.connexion.close()" not in source
    for method_name, expected in (
        ("OuvertureFichierLocal", "open_legacy_sqlite"),
        ("Commit", "commit_if_connected"),
        ("Close", "close_if_connected"),
    ):
        module = ast.parse(source)
        db = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "DB")
        method = next(node for node in db.body if isinstance(node, ast.FunctionDef) and node.name == method_name)
        called = {item.func.id for item in ast.walk(method)
                  if isinstance(item, ast.Call) and isinstance(item.func, ast.Name)}
        assert expected in called
