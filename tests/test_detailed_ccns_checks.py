from datetime import date

from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.engine.detailed_checks import (
    check_short_part_time_majoration,
    check_seniority_applicability,
    check_cee_max_days,
    check_apprenticeship_bar_scale,
)
from domain.engine.default_rules_ccns import build_default_ccns_rules


def _contract(classification_code: str | None = None) -> Contract:
    return Contract(
        person_id="person-1",
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2026, 9, 1),
        ccns_classification_code=classification_code,
    )


def test_short_part_time_majoration_for_9_hours():
    contract = _contract("G2")
    contract.weekly_reference_hours = 9
    result, anomaly = check_short_part_time_majoration(contract)
    assert anomaly is None
    assert result.retained_coefficient == 1.05


def test_short_part_time_majoration_for_15_hours():
    contract = _contract("G2")
    contract.weekly_reference_hours = 15
    result, anomaly = check_short_part_time_majoration(contract)
    assert anomaly is None
    assert result.retained_coefficient == 1.02


def test_short_part_time_majoration_for_24_hours():
    contract = _contract("G2")
    contract.weekly_reference_hours = 24
    result, anomaly = check_short_part_time_majoration(contract)
    assert anomaly is None
    assert result.retained_coefficient == 1.00


def test_seniority_applies_to_group_4():
    contract = _contract("G4")
    result, anomaly = check_seniority_applicability(contract)
    assert anomaly is None
    assert result.theoretical_value == 1.0


def test_seniority_not_applicable_to_group_7():
    contract = _contract("G7")
    result, anomaly = check_seniority_applicability(contract)
    assert anomaly is None
    assert result.theoretical_value == 0.0


def test_cee_limit_exceeded():
    contract = Contract(
        person_id="person-1",
        contract_type=ContractType.CEE,
        employment_regime=EmploymentRegime.CEE,
        time_organization=TimeOrganization.DAILY_CEE,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
    )
    result, anomaly = check_cee_max_days(82, contract)
    assert anomaly is not None
    assert anomaly.code == "CEE_DEPASSEMENT_80_JOURS"


def test_apprenticeship_scale_for_18_years_second_year():
    contract = Contract(
        person_id="person-1",
        contract_type=ContractType.APPRENTICESHIP,
        employment_regime=EmploymentRegime.APPRENTICE,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2026, 9, 1),
        end_date=date(2027, 8, 31),
    )
    result, anomaly = check_apprenticeship_bar_scale(age=18, execution_year=2, contract=contract)
    assert anomaly is None
    assert result.theoretical_value == 51.0


def test_default_ccns_rules_exist():
    rules = build_default_ccns_rules()
    assert len(rules) >= 4
