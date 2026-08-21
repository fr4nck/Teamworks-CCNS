from datetime import date
from decimal import Decimal

from domain.contracts.ccns_contract_mentions import (
    CCNSContractComplianceService,
    ContractTermsSnapshot,
)
from domain.contracts.contract_rules_preflight import (
    CCNSContractRulesPreflightService,
    ContractPreflightDecision,
)
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.convention.classification_rules import CCNSClassificationRulesService
from domain.convention.part_time_planned_week import CCNSPartTimePlannedWeekService
from domain.convention.seniority import CCNSSeniorityService
from domain.convention.seniority_timeline import CCNSContractSeniorityTimelineService


PREFLIGHT = CCNSContractRulesPreflightService()
MENTIONS = CCNSContractComplianceService()
TIMELINE = CCNSContractSeniorityTimelineService()
SENIORITY = CCNSSeniorityService()
PART_TIME_WEEK = CCNSPartTimePlannedWeekService()
CLASSIFICATION = CCNSClassificationRulesService()


def _complete_mentions(*, weekly_hours=Decimal("35.00")):
    empty = ContractTermsSnapshot(
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        weekly_reference_hours=weekly_hours,
        work_ratio=weekly_hours / Decimal("35.00"),
        is_foreign_worker=False,
        values={},
    )
    values = {requirement.code: "ok" for requirement in MENTIONS.requirements_for(empty)}
    snapshot = ContractTermsSnapshot(
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        weekly_reference_hours=weekly_hours,
        work_ratio=weekly_hours / Decimal("35.00"),
        is_foreign_worker=False,
        values=values,
    )
    return MENTIONS.evaluate(snapshot)


def _seniority(*, history_complete=True, effective=0, company=0, group="G3"):
    timeline = TIMELINE.evaluate(
        current_contract_start=date(2026, 1, 1),
        evaluation_date=date(2026, 8, 21),
        recognized_effective_work_months_at_start=effective if history_complete else None,
        recognized_company_seniority_months_at_start=company if history_complete else None,
    )
    result = SENIORITY.evaluate(
        group_code=group,
        effective_work_months=timeline.effective_work_months,
        company_seniority_months=timeline.company_seniority_months,
        smc_group3_monthly_amount=Decimal("1997.87"),
    )
    return timeline, result


def test_clean_contract_is_ok():
    timeline, seniority = _seniority()
    result = PREFLIGHT.evaluate(
        seniority_timeline=timeline,
        seniority=seniority,
        mentions=_complete_mentions(),
        compensation_compliant=True,
    )
    assert result.decision is ContractPreflightDecision.OK
    assert result.can_finalize_contract is True


def test_current_contract_is_counted_even_when_prior_history_needs_review():
    timeline, seniority = _seniority(history_complete=False)
    assert timeline.elapsed_contract_months == 7
    result = PREFLIGHT.evaluate(
        seniority_timeline=timeline,
        seniority=seniority,
        mentions=_complete_mentions(),
        compensation_compliant=True,
    )
    assert result.decision is ContractPreflightDecision.REVIEW
    assert any(issue.code == "SENIORITY_PRIOR_HISTORY_UNCONFIRMED" for issue in result.issues)


def test_missing_mandatory_mentions_block_finalization():
    timeline, seniority = _seniority()
    empty_snapshot = ContractTermsSnapshot(
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        weekly_reference_hours=Decimal("35.00"),
        work_ratio=Decimal("1.00"),
        is_foreign_worker=False,
        values={},
    )
    result = PREFLIGHT.evaluate(
        seniority_timeline=timeline,
        seniority=seniority,
        mentions=MENTIONS.evaluate(empty_snapshot),
        compensation_compliant=True,
    )
    assert result.decision is ContractPreflightDecision.BLOCKED
    assert result.can_finalize_contract is False


def test_48_hour_part_time_week_with_reason_is_recordable_but_never_compliant():
    timeline, seniority = _seniority()
    week = PART_TIME_WEEK.evaluate(
        contractual_weekly_hours=Decimal("21.00"),
        planned_weekly_hours=Decimal("48.00"),
        manual_override_reason="Période de vacances planifiée et validée manuellement.",
    )
    result = PREFLIGHT.evaluate(
        seniority_timeline=timeline,
        seniority=seniority,
        mentions=_complete_mentions(weekly_hours=Decimal("21.00")),
        part_time_week=week,
        compensation_compliant=True,
    )
    assert week.compliant is False
    assert week.recording_allowed is True
    assert result.decision is ContractPreflightDecision.REVIEW
    assert result.can_finalize_contract is True


def test_non_compliant_part_time_week_without_reason_blocks_recording():
    timeline, seniority = _seniority()
    week = PART_TIME_WEEK.evaluate(
        contractual_weekly_hours=Decimal("21.00"),
        planned_weekly_hours=Decimal("48.00"),
    )
    result = PREFLIGHT.evaluate(
        seniority_timeline=timeline,
        seniority=seniority,
        mentions=_complete_mentions(weekly_hours=Decimal("21.00")),
        part_time_week=week,
        compensation_compliant=True,
    )
    assert result.decision is ContractPreflightDecision.BLOCKED


def test_seniority_premium_is_informational_when_history_is_complete():
    timeline, seniority = _seniority(effective=24, company=24)
    result = PREFLIGHT.evaluate(
        seniority_timeline=timeline,
        seniority=seniority,
        mentions=_complete_mentions(),
        compensation_compliant=True,
    )
    assert seniority.monthly_due_amount > Decimal("0.00")
    assert result.decision is ContractPreflightDecision.OK
    assert any(issue.code == "SENIORITY_PREMIUM_DUE" for issue in result.issues)


def test_reclassification_required_is_blocking():
    timeline, seniority = _seniority()
    position = CLASSIFICATION.evaluate_position_change(
        current_group_code="G3",
        evaluated_group_code="G4",
        position_definition_changed=True,
    )
    result = PREFLIGHT.evaluate(
        seniority_timeline=timeline,
        seniority=seniority,
        mentions=_complete_mentions(),
        compensation_compliant=True,
        position_change=position,
    )
    assert result.decision is ContractPreflightDecision.BLOCKED
    assert any(issue.code == "CLASSIFICATION_RECLASSIFICATION_REQUIRED" for issue in result.issues)
