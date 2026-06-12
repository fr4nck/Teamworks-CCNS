from datetime import date

from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.engine.default_rules import build_default_rules
from domain.engine.simple_checks import (
    check_contract_has_classification,
    check_contract_has_salary_grid,
)


def build_contract() -> Contract:
    return Contract(
        person_id="person-1",
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2026, 9, 1),
    )


def test_default_rules_are_created():
    rules = build_default_rules()
    assert len(rules) >= 5


def test_contract_without_classification_creates_anomaly():
    contract = build_contract()
    result, anomaly = check_contract_has_classification(contract)
    assert anomaly is not None
    assert anomaly.code == "CONTRAT_SANS_CLASSIFICATION"
    assert result.status.value == "DATA_ERROR"


def test_contract_without_salary_grid_creates_anomaly():
    contract = build_contract()
    result, anomaly = check_contract_has_salary_grid(contract)
    assert anomaly is not None
    assert anomaly.code == "CONTRAT_SANS_GRILLE"
    assert result.status.value == "DATA_ERROR"
