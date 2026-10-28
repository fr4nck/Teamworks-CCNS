"""Regression tests for explicit SQL batch transaction boundaries."""

import sqlite3
from pathlib import Path

import pytest

from infrastructure.persistence.legacy_sql_batch import (
    execute_legacy_batch,
    legacy_batch_query,
)


def test_mysql_batch_rewrites_question_placeholders_and_commits_once():
    events = []

    class Cursor:
        def executemany(self, sql, rows):
            events.append(("many", sql, list(rows)))

    class Connection:
        def commit(self):
            events.append(("commit",))

        def rollback(self):
            pytest.fail("Unexpected implicit rollback")

    execute_legacy_batch(
        Cursor(), Connection(), "INSERT INTO demo VALUES (?, ?)",
        [(1, "a"), (2, "b")], is_network=True,
    )
    assert events == [
        ("many", "INSERT INTO demo VALUES (%s, %s)", [(1, "a"), (2, "b")]),
        ("commit",),
    ]


def test_mysql_batch_defers_commit_when_disabled():
    events = []

    class Cursor:
        def executemany(self, sql, rows):
            events.append((sql, list(rows)))

    class Connection:
        def commit(self):
            pytest.fail("Commit must remain disabled")

    execute_legacy_batch(
        Cursor(), Connection(), "INSERT INTO demo VALUES (?)",
        [(4,), (5,)], is_network=True, commit=False,
    )
    assert events == [("INSERT INTO demo VALUES (%s)", [(4,), (5,)])]


def test_sqlite_batch_can_defer_commit_and_rollback_on_explicit_request():
    db = sqlite3.connect(":memory:")
    try:
        db.execute("CREATE TABLE demo (id INTEGER)")
        execute_legacy_batch(
            db.cursor(), db, "INSERT INTO demo VALUES (%s)",
            [(10,), (20,)], is_network=False, commit=False,
        )
        assert db.in_transaction
        assert db.execute("SELECT id FROM demo").fetchall() == [(10,), (20,)]
        db.rollback()
        assert db.execute("SELECT id FROM demo").fetchall() == []
    finally:
        db.close()


def test_sqlite_batch_default_commit_is_durable(tmp_path: Path):
    path = tmp_path / "transactions.sqlite"
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE demo (id INTEGER)")
        execute_legacy_batch(
            db.cursor(), db, "INSERT INTO demo VALUES (%s)",
            [(4,), (5,)], is_network=False,
        )
        assert not db.in_transaction
    finally:
        db.close()
    with sqlite3.connect(path) as reopened:
        assert reopened.execute("SELECT id FROM demo").fetchall() == [(4,), (5,)]


def test_batch_failure_does_not_commit_or_rollback_implicitly():
    events = []

    class Cursor:
        def executemany(self, *_):
            events.append("execute")
            raise ValueError("SQL failure")

    class Connection:
        def commit(self):
            events.append("commit")

        def rollback(self):
            events.append("rollback")

    with pytest.raises(ValueError, match="SQL failure"):
        execute_legacy_batch(
            Cursor(), Connection(), "INSERT INTO demo VALUES (?)",
            [(1,)], is_network=True,
        )
    assert events == ["execute"]


def test_batch_placeholder_replacement_preserves_legacy_semantics():
    assert legacy_batch_query("SELECT %s, ?", is_network=True) == "SELECT %s, %s"
    assert legacy_batch_query("SELECT %s, ?", is_network=False) == "SELECT ?, ?"


def test_batch_commit_one_is_backwards_compatible_with_true():
    events = []

    class Cursor:
        def executemany(self, *_):
            events.append("execute")

    class Connection:
        def commit(self):
            events.append("commit")

    execute_legacy_batch(
        Cursor(), Connection(), "SELECT 1", (), is_network=False, commit=1,
    )
    assert events == ["execute", "commit"]
