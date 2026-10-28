"""SQLite compatibility checks against actual temporary databases."""

import ast
import sqlite3
from pathlib import Path

import pytest

from infrastructure.persistence.legacy_connection_lifecycle import (
    close_if_connected,
    commit_if_connected,
)
from infrastructure.persistence.legacy_sqlite_connection import open_legacy_sqlite


ROOT = Path(__file__).resolve().parents[1]


def test_missing_local_file_is_not_created_by_read(tmp_path: Path) -> None:
    filename = tmp_path / "absent.dat"
    assert open_legacy_sqlite(filename) is None
    assert not filename.exists()


def test_creation_mode_initializes_sqlite_without_schema_or_commit(tmp_path: Path) -> None:
    filename = tmp_path / "created.dat"
    connection, cursor = open_legacy_sqlite(filename, allow_creation=True)
    try:
        assert filename.is_file()
        assert cursor.execute("SELECT name FROM sqlite_master").fetchall() == []
        cursor.execute("CREATE TABLE sample (n INTEGER)")
        cursor.execute("INSERT INTO sample VALUES (42)")
        assert connection.in_transaction
        assert cursor.execute("SELECT n FROM sample").fetchall() == [(42,)]
        commit_if_connected(connection)
        assert not connection.in_transaction
    finally:
        close_if_connected(connection)
    reopened = sqlite3.connect(filename)
    try:
        assert reopened.execute("SELECT n FROM sample").fetchall() == [(42,)]
    finally:
        reopened.close()


def test_existing_file_is_opened_with_unmodified_sqlite_semantics(tmp_path: Path) -> None:
    filename = tmp_path / "existing.dat"
    sqlite3.connect(filename).close()
    connection, cursor = open_legacy_sqlite(filename)
    try:
        assert cursor.execute("PRAGMA database_list").fetchone()[2] == str(filename)
    finally:
        close_if_connected(connection)


def test_missing_parent_is_never_created_implicitly(tmp_path: Path) -> None:
    filename = tmp_path / "nonexistent" / "test.dat"
    with pytest.raises(sqlite3.OperationalError):
        open_legacy_sqlite(filename, allow_creation=True)
    assert not filename.parent.exists()


def test_cursor_failure_releases_open_connection() -> None:
    events = []

    class BrokenConnection:
        def cursor(self):
            raise RuntimeError("cursor unavailable")

        def close(self):
            events.append("closed")

    with pytest.raises(RuntimeError, match="cursor unavailable"):
        open_legacy_sqlite(":memory:", allow_creation=True, connect=lambda _: BrokenConnection())
    assert events == ["closed"]


def test_lifecycle_preserves_driver_errors_and_never_rolls_back() -> None:
    events = []

    class Fake:
        def commit(self):
            events.append("commit")

        def close(self):
            events.append("close")

        def rollback(self):
            events.append("rollback")

    connection = Fake()
    commit_if_connected(connection)
    close_if_connected(connection)
    commit_if_connected(None)
    close_if_connected(None)
    assert events == ["commit", "close"]

    class Broken:
        def commit(self):
            raise RuntimeError("commit failed")

        def close(self):
            raise RuntimeError("close failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        commit_if_connected(Broken())
    with pytest.raises(RuntimeError, match="close failed"):
        close_if_connected(Broken())


def test_engine_modules_never_import_a_graphical_toolkit() -> None:
    for filename in ("legacy_sqlite_connection.py", "legacy_connection_lifecycle.py"):
        path = ROOT / "infrastructure" / "persistence" / filename
        parsed = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for item in ast.walk(parsed):
            if isinstance(item, ast.Import):
                imports.extend(alias.name for alias in item.names)
            if isinstance(item, ast.ImportFrom):
                imports.append(item.module or "")
        assert not any(x.split(".")[0] in {"wx", "wxPython", "PySide6", "PyQt5", "PyQt6"} for x in imports)
