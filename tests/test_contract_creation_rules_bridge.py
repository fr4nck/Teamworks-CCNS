from datetime import date
from decimal import Decimal

import application.control.contract_creation_rules_bridge as bridge
from application.control.contract_compensation_preflight import ContractCompensationPreflight
from domain.contracts.contract_rules_preflight import ContractPreflightDecision


class Choice:
    def __init__(self, code, amount):
        self.code = code
        self.minimum_amount = Decimal(amount)


class Presenter:
    def group_choices(self, reference_date):
        return (Choice("G3", "1997.87"),)


def setup_module():
    bridge.CCNSContractCompliancePresenter = Presenter


def test_current_contract_seniority_accrues_when_no_prior_history_exists():
    result = bridge.build_ccns_creation_rules_preflight(
        group_code="G2",
        reference_date=date(2024, 1, 1),
        current_contract_start=date(2024, 1, 1),
        evaluation_date=date(2026, 1, 1),
        weekly_hours=Decimal("35.00"),
        compensation=ContractCompensationPreflight(True, "ok"),
        history_known_absent=True,
    )
    assert result.seniority_timeline.effective_work_months == 24
    assert result.seniority.total_rate_percent == Decimal("1.00")
    assert result.decision is ContractPreflightDecision.OK


def test_unknown_prior_history_keeps_current_contract_calculation_but_requests_review():
    result = bridge.build_ccns_creation_rules_preflight(
        group_code="G2",
        reference_date=date(2024, 1, 1),
        current_contract_start=date(2024, 1, 1),
        evaluation_date=date(2026, 1, 1),
        weekly_hours=Decimal("35.00"),
        compensation=ContractCompensationPreflight(True, "ok"),
    )
    assert result.seniority_timeline.effective_work_months == 24
    assert result.seniority_timeline.prior_history_requires_review is True
    assert result.decision is ContractPreflightDecision.REVIEW


def test_explicit_recognized_prior_months_are_added_to_current_contract():
    result = bridge.build_ccns_creation_rules_preflight(
        group_code="G1",
        reference_date=date(2025, 1, 1),
        current_contract_start=date(2025, 1, 1),
        evaluation_date=date(2026, 1, 1),
        weekly_hours=Decimal("17.50"),
        compensation=ContractCompensationPreflight(True, "ok"),
        recognized_effective_work_months_at_start=24,
        recognized_company_seniority_months_at_start=24,
    )
    assert result.seniority_timeline.effective_work_months == 36
    assert result.seniority_timeline.company_seniority_months == 36
    assert result.seniority.total_rate_percent == Decimal("6.00")
    assert result.seniority.monthly_due_amount == Decimal("59.94")
