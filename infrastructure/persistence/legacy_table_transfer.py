"""Compile legacy Teamworks table-copy SQL outside the GUI compatibility layer.

Only the historic SQLite (?) and MySQL (%s) placeholder conventions are
supported. This is not a PostgreSQL dialect adapter: an eventual migration
must provide its own reviewed SQL compiler and migrations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")


def _identifier(name: str) -> str:
    """Accept the identifiers in DATA_Tables without interpolating SQL input."""
    if not isinstance(name, str) or _IDENTIFIER.fullmatch(name) is None:
        raise ValueError("Invalid legacy SQL identifier")
    return name


def legacy_select_all_query(table: str) -> str:
    """Keep the historical SELECT-* spelling for source table discovery."""
    return "SELECT * FROM %s" % _identifier(table)


def legacy_mysql_columns_query(table: str) -> str:
    """Keep the historical MySQL SHOW-COLUMNS spelling for imports."""
    return "SHOW COLUMNS FROM %s;" % _identifier(table)


@dataclass(frozen=True)
class LegacyTableTransferPlan:
    """SQL and projected column order for one historical table copy."""

    columns: tuple[str, ...]
    select_query: str
    insert_query: str


def plan_legacy_table_transfer(
    table: str,
    source_columns: Iterable[str],
    *,
    destination_is_network: bool,
    destination_columns: Iterable[str] | None = None,
) -> LegacyTableTransferPlan:
    """Build matching source SELECT and destination INSERT statements.

    Preserve source column order. When destination_columns is specified,
    ignore source columns absent in the destination, as GestionDB always did.
    SQL construction has no connection, transaction, driver or GUI side effect.
    """
    table = _identifier(table)
    allowed = set(destination_columns) if destination_columns is not None else None
    columns = tuple(
        _identifier(column)
        for column in source_columns
        if allowed is None or column in allowed
    )
    if not columns:
        raise ValueError("No compatible legacy table columns")
    names = ", ".join(columns)
    marks = ", ".join(("%s" if destination_is_network else "?") for _ in columns)
    return LegacyTableTransferPlan(
        columns=columns,
        select_query="SELECT %s FROM %s" % (names, table),
        insert_query="INSERT INTO %s (%s) VALUES (%s)" % (table, names, marks),
    )


def legacy_sql_identifier(name: str) -> str:
    """Public, stable validator shared by legacy table-copy and DDL adapters."""
    return _identifier(name)
