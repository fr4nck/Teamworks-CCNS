from datetime import date

from domain.convention.salary_grid_version import SalaryGridVersion, SalaryGridVersionStatus
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
        return [CcnsLigneGrilleRecord(8, IDtw_salary_grid, "G3", "monthly", 1997.87, "EUR", None, None, None, None, "")]

    def close(self):
        self.closed = True


class MultiGridReader(FakeReader):
    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return [
            CcnsGrilleRecord(6, "CCNS-2025", "Grille 2025", "CCNS", "standard", "2025-01-01", "2025-12-31", "test"),
            CcnsGrilleRecord(7, "CCNS-2026", "Grille 2026", "CCNS", "standard", "2026-01-01", None, "test"),
        ]


def test_audit_contracts_utilise_le_lecteur_donnees_ccns_injecte():
    reader = FakeReader()

    rows = audit_contracts(limit=25, data_reader=reader, reference_date=date(2026, 3, 15))

    assert reader.calls == [("contrats", 25), ("grilles", None), ("lignes", 7)]
    assert reader.closed is False
    assert len(rows) == 1
    assert rows[0].IDcontrat == 1
    assert rows[0].nom_complet == "Ada Lovelace"
    assert rows[0].classification == "G3"
    assert rows[0].type_contrat == "CDI"
    assert "Version de grille salariale retenue : CCNS-2026 / 2026-01." in rows[0].messages


def test_audit_contracts_selectionne_la_grille_applicable_a_la_date_de_reference():
    reader = MultiGridReader()
    versions = [
        SalaryGridVersion(
            grid_code="CCNS-2025",
            version="2025-01",
            effective_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status=SalaryGridVersionStatus.ACTIVE,
        ),
        SalaryGridVersion(
            grid_code="CCNS-2026",
            version="2026-01",
            effective_date=date(2026, 1, 1),
            status=SalaryGridVersionStatus.ACTIVE,
        ),
    ]

    rows = audit_contracts(data_reader=reader, reference_date=date(2026, 3, 15), salary_grid_versions=versions)

    assert reader.calls == [("contrats", None), ("grilles", None), ("lignes", 7)]
    assert "Version de grille salariale retenue : CCNS-2026 / 2026-01." in rows[0].messages


def test_audit_contracts_conserve_un_repli_explicite_sans_version_applicable():
    reader = MultiGridReader()
    versions = [
        SalaryGridVersion(
            grid_code="CCNS-2026",
            version="2026-01",
            effective_date=date(2026, 1, 1),
            status=SalaryGridVersionStatus.ACTIVE,
        )
    ]

    rows = audit_contracts(data_reader=reader, reference_date=date(2025, 6, 1), salary_grid_versions=versions)

    assert reader.calls == [("contrats", None), ("grilles", None), ("lignes", 6)]
    assert "Aucune version de grille salariale applicable au 2025-06-01" in rows[0].messages[0]
