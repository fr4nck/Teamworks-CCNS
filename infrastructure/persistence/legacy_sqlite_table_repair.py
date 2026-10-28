"""Non-destructive repair of legacy SQLite table columns.

Only safe, additive catalogue columns are repaired. Existing columns, rows,
indexes, triggers, views, foreign keys and constraints are never rebuilt.
A type/primary-key mismatch or missing table needs a separately reviewed
migration rather than a destructive automatic reconstruction.
"""
from __future__ import annotations

from collections.abc import Iterable

from infrastructure.persistence.legacy_table_ddl import (
    _legacy_type,
    legacy_add_column_query,
)
from infrastructure.persistence.legacy_table_transfer import legacy_sql_identifier


_SAVEPOINT = "teamworks_legacy_repair_table"


def _normalized_type(declaration: str) -> str:
    """Compare SQLite column affinity declarations, not textual whitespace."""
    return " ".join(declaration.upper().split())


def repair_legacy_sqlite_table(
    cursor: object,
    table: str,
    descriptors: Iterable[tuple[str, str] | tuple],
) -> tuple[str, ...]:
    """Add missing ordinary catalogue columns without recreating the table.

    Preflight rejects missing tables, duplicate names, incompatible existing
    types, absent/mismatched primary keys and unsupported new constraints.
    The complete set of ALTER TABLE ADD COLUMN statements runs under one
    SAVEPOINT. On failure no partial schema change is retained, and any
    enclosing transaction remains under the caller's control.

    Returns the names of the columns actually added (empty tuple if none).
    Extra historical columns remain intact, by design.
    """
    table = legacy_sql_identifier(table)
    requested: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in descriptors:
        if len(item) < 2:
            raise ValueError("Incomplete legacy column description")
        name = legacy_sql_identifier(item[0])
        key = name.casefold()
        if key in seen:
            raise ValueError("Duplicate legacy column name")
        seen.add(key)
        declaration = _legacy_type(item[1], is_network=False)
        requested.append((name, declaration))
    if not requested:
        raise ValueError("Legacy table catalogue is empty")

    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    row = cursor.fetchone()
    if not row or not isinstance(row[0], str):
        raise ValueError("Legacy SQLite table is missing")
    if row[0].lstrip().upper().startswith("CREATE VIRTUAL TABLE"):
        raise ValueError("Virtual SQLite table requires a dedicated migration")

    cursor.execute('PRAGMA table_xinfo("%s")' % table)
    current = {
        str(item[1]).casefold(): item
        for item in cursor.fetchall()
    }
    if not current:
        raise ValueError("SQLite table metadata unavailable")

    missing: list[tuple[str, str]] = []
    for name, declaration in requested:
        found = current.get(name.casefold())
        is_pk = " PRIMARY KEY" in (" " + declaration.upper())
        if found is None:
            # SQLite cannot add an autoincrement / primary-key field using
            # ALTER TABLE. Do not silently replace it by a nullable column.
            if is_pk or " UNIQUE" in (" " + declaration.upper()):
                raise ValueError("A new key requires a dedicated migration")
            missing.append((name, declaration))
            continue

        actual_type = _normalized_type(str(found[2]))
        expected_type = _normalized_type(declaration.split(" PRIMARY KEY")[0])
        actual_pk = bool(found[5])
        if actual_type != expected_type or actual_pk != is_pk:
            raise ValueError("Existing SQLite column definition differs")
        if is_pk and "AUTOINCREMENT" in declaration.upper():
            if "AUTOINCREMENT" not in row[0].upper():
                raise ValueError("Existing SQLite autoincrement definition differs")
        # Avoid accidentally treating hidden/generated columns as ordinary
        # writable catalogue columns.
        if len(found) > 6 and found[6]:
            raise ValueError("Generated SQLite column requires a dedicated migration")

    if not missing:
        return ()

    # All schema validation completes before the first schema mutation.
    statements = [
        legacy_add_column_query(table, name, declaration)
        for name, declaration in missing
    ]
    cursor.execute("SAVEPOINT %s" % _SAVEPOINT)
    try:
        for statement in statements:
            cursor.execute(statement)
    except BaseException:
        try:
            cursor.execute("ROLLBACK TO SAVEPOINT %s" % _SAVEPOINT)
        finally:
            cursor.execute("RELEASE SAVEPOINT %s" % _SAVEPOINT)
        raise
    cursor.execute("RELEASE SAVEPOINT %s" % _SAVEPOINT)
    return tuple(name for name, _ in missing)
