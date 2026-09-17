from infrastructure.persistence.ccns_data_reader import CcnsDataReader
from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance


class FakeDB:
    def __init__(self, modern_contract_columns=False):
        self.requests = []
        self.closed = False
        self.current = ""
        self.modern_contract_columns = modern_contract_columns

    def GetListeChamps2(self, table_name):
        assert table_name == "contrats"
        columns = [
            ("IDcontrat",),
            ("IDpersonne",),
            ("date_debut",),
            ("date_fin",),
            ("IDclassification",),
            ("IDtype",),
            ("date_rupture",),
            ("signature",),
            ("due",),
        ]
        if self.modern_contract_columns:
            columns.extend((("convention_code",), ("ccns_group",)))
        return columns

    def AjoutChamp(self, *args, **kwargs):
        raise AssertionError("Le reader Qt ne doit jamais modifier le schéma")

    def ExecuterReq(self, req):
        self.current = req
        self.requests.append(req)

    def ResultatReq(self):
        if "FROM contrats\n" in self.current:
            convention = "CCNS" if self.modern_contract_columns else None
            group = "G3" if self.modern_contract_columns else None
            return [
                (
                    1,
                    42,
                    "2026-01-01",
                    None,
                    2100.0,
                    35.0,
                    10.0,
                    "Ada",
                    "Lovelace",
                    "G3",
                    "CDI",
                    None,
                    convention,
                    group,
                    "Oui",
                    "",
                )
            ]
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
    assert contrats[0].IDpersonne == 42
    assert contrats[0].classification == "G3"
    assert contrats[0].convention_code is None
    assert contrats[0].ccns_group is None
    assert contrats[0].signature == "Oui"
    assert contrats[0].due == ""
    assert classifications[0].nom == "G3"
    assert grilles[0].code == "CCNS-2026"
    assert lignes[0].IDtw_salary_grid == 7
    assert "LIMIT 5" in db.requests[0]
    assert "LIMIT 1" in db.requests[2]
    assert db.closed is True


def test_ccns_data_reader_lit_les_colonnes_tw184_si_presentes_sans_modifier_le_schema():
    db = FakeDB(modern_contract_columns=True)
    reader = CcnsDataReader(db_factory=lambda: db)

    contrat = reader.lire_contrats_personne(42)[0]

    assert contrat.convention_code == "CCNS"
    assert contrat.ccns_group == "G3"
    assert "contrats.convention_code AS convention_code" in db.requests[0]
    assert "contrats.ccns_group AS ccns_group" in db.requests[0]


def test_ccns_data_reader_projette_null_sur_schema_historique():
    db = FakeDB(modern_contract_columns=False)
    reader = CcnsDataReader(db_factory=lambda: db)

    reader.lire_contrats_personne(42)

    assert "NULL AS convention_code" in db.requests[0]
    assert "NULL AS ccns_group" in db.requests[0]


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


def test_ccns_data_reader_alimente_les_mesures_sql(monkeypatch):
    monkeypatch.setenv("TEAMWORKS_PERF_DIAG", "1")
    DiagnosticPerformance.reinitialiser_mesures()
    reader = CcnsDataReader(db_factory=FakeDB)

    contrats = reader.lire_contrats(limit=1)

    mesures = DiagnosticPerformance.obtenir_mesures()
    DiagnosticPerformance.reinitialiser_mesures()
    assert len(contrats) == 1
    assert [mesure["categorie"] for mesure in mesures] == ["sql", "sql_fetch", "sql_requetes"]
    assert mesures[-1]["nom"] == "ccns_data_reader.contrats.nombre"
    assert mesures[-1]["details"] == {"lignes": 1}


def test_ccns_data_reader_filtre_les_contrats_par_personne():
    db = FakeDB()
    reader = CcnsDataReader(db_factory=lambda: db)

    contrats = reader.lire_contrats_personne(42, limit=3)

    assert len(contrats) == 1
    assert "WHERE contrats.IDpersonne=42" in db.requests[0]
    assert "LIMIT 3" in db.requests[0]
