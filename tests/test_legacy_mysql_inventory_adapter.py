"""Tests de l'adaptateur MySQL via un double de connexion DB-API 2.0.

Aucun serveur MySQL réel n'est nécessaire : MySqlLegacyDatabasePort ne
dépend que d'un objet connexion minimal (.cursor()/.execute()/.fetch*),
ce que mysql-connector-python fournit en production et ce double fournit
ici. mysql-connector-python n'a donc pas besoin d'être installé pour
exécuter ces tests.
"""

from domain.migration.inventory_model import ColumnDefinition
from infrastructure.persistence.legacy_mysql_inventory_adapter import (
    MySqlLegacyDatabasePort,
    quote_identifier,
)


class _FakeCursor:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list[tuple[str, tuple]] = []
        self._last = None

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        self._last = self._responses.pop(0)

    def fetchone(self):
        return self._last

    def fetchall(self):
        return self._last


class _FakeConnection:
    def __init__(self, responses):
        self._cursor = _FakeCursor(responses)
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


def _port(responses, *, database="teamworks"):
    connection = _FakeConnection(responses)
    port = MySqlLegacyDatabasePort(
        connection, database=database, source_label="mysql://test", engine_version="8.0.39"
    )
    return port, connection


def test_quote_identifier_escapes_backticks():
    assert quote_identifier("deplacements") == "`deplacements`"
    assert quote_identifier("weird`name") == "`weird``name`"


def test_engine_version_is_read_when_not_provided():
    connection = _FakeConnection([(("8.0.39",))])
    port = MySqlLegacyDatabasePort(connection, database="teamworks", source_label="mysql://test")

    assert port.engine_version == "8.0.39"


def test_list_tables_queries_information_schema_with_database_param():
    port, connection = _port([[("deplacements",), ("remboursements",)]])

    tables = port.list_tables()

    assert tables == ("deplacements", "remboursements")
    sql, params = connection._cursor.calls[0]
    assert "INFORMATION_SCHEMA.TABLES" in sql
    assert params == ("teamworks",)


def test_row_count_returns_scalar():
    port, connection = _port([(3,)])

    assert port.row_count("deplacements") == 3
    sql, _ = connection._cursor.calls[0]
    assert "`deplacements`" in sql


def test_column_definitions_maps_primary_key_flag():
    responses = [
        [
            ("IDdeplacement", "int(11)", "NO", "PRI"),
            ("IDpersonne", "int(11)", "YES", ""),
        ]
    ]
    port, connection = _port(responses)

    columns = port.column_definitions("deplacements")

    assert columns[0] == ColumnDefinition(
        name="IDdeplacement", declared_type="int(11)", nullable=False, is_primary_key=True
    )
    assert columns[1].is_primary_key is False
    sql, params = connection._cursor.calls[0]
    assert params == ("teamworks", "deplacements")


def test_column_stats_skips_sample_query_for_blob_columns():
    column = ColumnDefinition(name="piece", declared_type="blob", nullable=True)
    responses = [(5, 1, 0, None, None, 0, None, None, None, None, None)]
    port, connection = _port(responses)

    stats = port.column_stats("documents", column, sample_limit=3)

    assert stats.row_count == 5
    assert stats.null_count == 1
    assert stats.sample_values == ()
    assert len(connection._cursor.calls) == 1


def test_column_stats_fetches_samples_for_text_columns():
    column = ColumnDefinition(name="objet", declared_type="varchar(100)", nullable=True)
    responses = [
        (3, 0, 0, 2, 8, 0, None, None, None, None, 2),
        [("Réunion",), ("Formation",)],
    ]
    port, connection = _port(responses)

    stats = port.column_stats("deplacements", column, sample_limit=3)

    assert stats.sample_values == ("Réunion", "Formation")
    assert len(connection._cursor.calls) == 2


def test_duplicate_key_row_count_reads_scalar():
    port, connection = _port([(2,)])

    assert port.duplicate_key_row_count("deplacements", ("IDdeplacement",)) == 2


def test_rows_without_usable_key_reads_scalar():
    port, connection = _port([(0,)])

    assert port.rows_without_usable_key("deplacements", ("IDdeplacement",)) == 0


def test_fetch_rows_yields_tuples():
    port, connection = _port([[(7, 12), (8, 12)]])

    rows = list(port.fetch_rows("deplacements", ("IDdeplacement", "IDpersonne")))

    assert rows == [(7, 12), (8, 12)]


def test_close_delegates_to_connection():
    port, connection = _port([])

    port.close()

    assert connection.closed is True


def test_context_manager_closes_connection():
    connection = _FakeConnection([])
    with MySqlLegacyDatabasePort(
        connection, database="teamworks", source_label="mysql://test", engine_version="8.0"
    ):
        pass

    assert connection.closed is True
