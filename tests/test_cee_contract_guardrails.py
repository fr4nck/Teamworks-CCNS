from decimal import Decimal

from domain.contracts.cee_contract_guardrails import CEEContractGuardrailService


SERVICE = CEEContractGuardrailService()


def test_cee_80_day_limit_is_inclusive():
    ok = SERVICE.evaluate(days_rolling_12_months=80, worker_age_years=20)
    too_many = SERVICE.evaluate(days_rolling_12_months=81, worker_age_years=20)
    assert ok.days_limit_compliant is True
    assert too_many.days_limit_compliant is False
    assert too_many.has_known_non_compliance is True


def test_missing_day_count_never_becomes_implicit_compliance():
    result = SERVICE.evaluate(days_rolling_12_months=None, worker_age_years=20)
    assert result.days_limit_compliant is None
    assert result.requires_review is True
    assert result.compliant is False


def test_48_hour_average_is_checked_when_known():
    result = SERVICE.evaluate(
        days_rolling_12_months=20,
        average_weekly_hours_all_contracts_6m=Decimal("48.01"),
        worker_age_years=20,
        require_average_hours_check=True,
    )
    assert result.average_hours_compliant is False
    assert result.has_known_non_compliance is True


def test_unknown_48_hour_average_requires_review_only_when_requested():
    optional = SERVICE.evaluate(
        days_rolling_12_months=20,
        worker_age_years=20,
        require_average_hours_check=False,
    )
    required = SERVICE.evaluate(
        days_rolling_12_months=20,
        worker_age_years=20,
        require_average_hours_check=True,
    )
    assert optional.requires_review is False
    assert required.requires_review is True


def test_minor_cee_uses_8h_daily_and_35h_weekly_animation_limits():
    result = SERVICE.evaluate(
        days_rolling_12_months=15,
        worker_age_years=17,
        planned_max_daily_hours=Decimal("8.00"),
        planned_max_weekly_hours=Decimal("35.00"),
    )
    assert result.is_minor is True
    assert result.minor_daily_hours_compliant is True
    assert result.minor_weekly_hours_compliant is True
    assert result.compliant is True


def test_minor_cee_over_35_hours_is_non_compliant():
    result = SERVICE.evaluate(
        days_rolling_12_months=15,
        worker_age_years=17,
        planned_max_daily_hours=Decimal("7.00"),
        planned_max_weekly_hours=Decimal("35.01"),
    )
    assert result.minor_weekly_hours_compliant is False
    assert result.has_known_non_compliance is True


def test_minor_without_schedule_requires_review_instead_of_guessing():
    result = SERVICE.evaluate(
        days_rolling_12_months=15,
        worker_age_years=17,
    )
    assert result.minor_daily_hours_compliant is None
    assert result.minor_weekly_hours_compliant is None
    assert result.requires_review is True
