from datetime import date

from domain.convention.salary_grid_version import SalaryGridVersion, SalaryGridVersionStatus
from domain.engine.rule_version import RuleVersionValidationLevel
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

    assert reader.calls == [("contrats", 25), ("grilles", None), ("lignes", 7)]
    assert reader.closed is False
    assert len(rows) == 1
    assert rows[0].IDcontrat == 1
    assert rows[0].nom_complet == "Ada Lovelace"
    assert rows[0].classification == "G3"
    assert rows[0].type_contrat == "CDI"


def _version(grid_code, effective_date=date(2026, 1, 1), version="2026-01"):
    return SalaryGridVersion(
        grid_code=grid_code,
        version=version,
        effective_date=effective_date,
        status=SalaryGridVersionStatus.ACTIVE,
        validation_level=RuleVersionValidationLevel.DOCUMENTED,
    )


class MultiGridReader(FakeReader):
    def __init__(self, grids):
        super().__init__()
        self._grids = grids

    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return self._grids


def test_audit_contracts_selectionne_la_version_applicable_la_plus_recente_sans_code_en_dur():
    grids = [
        CcnsGrilleRecord(6, "CCNS-2025", "Grille 2025", "CCNS", "standard", "2025-01-01", None, "test"),
        CcnsGrilleRecord(7, "CCNS-2026", "Grille 2026", "CCNS", "standard", "2026-01-01", None, "test"),
    ]
    reader = MultiGridReader(grids)

    rows = audit_contracts(
        data_reader=reader,
        reference_date=date(2026, 7, 1),
        salary_grid_versions=[
            _version("CCNS-2025", date(2025, 1, 1), "2025-01"),
            _version("CCNS-2026"),
        ],
    )

    assert ("grilles", None) in reader.calls
    assert ("lignes", 7) in reader.calls
    assert not [message for message in rows[0].messages if message.startswith("Diagnostic grille salariale")]


def test_audit_contracts_diagnostique_aucune_version_disponible_sans_bloquer():
    reader = FakeReader()

    rows = audit_contracts(data_reader=reader, salary_grid_versions=[])

    assert ("lignes", 7) not in reader.calls
    assert "Diagnostic grille salariale : aucune version disponible." in rows[0].messages


def test_audit_contracts_diagnostique_aucune_version_applicable_sans_bloquer():
    reader = FakeReader()

    rows = audit_contracts(
        data_reader=reader,
        reference_date=date(2026, 7, 1),
        salary_grid_versions=[_version("CCNS-2026", date(2027, 1, 1), "2027-01")],
    )

    assert ("lignes", 7) not in reader.calls
    assert "Diagnostic grille salariale : aucune version applicable aux grilles disponibles." in rows[0].messages


def test_audit_contracts_diagnostique_version_sans_grille_reelle_sans_bloquer():
    reader = FakeReader()

    rows = audit_contracts(
        data_reader=reader,
        reference_date=date(2026, 7, 1),
        salary_grid_versions=[_version("CCNS-MANQUANTE")],
    )

    assert ("lignes", 7) not in reader.calls
    assert "Diagnostic grille salariale : version applicable sans grille réelle (CCNS-MANQUANTE)." in rows[0].messages


def test_audit_contracts_diagnostique_plusieurs_grilles_pour_le_meme_code_sans_bloquer():
    grids = [
        CcnsGrilleRecord(7, "CCNS-2026", "Grille 2026 A", "CCNS", "standard", "2026-01-01", None, "test"),
        CcnsGrilleRecord(8, "CCNS-2026", "Grille 2026 B", "CCNS", "standard", "2026-01-01", None, "test"),
    ]
    reader = MultiGridReader(grids)

    rows = audit_contracts(
        data_reader=reader,
        reference_date=date(2026, 7, 1),
        salary_grid_versions=[_version("CCNS-2026")],
    )

    assert not any(call[0] == "lignes" for call in reader.calls)
    assert "Diagnostic grille salariale : plusieurs grilles réelles pour le code CCNS-2026." in rows[0].messages
