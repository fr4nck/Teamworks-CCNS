"""Lossless SQLite column removal using native ALTER TABLE DROP COLUMN.

SQLite 3.35+ preserves unrelated indexes, triggers, views, keys and table
constraints, and refuses to drop columns referenced by those schema objects.
Earlier versions fail closed: the old CREATE/COPY/DROP reconstruction would
silently discard schema constraints and is deliberately not used.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from infrastructure.persistence.legacy_table_transfer import legacy_sql_identifier


_SAVEPOINT = "teamworks_legacy_drop_column"
_MIN_NATIVE_DROP = (3, 35, 0)


def drop_legacy_sqlite_column(
    cursor: object,
    table: str,
    column: str,
    existing_columns: Iterable[tuple[str, str]],
) -> bool:
    """Drop one column atomically, keeping the surrounding transaction intact.

    Return False without any SQL for an unknown column or sole remaining
    column. SQLite rejects referenced/PK/UNIQUE/CHECK/FK/generated columns
    without modifying the schema. ROLLBACK TO undoes failed DDL inside the
    savepoint; RELEASE of a nested savepoint never commits its parent.
    """
    table = legacy_sql_identifier(table)
    column = legacy_sql_identifier(column)
    names = [legacy_sql_identifier(name) for name, _type in existing_columns]
    if column not in names or len(names) <= 1:
        return False

    # Native DROP COLUMN is available from SQLite 3.35 (2021). Do not
    # silently fall back to a destructive custom rebuild on older runtimes.
    if sqlite3.sqlite_version_info < _MIN_NATIVE_DROP:
        raise RuntimeError("SQLite 3.35 or newer is required for safe DROP COLUMN")

    cursor.execute("SAVEPOINT %s" % _SAVEPOINT)
    try:
        cursor.execute("ALTER TABLE %s DROP COLUMN %s;" % (table, column))
    except BaseException:
        try:
            cursor.execute("ROLLBACK TO SAVEPOINT %s" % _SAVEPOINT)
        finally:
            cursor.execute("RELEASE SAVEPOINT %s" % _SAVEPOINT)
        raise
    cursor.execute("RELEASE SAVEPOINT %s" % _SAVEPOINT)
    return True
