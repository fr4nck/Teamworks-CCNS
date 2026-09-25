from infrastructure.repositories.person_delete_repository import GestionDBPersonDeleteRepository


class FakeCursor:
    def __init__(self, rows=None, fail_table=None):
        self.rows = list(rows or [])
        self.fail_table = fail_table
        self.executed = []

    def execute(self, query, params=()):
        self.executed.append((query, params))
        if self.fail_table and ("DELETE FROM %s " % self.fail_table) in query:
            raise RuntimeError("delete failed")

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeConnection:
    def __init__(self):
        self.rollbacks = 0

    def rollback(self):
        self.rollbacks += 1


class FakeDB:
    def __init__(self, rows=None, fail_table=None, network=False):
        self.isNetwork = network
        self.cursor = FakeCursor(rows=rows, fail_table=fail_table)
        self.connexion = FakeConnection()
        self.commits = 0
        self.closed = 0

    def Commit(self):
        self.commits += 1

    def Close(self):
        self.closed += 1


class Factory:
    def __init__(self, db):
        self.db = db

    def __call__(self):
        return self.db


def test_dependency_check_uses_parameterized_query_and_closes():
    db = FakeDB(rows=[(1,)])
    repository = GestionDBPersonDeleteRepository(Factory(db))

    assert repository.has_contracts(42) is True
    query, params = db.cursor.executed[0]
    assert query == "SELECT IDcontrat FROM contrats WHERE IDpersonne=?"
    assert params == (42,)
    assert db.closed == 1


def test_network_dependency_check_uses_mysql_placeholder():
    db = FakeDB(rows=[], network=True)
    repository = GestionDBPersonDeleteRepository(Factory(db))

    assert repository.has_presences(42) is False
    assert db.cursor.executed[0] == (
        "SELECT IDpresence FROM presences WHERE IDpersonne=%s",
        (42,),
    )


def test_delete_is_one_transaction_for_person_and_dependents():
    db = FakeDB()
    repository = GestionDBPersonDeleteRepository(Factory(db))

    repository.delete_person_with_dependents(42)

    assert [query for query, _ in db.cursor.executed] == [
        "DELETE FROM coordonnees WHERE IDpersonne=?",
        "DELETE FROM diplomes WHERE IDpersonne=?",
        "DELETE FROM pieces WHERE IDpersonne=?",
        "DELETE FROM personnes WHERE IDpersonne=?",
    ]
    assert all(params == (42,) for _, params in db.cursor.executed)
    assert db.commits == 1
    assert db.connexion.rollbacks == 0
    assert db.closed == 1


def test_delete_rolls_back_whole_transaction_on_failure():
    db = FakeDB(fail_table="pieces")
    repository = GestionDBPersonDeleteRepository(Factory(db))

    try:
        repository.delete_person_with_dependents(42)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected delete failure")

    assert db.commits == 0
    assert db.connexion.rollbacks == 1
    assert db.closed == 1
