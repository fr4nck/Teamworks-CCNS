"""Adaptateur d'inventaire pour une base SQLite historique, en lecture seule.

N'utilise pas GestionDB : GestionDB mélange accès disque, configuration
applicative et, dans certains chemins, l'UI wx. Cet adaptateur reste un
lecteur minimal, jamais destiné à écrire.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from domain.migration.inventory_model import ColumnDefinition, ColumnKind, ColumnStats
from infrastructure.persistence.legacy_inventory_sql import (
    build_column_stats_sql,
    build_duplicate_key_sql,
    build_missing_key_sql,
    build_row_count_sql,
    build_sample_values_sql,
    build_select_rows_sql,
)


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def connect_sqlite_readonly(path: str | Path) -> sqlite3.Connection:
    """Ouvre une connexion SQLite strictement en lecture seule.

    Utilise le même motif d'URI `mode=ro` que tools/diagnostic_installation.py.
    """
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Base SQLite introuvable : {resolved}")
    uri = f"file:{resolved.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.execute("PRAGMA query_only = ON")
    return connection


class SqliteLegacyDatabasePort:
    """Implémentation SQLite du port LegacyDatabasePort."""

    engine_name = "sqlite"

    def __init__(self, connection: sqlite3.Connection, *, source_label: str) -> None:
        self._connection = connection
        self.source_label = source_label
        self.engine_version = sqlite3.sqlite_version

    @classmethod
    def from_path(cls, path: str | Path) -> "SqliteLegacyDatabasePort":
        connection = connect_sqlite_readonly(path)
        return cls(connection, source_label=str(Path(path)))

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SqliteLegacyDatabasePort":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def list_tables(self) -> tuple[str, ...]:
        rows = self._connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()
        return tuple(row[0] for row in rows)

    def row_count(self, table: str) -> int:
        sql = build_row_count_sql(table=table, quote=quote_identifier)
        return self._connection.execute(sql).fetchone()[0]

    def column_definitions(self, table: str) -> tuple[ColumnDefinition, ...]:
        rows = self._connection.execute(
            f"PRAGMA table_info({quote_identifier(table)})"
        ).fetchall()
        # PRAGMA table_info -> (cid, name, type, notnull, dflt_value, pk)
        return tuple(
            ColumnDefinition(
                name=row[1],
                declared_type=row[2] or "",
                nullable=not bool(row[3]),
                is_primary_key=bool(row[5]),
            )
            for row in rows
        )

    def column_stats(
        self, table: str, column: ColumnDefinition, *, sample_limit: int
    ) -> ColumnStats:
        stats_sql = build_column_stats_sql(table=table, column=column, quote=quote_identifier)
        row = self._connection.execute(stats_sql).fetchone()
        (
            row_count,
            null_count,
            empty_count,
            min_len,
            max_len,
            zero_count,
            min_num,
            max_num,
            min_date,
            max_date,
            distinct_count,
        ) = row

        samples: tuple[str, ...] = ()
        if sample_limit > 0 and column.kind is not ColumnKind.BLOB:
            sample_sql = build_sample_values_sql(
                table=table, column=column, quote=quote_identifier, limit=sample_limit
            )
            samples = tuple(
                str(item[0]) for item in self._connection.execute(sample_sql).fetchall()
            )

        return ColumnStats(
            column=column,
            row_count=row_count or 0,
            null_count=null_count or 0,
            empty_string_count=empty_count or 0,
            zero_count=zero_count or 0,
            distinct_count=distinct_count,
            min_text_length=min_len,
            max_text_length=max_len,
            min_numeric=str(min_num) if min_num is not None else None,
            max_numeric=str(max_num) if max_num is not None else None,
            min_date=str(min_date) if min_date is not None else None,
            max_date=str(max_date) if max_date is not None else None,
            sample_values=samples,
        )

    def duplicate_key_row_count(self, table: str, key_columns: tuple[str, ...]) -> int:
        sql = build_duplicate_key_sql(table=table, key_columns=key_columns, quote=quote_identifier)
        return self._connection.execute(sql).fetchone()[0] or 0

    def rows_without_usable_key(self, table: str, key_columns: tuple[str, ...]) -> int:
        sql = build_missing_key_sql(table=table, key_columns=key_columns, quote=quote_identifier)
        return self._connection.execute(sql).fetchone()[0] or 0

    def fetch_rows(
        self, table: str, columns: tuple[str, ...]
    ) -> Iterator[tuple[object, ...]]:
        sql = build_select_rows_sql(table=table, columns=columns, quote=quote_identifier)
        for row in self._connection.execute(sql):
            yield tuple(row)
