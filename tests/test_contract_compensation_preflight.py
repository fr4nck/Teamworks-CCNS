from datetime import date
from decimal import Decimal, localcontext

from application.control.contract_compensation_preflight import (
    validate_cee_daily_compensation,
    validate_ccns_monthly_compensation,
)


def test_ccns_preflight_blocks_salary_below_retained_minimum():
    result = validate_ccns_monthly_compensation(
        group_code="G1",
        reference_date=date(2026, 8, 19),
        weekly_hours=Decimal("35.00"),
        gross_monthly_salary=Decimal("1850.00"),
    )
    assert result.compliant is False
    assert result.required_minimum == Decimal("1867.02")


def test_ccns_preflight_accepts_compliant_salary_under_low_decimal_precision():
    with localcontext() as context:
        context.prec = 5
        result = validate_ccns_monthly_compensation(
            group_code="G1",
            reference_date=date(2026, 8, 19),
            weekly_hours=Decimal("35.00"),
            gross_monthly_salary=Decimal("1900.00"),
        )
    assert result.compliant is True
    assert result.required_minimum == Decimal("1867.02")


def test_ccns_preflight_does_not_fake_monthly_control_for_g7():
    result = validate_ccns_monthly_compensation(
        group_code="G7",
        reference_date=date(2026, 8, 19),
        weekly_hours=Decimal("35.00"),
        gross_monthly_salary=None,
    )
    assert result.compliant is True
    assert result.control_scope == "CCNS_ANNUAL"
    assert result.required_minimum == Decimal("40597.94")


def test_cee_preflight_requires_applicable_employer_rate():
    result = validate_cee_daily_compensation(
        qualification="BAFA_HOLDER",
        employer_daily_rate=None,
        legal_minimum_daily_rate=Decimal("52.93"),
    )
    assert result.compliant is False


def test_cee_preflight_blocks_rate_below_legal_minimum():
    result = validate_cee_daily_compensation(
        qualification="BAFA_TRAINEE",
        employer_daily_rate=Decimal("50.00"),
        legal_minimum_daily_rate=Decimal("52.93"),
    )
    assert result.compliant is False
    assert result.required_minimum == Decimal("52.93")


def test_cee_preflight_accepts_distinct_compliant_employer_rate():
    result = validate_cee_daily_compensation(
        qualification="BAFA_HOLDER",
        employer_daily_rate=Decimal("65.00"),
        legal_minimum_daily_rate=Decimal("52.93"),
    )
    assert result.compliant is True
    assert result.proposed_amount == Decimal("65.00")
