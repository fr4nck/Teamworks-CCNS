from datetime import date

from domain.repositories.ccns_data import CcnsContratRecord, CcnsGrilleRecord, CcnsLigneGrilleRecord
from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts


class FakeReader:
    def __init__(self):
        self.calls = []
        self.closed = False

    def lire_contrats(self, limit=None):
        self.calls.append(("contrats", limit))
        return [CcnsContratRecord(1, "2024-01-01", None, 2100.0, 35.0, 10.0, "Ada", "Lovelace", "G3", "CDI")]

    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return [CcnsGrilleRecord(7, "CCNS-2026", "Grille 2026", "CCNS", "standard", "2026-01-01", None, "test")]

    def lire_lignes_grille(self, IDtw_salary_grid):
        self.calls.append(("lignes", IDtw_salary_grid))
        return [CcnsLigneGrilleRecord(8, 7, "G3", "monthly", 1997.87, "EUR", None, None, None, None, "")]

    def close(self):
        self.closed = True


def test_audit_contracts_utilise_le_lecteur_donnees_ccns_injecte():
    reader = FakeReader()

    rows = audit_contracts(limit=25, data_reader=reader)

    assert reader.calls == [("contrats", 25), ("grilles", 1), ("lignes", 7)]
    assert reader.closed is False
    assert len(rows) == 1
    assert rows[0].IDcontrat == 1
    assert rows[0].nom_complet == "Ada Lovelace"
    assert rows[0].classification == "G3"
    assert rows[0].type_contrat == "CDI"


def test_audit_contracts_utilise_la_date_de_reference_injectee():
    reader = FakeReader()

    rows = audit_contracts(data_reader=reader, reference_date=date(2025, 12, 31))

    assert "ANCIENNETE_OUBLIEE" not in rows[0].anomalies
