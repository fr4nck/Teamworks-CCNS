import sqlite3

import pytest

from domain.migration.inventory_engine import build_database_inventory
from infrastructure.persistence.legacy_sqlite_inventory_adapter import (
    SqliteLegacyDatabasePort,
    connect_sqlite_readonly,
)


def _build_database(path):
    connection = sqlite3.connect(str(path))
    connection.executescript(
        """
        CREATE TABLE personnes (
            IDpersonne INTEGER PRIMARY KEY AUTOINCREMENT,
            nom VARCHAR(100),
            prenom VARCHAR(100)
        );
        CREATE TABLE deplacements (
            IDdeplacement INTEGER PRIMARY KEY AUTOINCREMENT,
            IDpersonne INTEGER,
            date DATE,
            objet VARCHAR(100),
            cp_depart VARCHAR(5),
            ville_depart VARCHAR(200),
            cp_arrivee VARCHAR(5),
            ville_arrivee VARCHAR(200),
            distance FLOAT,
            aller_retour VARCHAR(5),
            tarif_km FLOAT,
            IDremboursement INTEGER
        );
        CREATE TABLE remboursements (
            IDremboursement INTEGER PRIMARY KEY AUTOINCREMENT,
            IDpersonne INTEGER,
            date DATE,
            montant FLOAT,
            listeIDdeplacement VARCHAR(300)
        );

        INSERT INTO personnes VALUES (12, 'Dupont', 'Alice');
        INSERT INTO personnes VALUES (13, 'Martin', 'Bob');

        INSERT INTO deplacements VALUES
            (7, 12, '2026-09-10', 'Réunion', '03510', 'BRUZ', '35000', 'RENNES', 20.0, '0', 0.5, 3);
        INSERT INTO deplacements VALUES
            (8, 12, '2026-09-11', '', '', '', '', '', 5.0, '0', 0.5, 0);
        INSERT INTO deplacements VALUES
            (9, 12, '2026-09-12', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

        INSERT INTO remboursements VALUES (3, 12, '2026-09-30', 10.00, '7');
        """
    )
    connection.commit()
    connection.close()


@pytest.fixture()
def legacy_db_path(tmp_path):
    path = tmp_path / "legacy.sqlite"
    _build_database(path)
    return path


def test_connect_readonly_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        connect_sqlite_readonly(tmp_path / "does-not-exist.sqlite")


def test_connect_readonly_prevents_writes(legacy_db_path):
    connection = connect_sqlite_readonly(legacy_db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("INSERT INTO personnes VALUES (99, 'X', 'Y')")
    finally:
        connection.close()


def test_list_tables_returns_user_tables_only(legacy_db_path):
    with SqliteLegacyDatabasePort.from_path(legacy_db_path) as port:
        tables = port.list_tables()

    assert set(tables) == {"personnes", "deplacements", "remboursements"}


def test_row_count_matches_inserted_rows(legacy_db_path):
    with SqliteLegacyDatabasePort.from_path(legacy_db_path) as port:
        assert port.row_count("deplacements") == 3
        assert port.row_count("remboursements") == 1


def test_column_definitions_detect_primary_key(legacy_db_path):
    with SqliteLegacyDatabasePort.from_path(legacy_db_path) as port:
        columns = port.column_definitions("deplacements")

    by_name = {c.name: c for c in columns}
    assert by_name["IDdeplacement"].is_primary_key is True
    assert by_name["IDpersonne"].is_primary_key is False


def test_column_stats_count_null_empty_and_zero(legacy_db_path):
    with SqliteLegacyDatabasePort.from_path(legacy_db_path) as port:
        columns = {c.name: c for c in port.column_definitions("deplacements")}
        objet_stats = port.column_stats("deplacements", columns["objet"], sample_limit=3)
        reimb_stats = port.column_stats(
            "deplacements", columns["IDremboursement"], sample_limit=3
        )

    assert objet_stats.row_count == 3
    assert objet_stats.null_count == 1
    assert objet_stats.empty_string_count == 1
    assert reimb_stats.null_count == 1
    assert reimb_stats.zero_count == 1


def test_full_inventory_is_built_end_to_end(legacy_db_path):
    with SqliteLegacyDatabasePort.from_path(legacy_db_path) as port:
        inventory = build_database_inventory(port)

    assert inventory.table_count == 3
    assert inventory.total_row_count == 3 + 1 + 2
    personnes = inventory.table("personnes")
    nom_column = next(c for c in personnes.columns if c.column.name == "nom")
    assert nom_column.sample_values == ()


def test_duplicate_key_row_count_is_zero_for_clean_table(legacy_db_path):
    with SqliteLegacyDatabasePort.from_path(legacy_db_path) as port:
        assert port.duplicate_key_row_count("deplacements", ("IDdeplacement",)) == 0


def test_rows_without_usable_key_counts_null_primary_key(tmp_path):
    path = tmp_path / "broken.sqlite"
    connection = sqlite3.connect(str(path))
    connection.executescript(
        """
        CREATE TABLE t (id INTEGER, val TEXT);
        INSERT INTO t VALUES (1, 'a');
        INSERT INTO t VALUES (NULL, 'b');
        """
    )
    connection.commit()
    connection.close()

    with SqliteLegacyDatabasePort.from_path(path) as port:
        assert port.rows_without_usable_key("t", ("id",)) == 1


def test_fetch_rows_streams_requested_columns(legacy_db_path):
    with SqliteLegacyDatabasePort.from_path(legacy_db_path) as port:
        rows = list(
            port.fetch_rows("deplacements", ("IDdeplacement", "IDpersonne"))
        )

    assert rows == [(7, 12), (8, 12), (9, 12)]


def test_zero_sample_limit_never_issues_a_sample_query_at_the_sql_level(legacy_db_path):
    """Preuve au niveau SQL, pas seulement au niveau du résultat : quand
    sample_limit=0 (ce que le moteur impose pour une colonne sensible),
    l'adaptateur ne doit émettre aucune requête d'échantillonnage du tout.
    """
    connection = sqlite3.connect(str(legacy_db_path))
    executed_sql: list[str] = []
    connection.set_trace_callback(executed_sql.append)
    port = SqliteLegacyDatabasePort(connection, source_label=str(legacy_db_path))
    try:
        columns = {c.name: c for c in port.column_definitions("personnes")}

        # La requête de statistiques agrégées (COUNT/SUM/MIN/MAX, y compris
        # COUNT(DISTINCT ...)) est toujours exécutée : ce n'est pas elle
        # qu'il faut interdire. La requête d'échantillonnage, elle, a une
        # forme distincte : SELECT DISTINCT <col> ... ORDER BY ... LIMIT.
        def issued_sample_query(statements: list[str]) -> bool:
            return any("LIMIT" in sql and "ORDER BY" in sql for sql in statements)

        executed_sql.clear()
        stats_masked = port.column_stats("personnes", columns["nom"], sample_limit=0)

        assert stats_masked.sample_values == ()
        assert issued_sample_query(executed_sql) is False

        executed_sql.clear()
        stats_sampled = port.column_stats("personnes", columns["nom"], sample_limit=3)

        assert issued_sample_query(executed_sql) is True
        assert stats_sampled.sample_values != ()
    finally:
        port.close()
