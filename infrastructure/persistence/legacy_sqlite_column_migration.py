"""SQLite column removal with a reversible, nested savepoint boundary.

The historical table-copy approach is preserved, including its known loss
of constraints and indexes that are not reconstructed. This helper improves
failure atomicity; it does not make legacy schema reconstruction lossless.
"""
from __future__ import annotations

from collections.abc import Iterable

from infrastructure.persistence.legacy_table_transfer import legacy_sql_identifier
from infrastructure.persistence.legacy_table_ddl import _legacy_type


_SAVEPOINT = "teamworks_legacy_drop_column"


def drop_legacy_sqlite_column(
    cursor: object, table: str, column: str, existing_columns: Iterable[tuple[str, str]],
) -> bool:
    """Drop one SQLite column atomically; return False for historical no-ops.

    A SAVEPOINT avoids ending any surrounding caller-managed transaction.
    Failed reconstruction rolls back both schema and copied rows. Failure
    exceptions propagate, rather than treating an incomplete copy as success.
    """
    table = legacy_sql_identifier(table)
    column = legacy_sql_identifier(column)
    remaining = []
    found = False
    for name, type_name in existing_columns:
        name = legacy_sql_identifier(name)
        if name == column:
            found = True
            continue
        remaining.append((name, "" if type_name == "" else _legacy_type(type_name, is_network=False)))
    if not found or not remaining:
        return False

    declarations = ", ".join("%s %s" % pair for pair in remaining)
    names = ", ".join(name for name, _ in remaining)
    backup = "%s_backup" % table
    legacy_sql_identifier(backup)
    sql = (
        "CREATE TEMPORARY TABLE %s(%s);" % (backup, declarations),
        "INSERT INTO %s SELECT %s FROM %s;" % (backup, names, table),
        "DROP TABLE %s;" % table,
        "CREATE TABLE %s(%s);" % (table, declarations),
        "INSERT INTO %s SELECT %s FROM %s;" % (table, names, backup),
        "DROP TABLE %s;" % backup,
    )

    cursor.execute("SAVEPOINT %s" % _SAVEPOINT)
    try:
        for statement in sql:
            cursor.execute(statement)
    except BaseException:
        try:
            cursor.execute("ROLLBACK TO SAVEPOINT %s" % _SAVEPOINT)
        finally:
            cursor.execute("RELEASE SAVEPOINT %s" % _SAVEPOINT)
        raise
    cursor.execute("RELEASE SAVEPOINT %s" % _SAVEPOINT)
    return True
