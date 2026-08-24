from decimal import Decimal

import pytest

from domain.convention.classification_rules import CCNSClassificationRulesService


SERVICE = CCNSClassificationRulesService()


def test_position_change_requires_remuneration_review_and_interview_report():
    result = SERVICE.evaluate_position_change(
        current_group_code="G3",
        evaluated_group_code="G3",
        position_definition_changed=True,
    )
    assert result.remuneration_review_required is True
    assert result.specific_interview_and_report_required is True
    assert result.reclassification_required is False


def test_position_change_to_higher_responsibility_group_requires_reclassification():
    result = SERVICE.evaluate_position_change(
        current_group_code="G3",
        evaluated_group_code="G4",
        position_definition_changed=True,
    )
    assert result.reclassification_required is True
    assert result.evaluated_group_code == "G4"


def test_no_position_change_does_not_trigger_automatic_review():
    result = SERVICE.evaluate_position_change(
        current_group_code="G3",
        evaluated_group_code="G4",
        position_definition_changed=False,
    )
    assert result.remuneration_review_required is False
    assert result.reclassification_required is False


def test_permanent_polyvalence_at_exactly_twenty_percent_does_not_trigger_reclassification():
    result = SERVICE.evaluate_permanent_polyvalence(
        current_group_code="G2",
        highest_activity_group_code="G4",
        highest_group_activity_ratio=Decimal("0.20"),
    )
    assert result.reclassification_required is False
    assert result.target_group_code == "G2"


def test_permanent_polyvalence_above_twenty_percent_uses_highest_group():
    result = SERVICE.evaluate_permanent_polyvalence(
        current_group_code="G2",
        highest_activity_group_code="G4",
        highest_group_activity_ratio=Decimal("0.2001"),
    )
    assert result.reclassification_required is True
    assert result.target_group_code == "G4"


def test_polyvalence_never_downgrades_current_group():
    result = SERVICE.evaluate_permanent_polyvalence(
        current_group_code="G5",
        highest_activity_group_code="G4",
        highest_group_activity_ratio=Decimal("0.80"),
    )
    assert result.reclassification_required is False
    assert result.target_group_code == "G5"


def test_exceptional_higher_function_requires_at_least_one_full_week():
    before = SERVICE.evaluate_exceptional_higher_function(
        current_group_code="G3",
        temporary_group_code="G4",
        continuous_duration_weeks=Decimal("0.99"),
        higher_position_occupied_for_whole_period=True,
    )
    threshold = SERVICE.evaluate_exceptional_higher_function(
        current_group_code="G3",
        temporary_group_code="G4",
        continuous_duration_weeks=Decimal("1.00"),
        higher_position_occupied_for_whole_period=True,
    )
    assert before.premium_due is False
    assert threshold.premium_due is True


def test_exceptional_higher_function_requires_whole_period_occupation():
    result = SERVICE.evaluate_exceptional_higher_function(
        current_group_code="G3",
        temporary_group_code="G4",
        continuous_duration_weeks=Decimal("2.00"),
        higher_position_occupied_for_whole_period=False,
    )
    assert result.premium_due is False


def test_exceptional_higher_function_can_compute_injected_remuneration_difference():
    result = SERVICE.evaluate_exceptional_higher_function(
        current_group_code="G3",
        temporary_group_code="G4",
        continuous_duration_weeks=Decimal("1.00"),
        higher_position_occupied_for_whole_period=True,
        current_group_remuneration_reference=Decimal("1997.87"),
        temporary_group_remuneration_reference=Decimal("2099.37"),
    )
    assert result.premium_due is True
    assert result.remuneration_difference_amount == Decimal("101.50")


def test_invalid_groups_and_ratios_are_rejected():
    with pytest.raises(ValueError):
        SERVICE.evaluate_permanent_polyvalence(
            current_group_code="G0",
            highest_activity_group_code="G4",
            highest_group_activity_ratio=Decimal("0.50"),
        )
    with pytest.raises(ValueError):
        SERVICE.evaluate_permanent_polyvalence(
            current_group_code="G2",
            highest_activity_group_code="G4",
            highest_group_activity_ratio=Decimal("1.01"),
        )
