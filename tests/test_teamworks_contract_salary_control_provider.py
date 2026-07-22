from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.contracts import ContractType, EmploymentRegime, TimeOrganization
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason, ContractSalaryEvaluationService
from domain.convention import (
    ApplicableSalaryMinimumService,
    CCNSClassification,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumComplianceService,
    SalaryMinimumPeriodicity,
    SmicCatalog,
    SmicTerritory,
    SmicVersion,
)
from domain.repositories.ccns_data import CcnsContratRecord
from infrastructure.persistence.teamworks_contract_salary_control_provider import (
    HISTORICAL_FIXED_TERM_WITHOUT_END_DATE_REASON,
    TeamworksContractSalaryControlProvider,
    legacy_contract_uuid,
    legacy_employee_uuid,
)


class Reader:
    def __init__(self, records):
        self.records = records
        self.calls = 0

    def lire_contrats(self, limit=None):
        self.calls += 1
        assert limit is None
        return list(self.records)


def rec(IDcontrat=1, IDpersonne=10, type_contrat="CDI", date_fin=None, classification="G3"):
    return CcnsContratRecord(IDcontrat, IDpersonne, "2026-01-01", date_fin, 2100.0, 35.0, 0.0, "Ada", "Lovelace", classification, type_contrat)


def listed(provider, **filters):
    return list(provider.list_for_salary_control(**filters))


def test_convertit_un_cdi_historique_avec_idpersonne_reel():
    contract = listed(TeamworksContractSalaryControlProvider(Reader([rec(IDcontrat=7, IDpersonne=42)])))[0]
    assert contract.id == legacy_contract_uuid(7)
    assert contract.person_id == str(legacy_employee_uuid(42))
    assert contract.contract_type is ContractType.CDI
    assert contract.employment_regime is EmploymentRegime.CCNS_STANDARD
    assert contract.time_organization is TimeOrganization.WEEKLY_CONSTANT
    assert contract.start_date == date(2026, 1, 1)
    assert contract.monthly_gross_salary_amount == Decimal("2100.00")
    assert contract.weekly_hours == Decimal("35.00")
    assert contract.ccns_classification.code == "G3"


@pytest.mark.parametrize(
    ("label", "contract_type", "regime", "time_org"),
    [
        ("CDD", ContractType.CDD, EmploymentRegime.CCNS_STANDARD, TimeOrganization.WEEKLY_CONSTANT),
        ("CDII", ContractType.CDII, EmploymentRegime.CCNS_CDII, TimeOrganization.WEEKLY_CONSTANT),
        ("CEE", ContractType.CEE, EmploymentRegime.CEE, TimeOrganization.DAILY_CEE),
        ("APPRENTISSAGE", ContractType.APPRENTICESHIP, EmploymentRegime.APPRENTICE, TimeOrganization.WEEKLY_CONSTANT),
        ("STAGE", ContractType.INTERNSHIP, EmploymentRegime.STAGE_PFMP, TimeOrganization.WEEKLY_CONSTANT),
        ("SERVICE CIVIQUE", ContractType.CIVIC_SERVICE, EmploymentRegime.SERVICE_CIVIQUE, TimeOrganization.WEEKLY_CONSTANT),
        ("inconnu", ContractType.OTHER, EmploymentRegime.CCNS_STANDARD, TimeOrganization.WEEKLY_CONSTANT),
    ],
)
def test_convertit_les_types_de_contrats(label, contract_type, regime, time_org):
    contract = listed(TeamworksContractSalaryControlProvider(Reader([rec(type_contrat=label, date_fin="2026-12-31")])))[0]
    assert contract.contract_type is contract_type
    assert contract.employment_regime is regime
    assert contract.time_organization is time_org


def test_uuid_stables_et_espaces_separes():
    assert legacy_contract_uuid(12) == legacy_contract_uuid(12)
    assert legacy_employee_uuid(12) == legacy_employee_uuid(12)
    assert legacy_contract_uuid(12) != legacy_employee_uuid(12)


def test_conserve_ordre_filtres_et_supprime_doublons():
    records = [rec(1, 10), rec(2, 20), rec(1, 10), rec(3, 10)]
    provider = TeamworksContractSalaryControlProvider(Reader(records))
    result = listed(provider, contract_ids=(legacy_contract_uuid(3), legacy_contract_uuid(1)), employee_ids=(legacy_employee_uuid(10),))
    assert [item.id for item in result] == [legacy_contract_uuid(1), legacy_contract_uuid(3)]


def test_contrat_duree_determinee_sans_fin_conserve_non_evaluable():
    contract = listed(TeamworksContractSalaryControlProvider(Reader([rec(type_contrat="CDD", date_fin=None)])))[0]
    assert contract.contract_type is ContractType.CDD
    assert contract.end_date is None
    assert contract.legacy_salary_control_failure_reason == HISTORICAL_FIXED_TERM_WITHOUT_END_DATE_REASON
    grid = SalaryGridVersion(
        "G",
        "Grille",
        date(2026, 1, 1),
        (SalaryGridEntry(CCNSClassification(code="G3", label="G3"), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),),
    )
    smic = SmicVersion("S", "SMIC", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, Decimal("10.00"), Decimal("1800.00"), Decimal("35.00"), "test")
    service = ContractSalaryEvaluationService(ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid,))), SmicCatalog((smic,))))
    result = service.evaluate(contract, date(2026, 6, 1))
    assert result.failure_reason() is ContractSalaryEvaluationFailureReason.HISTORICAL_FIXED_TERM_MISSING_END_DATE


def test_propage_erreurs_techniques_et_lecteur_injecte():
    class Broken:
        def lire_contrats(self, limit=None):
            raise RuntimeError("base indisponible")

    with pytest.raises(RuntimeError, match="base"):
        listed(TeamworksContractSalaryControlProvider(Broken()))


def test_provider_immuable_sans_mutation_des_records():
    record = rec()
    before = record
    provider = TeamworksContractSalaryControlProvider(Reader([record]))
    listed(provider)
    assert record == before
    with pytest.raises(FrozenInstanceError):
        provider.data_reader = Reader([])
    with pytest.raises(ValueError, match="doublons"):
        listed(provider, contract_ids=(legacy_contract_uuid(1), legacy_contract_uuid(1)))
    with pytest.raises(TypeError, match="UUID"):
        listed(provider, employee_ids=(uuid4().hex,))
