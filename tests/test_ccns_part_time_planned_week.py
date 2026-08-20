from decimal import Decimal

from domain.convention.part_time_planned_week import (
    CCNSPartTimePlannedWeekService,
    PartTimePlannedWeekStatus,
)


SERVICE = CCNSPartTimePlannedWeekService()


def test_planned_48_hour_week_can_be_recorded_with_override_but_never_marked_compliant():
    result = SERVICE.evaluate(
        contractual_weekly_hours=Decimal("21.00"),
        planned_weekly_hours=Decimal("48.00"),
        manual_override_reason="Organisation vacances réellement planifiée",
    )
    assert result.status is PartTimePlannedWeekStatus.FULL_TIME_THRESHOLD_REACHED
    assert result.compliant is False
    assert result.recording_allowed is True
    assert result.manual_override_used is True
    assert result.can_be_marked_compliant is False
    assert "CCNS, article 5.2.4" in result.source_references
    assert "Code du travail, article L.3123-9" in result.source_references


def test_non_compliant_part_time_week_requires_reason_before_recording_override():
    result = SERVICE.evaluate(
        contractual_weekly_hours=Decimal("21.00"),
        planned_weekly_hours=Decimal("35.00"),
    )
    assert result.compliant is False
    assert result.requires_manual_override is True
    assert result.recording_allowed is False
    assert result.manual_override_used is False


def test_compliant_planned_week_needs_no_override():
    result = SERVICE.evaluate(
        contractual_weekly_hours=Decimal("21.00"),
        planned_weekly_hours=Decimal("28.00"),
    )
    assert result.compliant is True
    assert result.recording_allowed is True
    assert result.manual_override_used is False
    assert result.can_be_marked_compliant is True


def test_more_than_48_hours_is_separately_identified_even_when_recording_real_data():
    result = SERVICE.evaluate(
        contractual_weekly_hours=Decimal("21.00"),
        planned_weekly_hours=Decimal("49.00"),
        manual_override_reason="Saisie du réalisé pour audit",
    )
    assert result.status is PartTimePlannedWeekStatus.ABSOLUTE_WEEKLY_MAXIMUM_EXCEEDED
    assert result.recording_allowed is True
    assert result.compliant is False
