from decimal import Decimal

import pytest

from domain.convention.working_time_scenarios import WorkingTimeScenarioService


SERVICE = WorkingTimeScenarioService()


def test_pmsl_vacation_48_to_35_cap_costs_143_hours_after_five_weeks_leave():
    result = SERVICE.vacation_week_cap_impact(
        total_vacation_weeks=16,
        paid_leave_weeks_in_vacations=5,
        current_vacation_week_hours=Decimal("48.00"),
        capped_vacation_week_hours=Decimal("35.00"),
        school_weeks=36,
    )
    assert result.worked_vacation_weeks == 11
    assert result.current_vacation_hours == Decimal("528.00")
    assert result.capped_vacation_hours == Decimal("385.00")
    assert result.annual_hours_lost == Decimal("143.00")
    assert result.equivalent_hours_per_school_week == Decimal("3.972222222222222222222222222")


def test_scenario_does_not_create_negative_loss_when_cap_is_higher():
    result = SERVICE.vacation_week_cap_impact(
        total_vacation_weeks=10,
        paid_leave_weeks_in_vacations=2,
        current_vacation_week_hours=Decimal("30.00"),
        capped_vacation_week_hours=Decimal("35.00"),
        school_weeks=36,
    )
    assert result.annual_hours_lost == Decimal("0.00")


def test_scenario_rejects_more_leave_than_vacation_weeks():
    with pytest.raises(ValueError):
        SERVICE.vacation_week_cap_impact(
            total_vacation_weeks=4,
            paid_leave_weeks_in_vacations=5,
            current_vacation_week_hours=Decimal("48.00"),
            capped_vacation_week_hours=Decimal("35.00"),
            school_weeks=36,
        )
