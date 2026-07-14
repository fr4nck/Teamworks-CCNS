from infrastructure.persistence.ccns_data_reader import CcnsDataReader


class FakeDB:
    def __init__(self):
        self.requests = []
        self.closed = False
        self.current = ""

    def ExecuterReq(self, req):
        self.current = req
        self.requests.append(req)

    def ResultatReq(self):
        if "FROM contrats\n" in self.current:
            return [(1, "2026-01-01", None, 2100.0, 35.0, 10.0, "Ada", "Lovelace", "G3", "CDI")]
        if "FROM contrats_class" in self.current:
            return [(3, "G3")]
        if "FROM tw_salary_grids" in self.current:
            return [(7, "CCNS-2026", "Grille 2026", "CCNS", "standard", "2026-01-01", None, "test")]
        if "FROM tw_salary_grid_lines" in self.current:
            return [(8, 7, "G3", "monthly", 1997.87, "EUR", None, None, None, None, "")]
        return []

    def Close(self):
        self.closed = True


def test_ccns_data_reader_lit_le_perimetre_ccns_sans_wx():
    db = FakeDB()
    reader = CcnsDataReader(db_factory=lambda: db)

    contrats = reader.lire_contrats(limit=5)
    classifications = reader.lire_classifications()
    grilles = reader.lire_grilles(limit=1)
    lignes = reader.lire_lignes_grille(7)
    reader.close()

    assert contrats[0].IDcontrat == 1
    assert contrats[0].classification == "G3"
    assert classifications[0].nom == "G3"
    assert grilles[0].code == "CCNS-2026"
    assert lignes[0].IDtw_salary_grid == 7
    assert "LIMIT 5" in db.requests[0]
    assert "LIMIT 1" in db.requests[2]
    assert db.closed is True


def test_ccns_data_reader_reutilise_une_seule_connexion():
    instances = []

    def factory():
        db = FakeDB()
        instances.append(db)
        return db

    reader = CcnsDataReader(db_factory=factory)
    reader.lire_contrats()
    reader.lire_grilles(limit=1)
    reader.lire_lignes_grille(7)

    assert len(instances) == 1
    assert len(instances[0].requests) == 3
