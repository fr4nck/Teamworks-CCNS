from decimal import Decimal

from application.control.contract_compensation_preflight import ContractCompensationPreflight
from application.control.contract_final_preflight import (
    ContractFinalPreflightDecision,
    ContractFinalPreflightService,
)
from domain.contracts.cee_contract_guardrails import CEEContractGuardrailService


SERVICE = ContractFinalPreflightService()


def compensation(ok=True):
    return ContractCompensationPreflight(ok, "ok" if ok else "salaire insuffisant")


def test_compensation_failure_blocks_finalization():
    result = SERVICE.evaluate(compensation=compensation(False))
    assert result.decision is ContractFinalPreflightDecision.BLOCKED
    assert result.can_finalize is False


def test_cee_80_day_violation_blocks_finalization():
    guardrail = CEEContractGuardrailService().evaluate(
        days_rolling_12_months=81,
        worker_age_years=25,
    )
    result = SERVICE.evaluate(compensation=compensation(), cee_guardrails=guardrail)
    assert result.decision is ContractFinalPreflightDecision.BLOCKED
    assert "80 jours" in " ".join(result.blocking_messages())


def test_incomplete_cee_data_requests_review_but_does_not_block():
    guardrail = CEEContractGuardrailService().evaluate(
        days_rolling_12_months=None,
        worker_age_years=25,
    )
    result = SERVICE.evaluate(compensation=compensation(), cee_guardrails=guardrail)
    assert result.decision is ContractFinalPreflightDecision.REVIEW
    assert result.can_finalize is True


def test_minor_schedule_violation_blocks():
    guardrail = CEEContractGuardrailService().evaluate(
        days_rolling_12_months=10,
        worker_age_years=17,
        planned_max_daily_hours=Decimal("7.00"),
        planned_max_weekly_hours=Decimal("36.00"),
    )
    result = SERVICE.evaluate(compensation=compensation(), cee_guardrails=guardrail)
    assert result.decision is ContractFinalPreflightDecision.BLOCKED
