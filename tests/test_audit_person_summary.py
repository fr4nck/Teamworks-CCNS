from domain.repositories.ccns_data import CcnsContratRecord, CcnsGrilleRecord, CcnsLigneGrilleRecord
from teamworks.CcnsCore.audit_person_summary import build_person_ccns_summary


class FakePersonSummaryReader:
    def __init__(self):
        self.calls = []
        self.closed = False

    def lire_contrats_personne(self, IDpersonne, limit=None):
        self.calls.append(("contrats_personne", IDpersonne, limit))
        return [
            CcnsContratRecord(2, 102, "2026-01-01", None, 1500.0, 35.0, 0.0, "Ada", "Lovelace", "G3", "CDI"),
            CcnsContratRecord(1, 101, "2026-01-01", None, 2200.0, 35.0, 0.0, "Ada", "Lovelace", "G3", "CDI"),
        ]

    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return [CcnsGrilleRecord(7, "CCNS-2026", "Grille 2026", "CCNS", "standard", "2026-01-01", None, "test")]

    def lire_lignes_grille(self, IDtw_salary_grid):
        self.calls.append(("lignes", IDtw_salary_grid))
        return [CcnsLigneGrilleRecord(8, 7, "G3", "monthly", 1997.87, "EUR", None, None, None, None, "")]

    def close(self):
        self.closed = True


def test_build_person_ccns_summary_utilise_le_reader_filtre_par_personne():
    reader = FakePersonSummaryReader()

    summary = build_person_ccns_summary(42, data_reader=reader)

    assert reader.calls == [("contrats_personne", 42, None), ("grilles", None), ("lignes", 7)]
    assert reader.closed is False
    assert summary["IDpersonne"] == 42
    assert summary["nb_contracts"] == 2
    assert summary["nb_warning"] == 1
    assert summary["nb_ok"] == 1
    assert summary["global_status"] == "A_REVOIR"
    assert [row["IDcontrat"] for row in summary["rows"]] == [2, 1]
