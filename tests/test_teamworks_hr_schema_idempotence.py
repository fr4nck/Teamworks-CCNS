import sqlite3

from infrastructure.persistence.teamworks_hr_connections_repository import (
    TEAMWORKS_HR_SCHEMA_VERSION,
    TeamworksHrConnectionsRepository,
)


class LocalGestionDb:
    def __init__(self, path):
        self.isNetwork = False
        self.connexion = sqlite3.connect(path)
        self.cursor = self.connexion.cursor()

    def Commit(self):
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


def test_teamworks_hr_schema_initialization_is_idempotent(tmp_path):
    path = tmp_path / "teamworks-data.sqlite"
    factory = lambda: LocalGestionDb(path)

    repository = TeamworksHrConnectionsRepository(db_factory=factory)
    repository.ensure_schema()
    repository.ensure_schema()

    assert repository.schema_version() == TEAMWORKS_HR_SCHEMA_VERSION
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT component, schema_version FROM tw_hr_schema_versions"
        ).fetchall()
    assert rows == [("hr_connections_runtime", TEAMWORKS_HR_SCHEMA_VERSION)]
