"""Adaptateur d'inventaire pour une base MySQL historique, en lecture seule.

L'adaptateur reçoit une connexion déjà ouverte (DB-API 2.0 : .cursor(),
.execute(sql, params), .fetchone(), .fetchall()) : il n'importe donc pas
mysql-connector-python au niveau du module, ce qui le rend testable avec
un simple double de connexion, sans dépendance réseau ni paquet
supplémentaire. La fonction connect_mysql() ci-dessous, elle, importe
mysql-connector-python à l'appel : c'est la seule porte d'entrée qui a
besoin de ce paquet, déjà une dépendance historique du dépôt
(requirements/python311-core.txt).
"""

from __future__ import annotations

from typing import Iterator, Protocol

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
    return "`" + name.replace("`", "``") + "`"


class _DbApiCursor(Protocol):
    def execute(self, sql: str, params: tuple = ()) -> object: ...
    def fetchone(self) -> tuple | None: ...
    def fetchall(self) -> list[tuple]: ...


class _DbApiConnection(Protocol):
    def cursor(self) -> _DbApiCursor: ...


def connect_mysql(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    charset: str = "utf8mb4",
    connection_timeout: int = 10,
) -> _DbApiConnection:
    """Ouvre une connexion MySQL en lecture seule via mysql-connector-python.

    Importé à l'appel uniquement : les adaptateurs et leurs tests ne
    dépendent pas de mysql-connector-python tant que cette fonction n'est
    pas invoquée.
    """
    import mysql.connector

    connection = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset=charset,
        connection_timeout=connection_timeout,
        use_pure=True,
    )
    connection.start_transaction(readonly=True)
    return connection


class MySqlLegacyDatabasePort:
    """Implémentation MySQL du port LegacyDatabasePort.

    Prend une connexion DB-API 2.0 déjà ouverte : voir connect_mysql()
    pour l'ouvrir réellement, ou un double de test pour les tests
    unitaires sans réseau.
    """

    engine_name = "mysql"

    def __init__(
        self,
        connection: _DbApiConnection,
        *,
        database: str,
        source_label: str,
        engine_version: str | None = None,
    ) -> None:
        self._connection = connection
        self._database = database
        self.source_label = source_label
        self.engine_version = engine_version or self._read_version()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "MySqlLegacyDatabasePort":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _execute(self, sql: str, params: tuple = ()) -> _DbApiCursor:
        cursor = self._connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def _read_version(self) -> str:
        cursor = self._execute("SELECT VERSION()")
        row = cursor.fetchone()
        return str(row[0]) if row else "inconnue"

    def list_tables(self) -> tuple[str, ...]:
        cursor = self._execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' "
            "ORDER BY TABLE_NAME",
            (self._database,),
        )
        return tuple(row[0] for row in cursor.fetchall())

    def row_count(self, table: str) -> int:
        sql = build_row_count_sql(table=table, quote=quote_identifier)
        return self._execute(sql).fetchone()[0]

    def column_definitions(self, table: str) -> tuple[ColumnDefinition, ...]:
        cursor = self._execute(
            "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY "
            "FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
            "ORDER BY ORDINAL_POSITION",
            (self._database, table),
        )
        return tuple(
            ColumnDefinition(
                name=row[0],
                declared_type=row[1] or "",
                nullable=(row[2] == "YES"),
                is_primary_key=(row[3] == "PRI"),
            )
            for row in cursor.fetchall()
        )

    def column_stats(
        self, table: str, column: ColumnDefinition, *, sample_limit: int
    ) -> ColumnStats:
        stats_sql = build_column_stats_sql(table=table, column=column, quote=quote_identifier)
        row = self._execute(stats_sql).fetchone()
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
            samples = tuple(str(item[0]) for item in self._execute(sample_sql).fetchall())

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
        return self._execute(sql).fetchone()[0] or 0

    def rows_without_usable_key(self, table: str, key_columns: tuple[str, ...]) -> int:
        sql = build_missing_key_sql(table=table, key_columns=key_columns, quote=quote_identifier)
        return self._execute(sql).fetchone()[0] or 0

    def fetch_rows(
        self, table: str, columns: tuple[str, ...]
    ) -> Iterator[tuple[object, ...]]:
        sql = build_select_rows_sql(table=table, columns=columns, quote=quote_identifier)
        cursor = self._execute(sql)
        for row in cursor.fetchall():
            yield tuple(row)
