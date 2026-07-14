from datetime import date

from domain.convention.salary_grid_version import SalaryGridVersion, SalaryGridVersionStatus
from domain.engine.rule_version import RuleVersionValidationLevel
from domain.repositories.ccns_data import CcnsContratRecord, CcnsGrilleRecord, CcnsLigneGrilleRecord
from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance
from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.engine.minimum_checks import check_contract_minimum_from_grid
from teamworks.CcnsCore.audit_contracts_ccns import _build_salary_grid, _select_grid_record, audit_contracts


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

    def lire_versions_grilles(self):
        self.calls.append(("versions", None))
        return []

    def lire_lignes_grille(self, IDtw_salary_grid):
        self.calls.append(("lignes", IDtw_salary_grid))
        return [CcnsLigneGrilleRecord(8, 7, "G3", "monthly", 1997.87, "EUR", None, None, None, None, "")]

    def close(self):
        self.closed = True


def test_audit_contracts_utilise_le_lecteur_donnees_ccns_injecte():
    reader = FakeReader()

    rows = audit_contracts(limit=25, data_reader=reader)

    assert reader.calls == [("contrats", 25), ("grilles", None), ("versions", None), ("lignes", 7)]
    assert reader.closed is False
    assert len(rows) == 1
    assert rows[0].IDcontrat == 1
    assert rows[0].nom_complet == "Ada Lovelace"
    assert rows[0].classification == "G3"
    assert rows[0].type_contrat == "CDI"


class VersionedFakeReader(FakeReader):
    def __init__(self, grilles, lignes_par_grille, versions):
        super().__init__()
        self._grilles = grilles
        self._lignes_par_grille = lignes_par_grille
        self._versions = versions

    def lire_contrats(self, limit=None):
        self.calls.append(("contrats", limit))
        return [CcnsContratRecord(1, date(2024, 1, 1), None, 1700.0, 35.0, 0.0, "Ada", "Lovelace", "G3", "CDI")]

    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return self._grilles

    def lire_versions_grilles(self):
        self.calls.append(("versions", None))
        return self._versions

    def lire_lignes_grille(self, IDtw_salary_grid):
        self.calls.append(("lignes", IDtw_salary_grid))
        return self._lignes_par_grille.get(IDtw_salary_grid, [])


def _version(code, start, status=SalaryGridVersionStatus.ACTIVE, validation=RuleVersionValidationLevel.DOCUMENTED):
    return SalaryGridVersion(grid_code=code, version=code, effective_date=start, status=status, validation_level=validation)


def _grid(grid_id, code, start):
    return CcnsGrilleRecord(grid_id, code, code, "CCNS", "standard", start, None, "test")


def _line(line_id, grid_id, amount):
    return CcnsLigneGrilleRecord(line_id, grid_id, "G3", "monthly", amount, "EUR", None, None, None, None, "")


def test_audit_contracts_signale_les_grilles_dupliquees_et_choisit_un_repli_deterministe():
    reader = VersionedFakeReader(
        grilles=[_grid(9, "CCNS-2026", date(2026, 1, 1)), _grid(7, "CCNS-2026", date(2026, 1, 1))],
        lignes_par_grille={7: [_line(70, 7, 1997.87)], 9: [_line(90, 9, 2500.0)]},
        versions=[_version("CCNS-2026", date(2026, 1, 1))],
    )

    rows = audit_contracts(data_reader=reader, reference_date=date(2026, 7, 1))

    assert ("lignes", 7) in reader.calls
    assert any("grille_dupliquee" in message for message in rows[0].messages)


def test_audit_contracts_signale_une_version_sans_grille_reelle_et_utilise_un_repli():
    reader = VersionedFakeReader(
        grilles=[_grid(7, "CCNS-2026", date(2026, 1, 1))],
        lignes_par_grille={7: [_line(70, 7, 1997.87)]},
        versions=[_version("CCNS-2027", date(2026, 1, 1))],
    )

    rows = audit_contracts(data_reader=reader, reference_date=date(2026, 7, 1))

    assert ("lignes", 7) in reader.calls
    assert any("version_sans_grille_reelle" in message for message in rows[0].messages)


def test_selection_grille_produit_reellement_des_minima_differents_selon_la_date():
    grilles = [_grid(7, "CCNS-2024", date(2024, 1, 1)), _grid(8, "CCNS-2026", date(2026, 1, 1))]
    lignes = {7: [_line(70, 7, 1800.0)], 8: [_line(80, 8, 2200.0)]}
    versions = [_version("CCNS-2024", date(2024, 1, 1)), _version("CCNS-2026", date(2026, 1, 1))]
    contract = Contract(
        person_id="person-1",
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2024, 1, 1),
        ccns_classification_code="G3",
        salary_grid_code="CCNS",
        base_salary_amount=2500.0,
        salary_unit="monthly",
        work_ratio=1.0,
        weekly_reference_hours=35.0,
    )

    ancienne_selection = _select_grid_record(grilles, versions, date(2025, 6, 1)).grid_record
    ancienne_grille, anciennes_lignes = _build_salary_grid(ancienne_selection, lignes[ancienne_selection.IDtw_salary_grid])
    ancien_resultat, _ = check_contract_minimum_from_grid(contract=contract, salary_grid=ancienne_grille, salary_grid_lines=anciennes_lignes, reference_date=date(2025, 6, 1))

    recente_selection = _select_grid_record(grilles, versions, date(2026, 6, 1)).grid_record
    recente_grille, recentes_lignes = _build_salary_grid(recente_selection, lignes[recente_selection.IDtw_salary_grid])
    recent_resultat, _ = check_contract_minimum_from_grid(contract=contract, salary_grid=recente_grille, salary_grid_lines=recentes_lignes, reference_date=date(2026, 6, 1))

    assert ancien_resultat.theoretical_value == 1800.0
    assert recent_resultat.theoretical_value == 2200.0


def test_audit_contracts_instrumente_selection_recherche_et_repli(monkeypatch):
    monkeypatch.setenv("TEAMWORKS_PERF_DIAG", "1")
    DiagnosticPerformance.reinitialiser_mesures()
    reader = VersionedFakeReader(
        grilles=[_grid(7, "CCNS-2026", date(2026, 1, 1))],
        lignes_par_grille={7: [_line(70, 7, 1997.87)]},
        versions=[_version("CCNS-2027", date(2026, 1, 1))],
    )

    audit_contracts(data_reader=reader, reference_date=date(2026, 7, 1))

    noms = [mesure["nom"] for mesure in DiagnosticPerformance.obtenir_mesures()]
    DiagnosticPerformance.reinitialiser_mesures()
    assert "audit_contracts_ccns.selection_version" in noms
    assert "audit_contracts_ccns.recherche_grille" in noms
    assert "audit_contracts_ccns.recours_repli" in noms
