from decimal import Decimal, getcontext

import pytest

from domain.convention.seniority import CCNSSeniorityService


SMC_G3_2026 = Decimal("1997.87")


def evaluate(group: str, effective: int, company: int, ratio: str = "1.00"):
    return CCNSSeniorityService().evaluate(
        group_code=group,
        effective_work_months=effective,
        company_seniority_months=company,
        smc_group3_monthly_amount=SMC_G3_2026,
        work_ratio=Decimal(ratio),
    )


def test_groups_7_and_8_are_outside_standard_seniority_rule():
    result = evaluate("G7", 240, 240)
    assert result.applicable is False
    assert result.total_rate_percent == Decimal("0.00")
    assert result.monthly_due_amount == Decimal("0.00")


def test_first_percent_starts_at_24_effective_work_months():
    before = evaluate("G2", 23, 23)
    at_threshold = evaluate("G2", 24, 24)

    assert before.total_rate_percent == Decimal("0.00")
    assert before.next_standard_increment_at_effective_work_month == 24
    assert at_threshold.standard_rate_percent == Decimal("1.00")
    assert at_threshold.total_rate_percent == Decimal("1.00")
    assert at_threshold.full_time_reference_amount == Decimal("19.98")
    assert at_threshold.next_standard_increment_at_effective_work_month == 48


def test_standard_rate_increases_one_percent_each_24_effective_months():
    result = evaluate("G4", 120, 120)
    assert result.standard_rate_percent == Decimal("5.00")
    assert result.total_rate_percent == Decimal("5.00")
    assert result.full_time_reference_amount == Decimal("99.89")


def test_group_1_gets_exceptional_five_percent_after_three_years_company_seniority():
    result = evaluate("G1", 36, 36)
    assert result.standard_rate_percent == Decimal("1.00")
    assert result.g1_exceptional_rate_percent == Decimal("5.00")
    assert result.total_rate_percent == Decimal("6.00")
    assert result.full_time_reference_amount == Decimal("119.87")
    assert result.next_g1_exceptional_at_company_seniority_month is None


def test_group_1_exceptional_component_is_not_granted_before_36_company_months():
    result = evaluate("G1", 36, 35)
    assert result.standard_rate_percent == Decimal("1.00")
    assert result.g1_exceptional_rate_percent == Decimal("0.00")
    assert result.total_rate_percent == Decimal("1.00")
    assert result.next_g1_exceptional_at_company_seniority_month == 36


def test_total_rate_is_capped_at_fifteen_percent_including_group_1_exceptional_component():
    result = evaluate("G1", 240, 240)
    assert result.standard_rate_percent == Decimal("10.00")
    assert result.g1_exceptional_rate_percent == Decimal("5.00")
    assert result.total_rate_percent == Decimal("15.00")
    assert result.full_time_reference_amount == Decimal("299.68")
    assert result.next_standard_increment_at_effective_work_month is None


def test_monthly_amount_is_prorated_from_unrounded_reference():
    result = evaluate("G3", 48, 48, "0.60")
    assert result.total_rate_percent == Decimal("2.00")
    assert result.full_time_reference_amount == Decimal("39.96")
    assert result.monthly_due_amount == Decimal("23.97")


def test_calculation_is_independent_from_global_decimal_precision():
    previous = getcontext().prec
    try:
        getcontext().prec = 2
        result = evaluate("G1", 36, 36)
    finally:
        getcontext().prec = previous
    assert result.full_time_reference_amount == Decimal("119.87")


def test_invalid_inputs_are_rejected_explicitly():
    service = CCNSSeniorityService()
    with pytest.raises(TypeError):
        service.evaluate(
            group_code="G3",
            effective_work_months=24.0,
            company_seniority_months=24,
            smc_group3_monthly_amount=SMC_G3_2026,
        )
    with pytest.raises(ValueError):
        evaluate("G3", -1, 10)
    with pytest.raises(ValueError):
        evaluate("G3", 24, 24, "1.01")
