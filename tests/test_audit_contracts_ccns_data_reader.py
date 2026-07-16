from datetime import date

from domain.convention.salary_grid_version import SalaryGridVersion, SalaryGridVersionStatus
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.engine.rule_version import RuleVersionValidationLevel
from domain.repositories.ccns_data import CcnsContratRecord, CcnsGrilleRecord, CcnsLigneGrilleRecord
from teamworks.CcnsCore import audit_contracts_ccns as audit_module
from teamworks.CcnsCore.audit_contracts_ccns import _select_salary_grid_record, audit_contracts


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


def test_audit_signale_un_cdd_historique_sans_date_fin_et_poursuit():
    class IncompleteContractsReader(FakeReader):
        def lire_contrats(self, limit=None):
            self.calls.append(("contrats", limit))
            return [
                CcnsContratRecord(1, "2024-01-01", None, 2100.0, 35.0, 10.0, "Ada", "Lovelace", "G3", "CDD"),
                CcnsContratRecord(2, "2024-02-01", "2024-12-31", 2100.0, 35.0, 10.0, "Grace", "Hopper", "G3", "CDD"),
            ]

    rows = audit_contracts(data_reader=IncompleteContractsReader())

    assert len(rows) == 2
    assert rows[0].IDcontrat == 1
    assert rows[0].anomalies == ["CONTRAT_A_DUREE_DETERMINEE_SANS_DATE_FIN"]
    assert rows[1].IDcontrat == 2
    assert "CONTRAT_A_DUREE_DETERMINEE_SANS_DATE_FIN" not in rows[1].anomalies
    assert "Classification conventionnelle présente" in rows[1].messages


def test_mapping_historique_des_regimes_utilise_les_codes_canoniques():
    assert audit_module._map_employment_regime(ContractType.APPRENTICESHIP) is EmploymentRegime.APPRENTICE
    assert audit_module._map_employment_regime(ContractType.CIVIC_SERVICE) is EmploymentRegime.SERVICE_CIVIQUE
    assert audit_module._map_employment_regime(ContractType.INTERNSHIP) is EmploymentRegime.STAGE_PFMP


def _grid(grid_id, code, effective_date, amount_code="CCNS"):
    return CcnsGrilleRecord(grid_id, code, f"Grille {code}", amount_code, "standard", effective_date, None, "test")


def _version(code, version, effective_date, status=SalaryGridVersionStatus.ACTIVE, validation_level=RuleVersionValidationLevel.DOCUMENTED):
    return SalaryGridVersion(
        grid_code=code,
        version=version,
        effective_date=effective_date,
        status=status,
        validation_level=validation_level,
    )


def test_select_salary_grid_record_replie_si_aucune_version_disponible(monkeypatch):
    events = []
    monkeypatch.setattr(audit_module, "_diagnose_salary_grid_selection", lambda event, *args, **kwargs: events.append(event))
    grids = [_grid(20, "CCNS-2027", "2027-01-01"), _grid(10, "CCNS-2026", "2026-01-01")]

    selected = _select_salary_grid_record(grids, date(2026, 9, 15), [])

    assert selected.IDtw_salary_grid == 10
    assert "aucune_version" in events
    assert "repli_grille" in events


def test_select_salary_grid_record_replie_si_aucune_version_applicable(monkeypatch):
    events = []
    monkeypatch.setattr(audit_module, "_diagnose_salary_grid_selection", lambda event, *args, **kwargs: events.append(event))
    grids = [_grid(30, "CCNS-2027", "2027-01-01"), _grid(10, "CCNS-2026", "2026-01-01")]
    versions = [_version("CCNS-2027", "2027-01", date(2027, 1, 1))]

    selected = _select_salary_grid_record(grids, date(2026, 9, 15), versions)

    assert selected.IDtw_salary_grid == 10
    assert "aucune_version_applicable" in events
    assert "repli_grille" in events


def test_select_salary_grid_record_replie_si_version_applicable_sans_grille(monkeypatch):
    events = []
    monkeypatch.setattr(audit_module, "_diagnose_salary_grid_selection", lambda event, *args, **kwargs: events.append(event))
    grids = [_grid(10, "CCNS-2026", "2026-01-01")]
    versions = [_version("CCNS-ABSENTE", "2026-01", date(2026, 1, 1))]

    selected = _select_salary_grid_record(grids, date(2026, 9, 15), versions)

    assert selected.IDtw_salary_grid == 10
    assert "version_sans_grille_reelle" in events
    assert "repli_grille" in events


def test_select_salary_grid_record_signale_doublon_et_choisit_deterministiquement(monkeypatch):
    events = []
    monkeypatch.setattr(audit_module, "_diagnose_salary_grid_selection", lambda event, *args, **kwargs: events.append(event))
    grids = [_grid(9, "CCNS-2026", "2026-01-01"), _grid(7, "CCNS-2026", "2026-01-01")]
    versions = [_version("CCNS-2026", "2026-01", date(2026, 1, 1))]

    selected = _select_salary_grid_record(grids, date(2026, 9, 15), versions)

    assert selected.IDtw_salary_grid == 7
    assert "doublon_code_grille" in events


def test_audit_ne_cree_pas_contrat_sans_grille_quand_repli_existe(monkeypatch):
    events = []
    monkeypatch.setattr(audit_module, "_diagnose_salary_grid_selection", lambda event, *args, **kwargs: events.append(event))
    reader = FakeReader()

    rows = audit_contracts(limit=25, data_reader=reader, reference_date=date(2026, 9, 15))

    assert "aucune_version" in events
    assert "CONTRAT_SANS_GRILLE" not in rows[0].anomalies


def test_audit_selection_historique_charge_la_grille_reelle_selon_version():
    class HistoricalReader(FakeReader):
        def lire_grilles(self, limit=None):
            self.calls.append(("grilles", limit))
            return [
                _grid(1, "CCNS-2025", "2025-01-01"),
                _grid(2, "CCNS-2026", "2026-01-01"),
            ]

        def lire_versions_grilles(self):
            self.calls.append(("versions", None))
            return [
                _version("CCNS-2025", "2025-01", date(2025, 1, 1)),
                _version("CCNS-2026", "2026-01", date(2026, 1, 1)),
            ]

        def lire_lignes_grille(self, IDtw_salary_grid):
            self.calls.append(("lignes", IDtw_salary_grid))
            amounts = {1: 2200.0, 2: 1900.0}
            return [CcnsLigneGrilleRecord(IDtw_salary_grid * 10, IDtw_salary_grid, "G3", "monthly", amounts[IDtw_salary_grid], "EUR", None, None, None, None, "")]

    reader = HistoricalReader()

    rows = audit_contracts(limit=25, data_reader=reader, reference_date=date(2025, 9, 15))

    assert ("lignes", 1) in reader.calls
    assert "MINIMUM_CCNS_NON_ATTEINT" in rows[0].anomalies
