from decimal import Decimal

import pytest

from domain.convention.part_time_working_time import (
    CCNSPartTimeWorkingTimeService,
    PartTimeMinimumStatus,
)


SERVICE = CCNSPartTimeWorkingTimeService()


@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (1, "2.00"),
        (2, "3.00"),
        (3, "5.00"),
        (4, "8.00"),
        (5, "10.00"),
        (6, "24.00"),
    ],
)
def test_minimum_weekly_hours_depends_on_number_of_worked_days(days, expected):
    assert SERVICE.minimum_weekly_hours_for_days(days) == Decimal(expected)


def test_six_day_minimum_is_injected_from_current_legislation_instead_of_hardcoded():
    assert SERVICE.minimum_weekly_hours_for_days(
        6,
        legal_minimum_for_six_days=Decimal("22.00"),
    ) == Decimal("22.00")


def test_annual_cycle_minimum_is_304_hours_and_can_be_prorated_explicitly():
    assert SERVICE.annual_cycle_minimum_hours() == Decimal("304.0000")
    assert SERVICE.annual_cycle_minimum_hours(Decimal("0.50")) == Decimal("152.0000")


def test_short_part_time_is_rejected_when_post_is_cdii_eligible_and_cdii_is_usable():
    result = SERVICE.evaluate_minimum(
        contractual_weekly_hours=Decimal("21.00"),
        days_per_worked_week=3,
        job_eligible_for_cdii=True,
        organization_allows_cdii=True,
    )
    assert result.status is PartTimeMinimumStatus.COMPLIANT
    assert result.minimum_compliant is True
    assert result.requires_non_cdii_route_justification is True
    assert result.compliant is False
    assert result.short_part_time_ccns_route_allowed is False


def test_short_part_time_route_is_allowed_when_organization_does_not_allow_cdii():
    result = SERVICE.evaluate_minimum(
        contractual_weekly_hours=Decimal("21.00"),
        days_per_worked_week=3,
        job_eligible_for_cdii=True,
        organization_allows_cdii=False,
    )
    assert result.status is PartTimeMinimumStatus.COMPLIANT
    assert result.minimum_weekly_hours == Decimal("5.00")


def test_contract_below_distribution_minimum_is_reported():
    result = SERVICE.evaluate_minimum(
        contractual_weekly_hours=Decimal("4.00"),
        days_per_worked_week=3,
        job_eligible_for_cdii=False,
        organization_allows_cdii=False,
    )
    assert result.status is PartTimeMinimumStatus.BELOW_MINIMUM
    assert result.minimum_weekly_hours == Decimal("5.00")


def test_validated_student_derogation_removes_conventional_minimum():
    result = SERVICE.evaluate_minimum(
        contractual_weekly_hours=Decimal("1.50"),
        days_per_worked_week=1,
        job_eligible_for_cdii=False,
        organization_allows_cdii=False,
        student_under_26_derogation=True,
    )
    assert result.status is PartTimeMinimumStatus.DEROGATION_APPLIES
    assert result.minimum_weekly_hours is None
    assert result.minimum_compliant is True
    assert result.compliant is True


def test_validated_employee_requested_derogation_removes_conventional_minimum():
    result = SERVICE.evaluate_minimum(
        contractual_weekly_hours=Decimal("1.50"),
        days_per_worked_week=1,
        job_eligible_for_cdii=False,
        organization_allows_cdii=False,
        employee_requested_derogation=True,
    )
    assert result.status is PartTimeMinimumStatus.DEROGATION_APPLIES
    assert result.minimum_weekly_hours is None


def test_complementary_hours_are_limited_to_one_third_and_below_35_hours():
    ok = SERVICE.evaluate_complementary_hours(
        contractual_weekly_hours=Decimal("21.00"),
        complementary_hours=Decimal("7.00"),
    )
    too_many = SERVICE.evaluate_complementary_hours(
        contractual_weekly_hours=Decimal("21.00"),
        complementary_hours=Decimal("7.01"),
    )
    assert ok.one_third_limit_hours == Decimal("7.00")
    assert ok.compliant is True
    assert too_many.compliant is False


def test_complementary_hours_can_never_reach_35_hours_even_if_one_third_allows_it():
    result = SERVICE.evaluate_complementary_hours(
        contractual_weekly_hours=Decimal("27.00"),
        complementary_hours=Decimal("8.00"),
    )
    assert result.within_one_third_limit is True
    assert result.below_legal_duration is False
    assert result.compliant is False


def test_employee_must_perform_only_up_to_ten_percent_of_contractual_hours():
    mandatory = SERVICE.evaluate_complementary_hours(
        contractual_weekly_hours=Decimal("20.00"),
        complementary_hours=Decimal("2.00"),
    )
    above = SERVICE.evaluate_complementary_hours(
        contractual_weekly_hours=Decimal("20.00"),
        complementary_hours=Decimal("2.01"),
    )
    assert mandatory.employee_must_perform is True
    assert above.employee_must_perform is False
    assert mandatory.increase_rate == Decimal("0.10")


def test_hours_amendments_are_limited_to_eight_and_nine_weeks_per_year():
    ok = SERVICE.evaluate_hours_amendment_capacity(
        amendments_used_before=7,
        weeks_used_before=7,
        planned_weeks=2,
    )
    ninth = SERVICE.evaluate_hours_amendment_capacity(
        amendments_used_before=8,
        weeks_used_before=7,
        planned_weeks=1,
    )
    tenth_week = SERVICE.evaluate_hours_amendment_capacity(
        amendments_used_before=3,
        weeks_used_before=9,
        planned_weeks=1,
    )
    assert ok.compliant is True
    assert ninth.amendment_count_compliant is False
    assert tenth_week.weeks_count_compliant is False


def test_replacement_of_at_least_one_month_does_not_consume_nine_week_quota():
    result = SERVICE.evaluate_hours_amendment_capacity(
        amendments_used_before=2,
        weeks_used_before=9,
        planned_weeks=5,
        replacement_at_least_one_month=True,
    )
    assert result.counted_weeks_after == 9
    assert result.weeks_count_compliant is True
    assert result.compliant is True
    assert result.overtime_beyond_amendment_increase_rate == Decimal("0.25")


def test_invalid_part_time_values_are_rejected():
    with pytest.raises(ValueError):
        SERVICE.minimum_weekly_hours_for_days(0)
    with pytest.raises(ValueError):
        SERVICE.evaluate_complementary_hours(
            contractual_weekly_hours=Decimal("35.00"),
            complementary_hours=Decimal("0.00"),
        )


def test_individual_minimum_derogation_does_not_hide_cdii_route_check():
    result = SERVICE.evaluate_minimum(
        contractual_weekly_hours=Decimal("4.00"),
        days_per_worked_week=3,
        job_eligible_for_cdii=True,
        organization_allows_cdii=True,
        student_under_26_derogation=True,
    )
    assert result.status is PartTimeMinimumStatus.DEROGATION_APPLIES
    assert result.minimum_compliant is True
    assert result.requires_non_cdii_route_justification is True
    assert result.compliant is False
