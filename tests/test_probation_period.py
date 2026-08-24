from datetime import date

import pytest

from domain.contracts.contract_operation import ContractOperation
from domain.contracts.contract_type import ContractType
from domain.contracts.probation_period import (
    ProbationUnit,
    probation_calendar_days,
    propose_ccns_probation_period,
)


def test_new_ccns_cdi_uses_group_category_months() -> None:
    assert propose_ccns_probation_period(
        contract_type=ContractType.CDI,
        operation=ContractOperation.NEW,
        start_date=date(2026, 9, 1),
        ccns_group="G1",
    ).value == 1
    assert propose_ccns_probation_period(
        contract_type=ContractType.CDI,
        operation=ContractOperation.NEW,
        start_date=date(2026, 9, 1),
        ccns_group="G4",
    ).value == 2
    proposal = propose_ccns_probation_period(
        contract_type=ContractType.CDI,
        operation=ContractOperation.NEW,
        start_date=date(2026, 9, 1),
        ccns_group="G7",
    )
    assert proposal.value == 3
    assert proposal.unit is ProbationUnit.MONTH


def test_new_cdd_is_one_day_per_week_with_legal_caps() -> None:
    four_weeks = propose_ccns_probation_period(
        contract_type=ContractType.CDD,
        operation=ContractOperation.NEW,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 28),
    )
    assert (four_weeks.value, four_weeks.unit) == (4, ProbationUnit.DAY)

    four_months = propose_ccns_probation_period(
        contract_type=ContractType.CDD,
        operation=ContractOperation.NEW,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 12, 31),
    )
    assert (four_months.value, four_months.unit) == (14, ProbationUnit.DAY)

    eight_months = propose_ccns_probation_period(
        contract_type=ContractType.CDD,
        operation=ContractOperation.NEW,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 8, 31),
    )
    assert (eight_months.value, eight_months.unit) == (1, ProbationUnit.MONTH)


def test_cdd_renewal_never_recreates_probation() -> None:
    proposal = propose_ccns_probation_period(
        contract_type=ContractType.CDD,
        operation=ContractOperation.CDD_RENEWAL,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 12, 31),
    )
    assert proposal.value == 0
    assert proposal.automatic is True


def test_cdd_to_cdi_deducts_previous_cdd_duration() -> None:
    proposal = propose_ccns_probation_period(
        contract_type=ContractType.CDI,
        operation=ContractOperation.CDD_TO_CDI,
        start_date=date(2026, 9, 1),
        ccns_group="G4",
        previous_contract_start=date(2026, 7, 1),
        previous_contract_end=date(2026, 8, 31),
    )
    assert proposal.value == 0
    assert proposal.unit is ProbationUnit.DAY


def test_cdd_to_cdi_keeps_only_the_remaining_trial_duration() -> None:
    proposal = propose_ccns_probation_period(
        contract_type=ContractType.CDI,
        operation=ContractOperation.CDD_TO_CDI,
        start_date=date(2026, 9, 1),
        ccns_group="G7",
        previous_contract_start=date(2026, 8, 1),
        previous_contract_end=date(2026, 8, 31),
    )
    # Trois mois théoriques à partir du 1er septembre = 91 jours ; le CDD
    # précédent compte 31 jours calendaires, il reste donc 60 jours.
    assert proposal.value == 60
    assert proposal.unit is ProbationUnit.DAY


def test_month_unit_uses_real_calendar_length_for_legacy_days() -> None:
    assert probation_calendar_days(
        start_date=date(2026, 2, 1), value=1, unit=ProbationUnit.MONTH
    ) == 28
    assert probation_calendar_days(
        start_date=date(2026, 9, 1), value=3, unit=ProbationUnit.MONTH
    ) == 91


def test_operation_type_must_match_resulting_contract_type() -> None:
    with pytest.raises(ValueError):
        propose_ccns_probation_period(
            contract_type=ContractType.CDI,
            operation=ContractOperation.CDD_RENEWAL,
            start_date=date(2026, 9, 1),
        )
