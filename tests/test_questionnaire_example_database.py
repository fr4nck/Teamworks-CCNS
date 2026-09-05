from __future__ import annotations

import sqlite3
from pathlib import Path

from infrastructure.persistence.questionnaire_reader import QuestionnaireReader


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DB = ROOT / "teamworks" / "Static" / "Exemples" / "Exemple_TDATA.dat"


class SqliteGestionDBCompat:
    """Adaptateur minimal de la base exemple vers le contrat GestionDB du reader."""

    def __init__(self, path: Path):
        self._connection = sqlite3.connect(path)
        self._cursor = None

    def ExecuterReq(self, req):
        self._cursor = self._connection.execute(req)

    def ResultatReq(self):
        return self._cursor.fetchall()

    def Close(self):
        self._connection.close()


def test_questionnaire_projection_matches_historical_example_database():
    from questionnaire_read_adapter import QuestionnaireProductionReadAdapter

    db = SqliteGestionDBCompat(EXAMPLE_DB)
    reader = QuestionnaireReader(db_factory=lambda: db)
    adapter = QuestionnaireProductionReadAdapter(reader=reader)

    views = adapter.list_questionnaire(3)

    assert [(view.question, view.answer) for view in views] == [
        ("Numéro de matricule", "XD16252"),
        ("Date d'embauche", "2008-12-03"),
        ("Statut", "Permanent"),
        ("Fiche de candidature", "—"),
        ("Véhicule personnel", "Moto, Vélo"),
        ("Pointure", "41"),
    ]
    assert all("##DOCUMENTS##" not in view.answer for view in views)

    adapter.close()
