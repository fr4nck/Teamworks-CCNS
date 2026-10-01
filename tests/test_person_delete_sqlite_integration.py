import sqlite3

import pytest

from infrastructure.repositories.person_delete_repository import (
    GestionDBPersonDeleteRepository,
)


SCHEMA = """
CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, nom TEXT);
CREATE TABLE coordonnees (IDcoord INTEGER PRIMARY KEY, IDpersonne INTEGER, texte TEXT);
CREATE TABLE diplomes (IDdiplome INTEGER PRIMARY KEY, IDpersonne INTEGER, libelle TEXT);
CREATE TABLE pieces (IDpiece INTEGER PRIMARY KEY, IDpersonne INTEGER, libelle TEXT);
"""


class SQLiteGestionDB:
    """Double d'intégration minimal reproduisant le contrat GestionDB utilisé par l'adaptateur."""

    def __init__(self, path):
        self.isNetwork = False
        self.connexion = sqlite3.connect(path)
        self.cursor = self.connexion.cursor()

    def Commit(self):
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


class SQLiteFactory:
    def __init__(self, path):
        self.path = path

    def __call__(self):
        return SQLiteGestionDB(self.path)


def _create_database(path, *, fail_on_piece_delete=False):
    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA)
        connection.execute("INSERT INTO personnes VALUES (42, 'MARTIN')")
        connection.execute("INSERT INTO coordonnees VALUES (1, 42, 'test@example.invalid')")
        connection.execute("INSERT INTO diplomes VALUES (1, 42, 'BAFA')")
        connection.execute("INSERT INTO pieces VALUES (1, 42, 'piece')")
        if fail_on_piece_delete:
            connection.execute(
                """
                CREATE TRIGGER fail_piece_delete
                BEFORE DELETE ON pieces
                WHEN OLD.IDpersonne = 42
                BEGIN
                    SELECT RAISE(ABORT, 'forced piece delete failure');
                END;
                """
            )
        connection.commit()
    finally:
        connection.close()


def _counts(path):
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(
                "SELECT COUNT(*) FROM %s WHERE IDpersonne = 42" % table
            ).fetchone()[0]
            for table in ("personnes", "coordonnees", "diplomes", "pieces")
        }
    finally:
        connection.close()


def test_sqlite_delete_commits_person_and_dependents_atomically(tmp_path):
    path = tmp_path / "people-delete.sqlite"
    _create_database(path)
    repository = GestionDBPersonDeleteRepository(SQLiteFactory(path))

    repository.delete_person_with_dependents(42)

    assert _counts(path) == {
        "personnes": 0,
        "coordonnees": 0,
        "diplomes": 0,
        "pieces": 0,
    }


def test_sqlite_delete_rolls_back_every_prior_delete_on_database_error(tmp_path):
    path = tmp_path / "people-delete-rollback.sqlite"
    _create_database(path, fail_on_piece_delete=True)
    repository = GestionDBPersonDeleteRepository(SQLiteFactory(path))

    with pytest.raises(sqlite3.IntegrityError, match="forced piece delete failure"):
        repository.delete_person_with_dependents(42)

    # coordonnees et diplomes sont supprimés avant pieces dans l'adaptateur.
    # Leur présence après l'erreur prouve que le rollback couvre toute
    # l'opération et pas seulement la requête qui a échoué.
    assert _counts(path) == {
        "personnes": 1,
        "coordonnees": 1,
        "diplomes": 1,
        "pieces": 1,
    }
