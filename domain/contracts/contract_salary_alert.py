from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional
from uuid import UUID

from domain.contracts.contract_salary_control_issue_history import ContractSalaryControlIssueHistory, ContractSalaryControlIssueStatus
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot
from domain.contracts.contract_salary_control_snapshot_comparison import ContractSalaryControlSnapshotChangeType, ContractSalaryControlSnapshotComparison
from domain.contracts.contract_salary_evaluation import _strict_date, _strict_uuid

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")
SIGNIFICANT_SHORTFALL_INCREASE_THRESHOLD = Decimal("0.01")
MINIMUM_INCREASE_THRESHOLD = Decimal("0.01")
SALARY_DECREASE_THRESHOLD = Decimal("0.01")


class ContractSalaryAlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ContractSalaryAlertType(str, Enum):
    NEW_ANOMALY = "new_anomaly"
    PERSISTENT_ANOMALY = "persistent_anomaly"
    SALARY_DECREASE = "salary_decrease"
    MINIMUM_INCREASE = "minimum_increase"
    NON_COMPLIANT_CONTRACT = "non_compliant_contract"
    NOT_EVALUATED_CONTRACT = "not_evaluated_contract"
    NEW_CONTRACT = "new_contract"
    REMOVED_CONTRACT = "removed_contract"
    SIGNIFICANT_SHORTFALL = "significant_shortfall"
    OTHER = "other"


def _strict_optional_uuid(value: object, field_name: str) -> None:
    if value is not None:
        _strict_uuid(value, field_name)


def _strict_optional_str(value: object, field_name: str) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise TypeError(f"{field_name} doit être None ou une chaîne.")
    cleaned = value.strip()
    return cleaned or None


@dataclass(frozen=True, slots=True)
class ContractSalaryAlert:
    contract_id: UUID
    employee_id: Optional[UUID]
    severity: ContractSalaryAlertSeverity
    alert_type: ContractSalaryAlertType
    summary_key: str
    detail_key: str
    alert_date: date
    amount: Optional[Decimal] = None
    issue_code: Optional[str] = None

    def __post_init__(self) -> None:
        _strict_uuid(self.contract_id, "contract_id")
        _strict_optional_uuid(self.employee_id, "employee_id")
        if type(self.severity) is not ContractSalaryAlertSeverity:
            raise TypeError("severity doit être un ContractSalaryAlertSeverity.")
        if type(self.alert_type) is not ContractSalaryAlertType:
            raise TypeError("alert_type doit être un ContractSalaryAlertType.")
        object.__setattr__(self, "summary_key", _strict_optional_str(self.summary_key, "summary_key"))
        object.__setattr__(self, "detail_key", _strict_optional_str(self.detail_key, "detail_key"))
        if self.summary_key is None or self.detail_key is None:
            raise ValueError("summary_key et detail_key sont obligatoires.")
        _strict_date(self.alert_date)
        if self.amount is not None:
            if type(self.amount) is not Decimal:
                raise TypeError("amount doit être None ou un Decimal strict.")
            if self.amount != self.amount.quantize(_CENT, rounding=ROUND_HALF_UP):
                raise ValueError("amount doit être quantifié à deux décimales.")
        object.__setattr__(self, "issue_code", _strict_optional_str(self.issue_code, "issue_code"))


@dataclass(frozen=True, slots=True)
class ContractSalaryAlertCollection:
    alerts: tuple[ContractSalaryAlert, ...]

    def __post_init__(self) -> None:
        if type(self.alerts) is not tuple or any(type(alert) is not ContractSalaryAlert for alert in self.alerts):
            raise TypeError("alerts doit être un tuple de ContractSalaryAlert.")

    @property
    def total_count(self) -> int:
        return len(self.alerts)

    @property
    def critical_count(self) -> int:
        return sum(1 for alert in self.alerts if alert.severity is ContractSalaryAlertSeverity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for alert in self.alerts if alert.severity is ContractSalaryAlertSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for alert in self.alerts if alert.severity is ContractSalaryAlertSeverity.INFO)


class GenerateContractSalaryAlertsService:
    def generate(self, current_snapshot: ContractSalaryControlSnapshot, comparison: ContractSalaryControlSnapshotComparison, issue_history: ContractSalaryControlIssueHistory) -> ContractSalaryAlertCollection:
        if type(current_snapshot) is not ContractSalaryControlSnapshot:
            raise TypeError("current_snapshot doit être un ContractSalaryControlSnapshot strict.")
        if type(comparison) is not ContractSalaryControlSnapshotComparison:
            raise TypeError("comparison doit être une ContractSalaryControlSnapshotComparison stricte.")
        if type(issue_history) is not ContractSalaryControlIssueHistory:
            raise TypeError("issue_history doit être un ContractSalaryControlIssueHistory strict.")
        rows_by_contract = {row.contract_id: row for row in current_snapshot.rows}
        alerts = []
        for row in comparison.rows:
            employee_id = row.employee_id_after or row.employee_id_before
            if row.change_type is ContractSalaryControlSnapshotChangeType.NEW_CONTRACT:
                if row.status_after is ContractSalaryControlStatus.NON_COMPLIANT:
                    alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.CRITICAL, ContractSalaryAlertType.NON_COMPLIANT_CONTRACT, "new_non_compliant_contract", "new_contract_requires_action", current_snapshot.reference_date, row.shortfall_amount_after))
                elif row.status_after is ContractSalaryControlStatus.COMPLIANT:
                    alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.INFO, ContractSalaryAlertType.NEW_CONTRACT, "new_compliant_contract", "new_contract_no_action", current_snapshot.reference_date))
            if row.change_type is ContractSalaryControlSnapshotChangeType.REMOVED_CONTRACT:
                alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.INFO, ContractSalaryAlertType.REMOVED_CONTRACT, "removed_contract", "contract_absent_from_current_snapshot", current_snapshot.reference_date))
            if row.change_type is ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT:
                alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.INFO, ContractSalaryAlertType.OTHER, "contract_became_compliant", "non_compliance_resolved", current_snapshot.reference_date))
            if row.change_type is ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT:
                alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.CRITICAL, ContractSalaryAlertType.NON_COMPLIANT_CONTRACT, "contract_became_non_compliant", "contract_requires_action", current_snapshot.reference_date, row.shortfall_amount_after))
            if row.status_after is ContractSalaryControlStatus.NOT_EVALUATED and row.status_before is not ContractSalaryControlStatus.NOT_EVALUATED:
                alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.WARNING, ContractSalaryAlertType.NOT_EVALUATED_CONTRACT, "contract_not_evaluated", "missing_data_or_rule_prevents_evaluation", current_snapshot.reference_date))
            has_before_and_after = row.change_type not in (
                ContractSalaryControlSnapshotChangeType.NEW_CONTRACT,
                ContractSalaryControlSnapshotChangeType.REMOVED_CONTRACT,
            )
            if has_before_and_after and row.minimum_delta >= MINIMUM_INCREASE_THRESHOLD:
                alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.WARNING, ContractSalaryAlertType.MINIMUM_INCREASE, "minimum_increased", "applicable_minimum_above_previous_snapshot", current_snapshot.reference_date, row.minimum_delta))
            if has_before_and_after and row.remuneration_delta <= -SALARY_DECREASE_THRESHOLD:
                alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.WARNING, ContractSalaryAlertType.SALARY_DECREASE, "salary_decreased", "remuneration_below_previous_snapshot", current_snapshot.reference_date, row.remuneration_delta))
            if has_before_and_after and row.shortfall_delta >= SIGNIFICANT_SHORTFALL_INCREASE_THRESHOLD and row.shortfall_amount_after and row.shortfall_amount_after > _ZERO:
                alerts.append(self._alert(row.contract_id, employee_id, ContractSalaryAlertSeverity.CRITICAL, ContractSalaryAlertType.SIGNIFICANT_SHORTFALL, "shortfall_increased", "shortfall_above_previous_snapshot", current_snapshot.reference_date, row.shortfall_delta))
        for issue in issue_history.rows:
            employee_id = issue.employee_id or (rows_by_contract.get(issue.contract_id).employee_id if issue.contract_id in rows_by_contract else None)
            issue_code = issue.issue_code_after or issue.issue_code_before
            if issue.status is ContractSalaryControlIssueStatus.NEW:
                alerts.append(self._alert(issue.contract_id, employee_id, ContractSalaryAlertSeverity.WARNING, ContractSalaryAlertType.NEW_ANOMALY, "new_anomaly", "anomaly_absent_from_previous_snapshot", current_snapshot.reference_date, issue.shortfall_amount_after, issue_code))
            elif issue.status is ContractSalaryControlIssueStatus.ONGOING:
                severity = ContractSalaryAlertSeverity.CRITICAL if (issue.shortfall_amount_after or _ZERO) > (issue.shortfall_amount_before or _ZERO) else ContractSalaryAlertSeverity.WARNING
                alerts.append(self._alert(issue.contract_id, employee_id, severity, ContractSalaryAlertType.PERSISTENT_ANOMALY, "persistent_anomaly", "anomaly_still_present", current_snapshot.reference_date, issue.shortfall_amount_after, issue_code))
            elif issue.status is ContractSalaryControlIssueStatus.RESOLVED:
                alerts.append(self._alert(issue.contract_id, employee_id, ContractSalaryAlertSeverity.INFO, ContractSalaryAlertType.OTHER, "resolved_anomaly", "anomaly_absent_from_current_snapshot", current_snapshot.reference_date, issue.shortfall_amount_before, issue_code))
        ordered = tuple(sorted(alerts, key=lambda a: ({ContractSalaryAlertSeverity.CRITICAL: 0, ContractSalaryAlertSeverity.WARNING: 1, ContractSalaryAlertSeverity.INFO: 2}[a.severity], str(a.contract_id), a.alert_type.value, a.summary_key)))
        return ContractSalaryAlertCollection(ordered)

    def _alert(self, contract_id, employee_id, severity, alert_type, summary_key, detail_key, alert_date, amount=None, issue_code=None):
        return ContractSalaryAlert(contract_id, employee_id, severity, alert_type, summary_key, detail_key, alert_date, amount, issue_code)
