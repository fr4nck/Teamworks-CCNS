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

import re
from typing import Iterable, Iterator, Protocol

from domain.migration.inventory_model import ColumnDefinition, ColumnKind, ColumnStats
from infrastructure.persistence.legacy_inventory_sql import (
    build_column_stats_sql,
    build_duplicate_key_sql,
    build_missing_key_sql,
    build_row_count_sql,
    build_sample_values_sql,
    build_select_rows_sql,
)

# start_transaction(readonly=True) n'existe côté serveur qu'à partir de
# MySQL 5.6.5 (RESET TRANSACTION / READ ONLY). En dessous, Connector/Python
# lève une erreur si on l'utilise : il faut une autre garantie de lecture
# seule. Voir docs/68-inventaire-legacy-database.md pour le détail de la
# stratégie et son statut de qualification (MySQL 5.5 réel NON QUALIFIÉ).
READONLY_TRANSACTION_MIN_VERSION: tuple[int, int, int] = (5, 6, 5)

# Seuls des privilèges strictement en lecture sont acceptés pour un serveur
# trop ancien pour start_transaction(readonly=True). USAGE est le
# "privilège nul" que MySQL attribue par défaut ; il n'autorise aucune
# opération.
_READ_ONLY_GRANT_PRIVILEGES = frozenset({"SELECT", "USAGE"})


def quote_identifier(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


class _DbApiCursor(Protocol):
    def execute(self, sql: str, params: tuple = ()) -> object: ...
    def fetchone(self) -> tuple | None: ...
    def fetchall(self) -> list[tuple]: ...


class _DbApiConnection(Protocol):
    def cursor(self) -> _DbApiCursor: ...


class MySqlReadOnlyGuaranteeError(RuntimeError):
    """La lecture seule ne peut pas être garantie automatiquement.

    Levée plutôt que de tenter silencieusement une connexion en écriture
    potentielle sur un serveur MySQL trop ancien pour
    start_transaction(readonly=True).
    """


def parse_mysql_version(version_string: str) -> tuple[int, int, int]:
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version_string or "")
    if not match:
        raise MySqlReadOnlyGuaranteeError(
            f"Version MySQL non interprétable ({version_string!r}) : "
            "impossible de choisir une stratégie de lecture seule."
        )
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def supports_readonly_transaction(version: tuple[int, int, int]) -> bool:
    return version >= READONLY_TRANSACTION_MIN_VERSION


def _grant_privileges(grant_statement: str) -> tuple[str, ...]:
    match = re.match(r"\s*GRANT\s+(.+?)\s+ON\s+", grant_statement or "", re.IGNORECASE)
    if not match:
        return ()
    return tuple(part.strip().upper() for part in match.group(1).split(",") if part.strip())


def ensure_select_only_account(grants: Iterable[str]) -> None:
    """Vérifie que le compte connecté n'a aucun privilège d'écriture.

    Seul recours pour un serveur antérieur à MySQL 5.6.5, où aucune
    transaction en lecture seule ne peut être demandée au serveur : c'est
    au compte SQL lui-même de ne pouvoir qu'exécuter des SELECT.
    """
    grants = tuple(grants)
    if not grants:
        raise MySqlReadOnlyGuaranteeError(
            "Aucun droit lisible pour le compte MySQL connecté : impossible "
            "de garantir la lecture seule sur un serveur antérieur à "
            "MySQL 5.6.5. Un compte strictement SELECT-only est requis."
        )
    for grant_statement in grants:
        privileges = _grant_privileges(grant_statement)
        if not privileges:
            raise MySqlReadOnlyGuaranteeError(
                f"Droits MySQL illisibles ({grant_statement!r}) : un compte "
                "strictement SELECT-only est requis pour un serveur "
                "antérieur à MySQL 5.6.5."
            )
        unexpected = [p for p in privileges if p not in _READ_ONLY_GRANT_PRIVILEGES]
        if unexpected:
            raise MySqlReadOnlyGuaranteeError(
                "Le compte MySQL connecté dispose de privilèges d'écriture "
                f"({', '.join(unexpected)}) alors que le serveur est "
                "antérieur à MySQL 5.6.5 et ne supporte pas "
                "start_transaction(readonly=True). Un compte strictement "
                "SELECT-only est requis pour cette version de serveur."
            )


def negotiate_read_only_mode(connection: object, *, version_string: str) -> None:
    """Choisit et applique la stratégie de lecture seule selon la version serveur.

    >= 5.6.5 : transaction readonly=True, supportée nativement.
    < 5.6.5 : aucune commande DDL/DML n'est jamais émise par cet adaptateur,
    mais ce n'est pas une garantie automatique suffisante à elle seule ; on
    vérifie donc que le compte connecté n'a que des privilèges SELECT.
    Si cela ne peut pas être vérifié, la connexion échoue explicitement
    plutôt que de continuer sur une hypothèse non garantie.
    """
    version = parse_mysql_version(version_string)
    if supports_readonly_transaction(version):
        connection.start_transaction(readonly=True)
        return

    try:
        cursor = connection.cursor()
        cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
        grants = [row[0] for row in cursor.fetchall()]
    except MySqlReadOnlyGuaranteeError:
        raise
    except Exception as exc:
        raise MySqlReadOnlyGuaranteeError(
            "Impossible de lire les droits du compte MySQL connecté "
            f"({exc}) sur un serveur {version_string} antérieur à "
            "MySQL 5.6.5. Un compte strictement SELECT-only est requis "
            "pour garantir la lecture seule."
        ) from exc

    ensure_select_only_account(grants)


def _read_server_version(connection: object) -> str:
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    row = cursor.fetchone()
    return str(row[0]) if row else ""


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
    """Ouvre une connexion MySQL et négocie une garantie de lecture seule.

    Importé à l'appel uniquement : les adaptateurs et leurs tests ne
    dépendent pas de mysql-connector-python tant que cette fonction n'est
    pas invoquée.

    Détecte la version réelle du serveur avant de choisir le mode
    transactionnel (voir negotiate_read_only_mode) : aucune hypothèse
    implicite que readonly=True fonctionne partout. Si la lecture seule ne
    peut pas être garantie, la connexion est fermée et une
    MySqlReadOnlyGuaranteeError explicite est levée — jamais une tentative
    d'écriture « pour tester ».
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
    try:
        version_string = _read_server_version(connection)
        negotiate_read_only_mode(connection, version_string=version_string)
    except Exception:
        connection.close()
        raise
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
