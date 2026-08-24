from datetime import date

import pytest

from domain.convention.seniority_timeline import CCNSContractSeniorityTimelineService


SERVICE = CCNSContractSeniorityTimelineService()


def test_current_contract_months_are_counted_automatically():
    result = SERVICE.evaluate(
        current_contract_start=date(2025, 9, 1),
        evaluation_date=date(2026, 8, 21),
        recognized_effective_work_months_at_start=24,
        recognized_company_seniority_months_at_start=24,
    )
    assert result.elapsed_contract_months == 11
    assert result.effective_work_months == 35
    assert result.company_seniority_months == 35
    assert result.history_complete is True


def test_end_of_month_anniversary_is_clamped_correctly():
    result = SERVICE.evaluate(
        current_contract_start=date(2024, 1, 31),
        evaluation_date=date(2024, 2, 29),
        recognized_effective_work_months_at_start=0,
        recognized_company_seniority_months_at_start=0,
    )
    assert result.elapsed_contract_months == 1


def test_closed_contract_stops_accruing_after_its_end():
    result = SERVICE.evaluate(
        current_contract_start=date(2024, 1, 1),
        current_contract_end=date(2024, 12, 31),
        evaluation_date=date(2026, 8, 21),
        recognized_effective_work_months_at_start=12,
        recognized_company_seniority_months_at_start=12,
    )
    assert result.elapsed_contract_months == 11
    assert result.company_seniority_months == 23


def test_unconfirmed_prior_history_never_hides_current_contract_accrual():
    result = SERVICE.evaluate(
        current_contract_start=date(2024, 8, 21),
        evaluation_date=date(2026, 8, 21),
    )
    assert result.elapsed_contract_months == 24
    assert result.effective_work_months == 24
    assert result.company_seniority_months == 24
    assert result.history_complete is False
    assert result.prior_history_requires_review is True


def test_validated_non_effective_months_only_reduce_effective_work_counter():
    result = SERVICE.evaluate(
        current_contract_start=date(2024, 8, 21),
        evaluation_date=date(2026, 8, 21),
        recognized_effective_work_months_at_start=12,
        recognized_company_seniority_months_at_start=12,
        excluded_current_contract_effective_months=3,
    )
    assert result.current_contract_effective_months == 21
    assert result.effective_work_months == 33
    assert result.company_seniority_months == 36


def test_exclusions_cannot_exceed_elapsed_contract_months():
    with pytest.raises(ValueError):
        SERVICE.evaluate(
            current_contract_start=date(2026, 1, 1),
            evaluation_date=date(2026, 8, 21),
            excluded_current_contract_effective_months=8,
        )
