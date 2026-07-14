from infrastructure.persistence.person_reader import PersonReader
from teamworks.Utils import UTILS_Diagnostic_performance as diag


class FakeDB:
    def __init__(self):
        self.requests = []
        self.closed = False
        self.current = ""

    def ExecuterReq(self, req):
        self.current = req
        self.requests.append(req)

    def ResultatReq(self):
        if "FROM personnes" in self.current:
            return [(2, "Curie", "Marie"), (1, "Lovelace", "Ada")]
        return []

    def Close(self):
        self.closed = True


def test_person_reader_lit_identites_triees_sans_wx():
    db = FakeDB()
    reader = PersonReader(db_factory=lambda: db)

    personnes = reader.lire_identites()
    reader.close()

    assert [personne.IDpersonne for personne in personnes] == [2, 1]
    assert personnes[0].nom == "Curie"
    assert personnes[1].prenom == "Ada"
    assert tuple(personnes[0]) == (2, "Curie", "Marie")
    assert len(db.requests) == 1
    assert db.requests[0] == "SELECT IDpersonne, nom, prenom FROM personnes ORDER BY nom, prenom;"
    assert db.closed is True


def test_person_reader_mesure_sql_et_mapping_python(monkeypatch):
    monkeypatch.setenv("TEAMWORKS_PERF_DIAG", "1")
    diag.reinitialiser_mesures()
    db = FakeDB()
    reader = PersonReader(db_factory=lambda: db)

    personnes = reader.lire_identites()

    mesures = diag.obtenir_mesures()
    mesures_sql = [mesure for mesure in mesures if mesure["categorie"] == "sql"]
    mesures_python = [mesure for mesure in mesures if mesure["categorie"] == "python"]

    assert len(personnes) == 2
    assert len(db.requests) == 1
    assert len(mesures_sql) == 1
    assert len(mesures_python) == 1
    assert mesures_sql[0]["nom"] == "PersonReader.lire_identites"
    assert mesures_python[0]["nom"] == "PersonReader.lire_identites.mapping"
    assert mesures_python[0]["details"]["lignes"] == 2

    diag.reinitialiser_mesures()
    monkeypatch.delenv("TEAMWORKS_PERF_DIAG", raising=False)
