from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional
from uuid import UUID

from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot, ContractSalaryControlSnapshotRow
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason, _strict_date, _strict_uuid

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")


class ContractSalaryControlIssueStatus(str, Enum):
    NEW = "new"
    ONGOING = "ongoing"
    RESOLVED = "resolved"
    UNKNOWN = "unknown"


class ContractSalaryControlIssueEvolutionType(str, Enum):
    NEW = "new"
    ONGOING = "ongoing"
    RESOLVED = "resolved"
    REPLACED = "replaced"
    SEVERITY_CHANGED = "severity_changed"
    REASON_CHANGED = "reason_changed"
    STATUS_CHANGED = "status_changed"
    UNKNOWN = "unknown"


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


def _strict_optional_decimal(value: object, field_name: str) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être None ou un Decimal strict.")
    if value != value.quantize(_CENT, rounding=ROUND_HALF_UP):
        raise ValueError(f"{field_name} doit être quantifié à deux décimales.")


def _strict_optional_failure_reason(value: object, field_name: str) -> None:
    if value is not None and type(value) is not ContractSalaryEvaluationFailureReason:
        raise TypeError(f"{field_name} doit être None ou un ContractSalaryEvaluationFailureReason.")


def _strict_optional_status(value: object, field_name: str) -> None:
    if value is not None and type(value) is not ContractSalaryControlStatus:
        raise TypeError(f"{field_name} doit être None ou un ContractSalaryControlStatus.")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlIssue:
    contract_id: UUID
    employee_id: Optional[UUID]
    issue_code: str
    failure_reason: Optional[ContractSalaryEvaluationFailureReason]
    status: Optional[ContractSalaryControlStatus]
    shortfall_amount: Optional[Decimal]
    issue_message: Optional[str] = None
    failure_message: Optional[str] = None
    classification_code: Optional[str] = None

    def __post_init__(self) -> None:
        _strict_uuid(self.contract_id, "contract_id")
        _strict_optional_uuid(self.employee_id, "employee_id")
        object.__setattr__(self, "issue_code", _strict_optional_str(self.issue_code, "issue_code"))
        if self.issue_code is None:
            raise ValueError("issue_code doit identifier l'anomalie sans libellé d'interface.")
        _strict_optional_failure_reason(self.failure_reason, "failure_reason")
        _strict_optional_status(self.status, "status")
        _strict_optional_decimal(self.shortfall_amount, "shortfall_amount")
        object.__setattr__(self, "issue_message", _strict_optional_str(self.issue_message, "issue_message"))
        object.__setattr__(self, "failure_message", _strict_optional_str(self.failure_message, "failure_message"))
        object.__setattr__(self, "classification_code", _strict_optional_str(self.classification_code, "classification_code"))

    @property
    def stable_key(self) -> tuple[UUID, str, Optional[ContractSalaryEvaluationFailureReason]]:
        return (self.contract_id, self.issue_code, self.failure_reason)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlIssueHistoryRow:
    contract_id: UUID
    employee_id: Optional[UUID]
    issue_code_before: Optional[str]
    issue_code_after: Optional[str]
    status: ContractSalaryControlIssueStatus
    evolution_type: ContractSalaryControlIssueEvolutionType
    salary_status_before: Optional[ContractSalaryControlStatus]
    salary_status_after: Optional[ContractSalaryControlStatus]
    failure_reason_before: Optional[ContractSalaryEvaluationFailureReason]
    failure_reason_after: Optional[ContractSalaryEvaluationFailureReason]
    issue_message_before: Optional[str]
    issue_message_after: Optional[str]
    shortfall_amount_before: Optional[Decimal]
    shortfall_amount_after: Optional[Decimal]
    replacement_issue_key: Optional[tuple[UUID, str, Optional[ContractSalaryEvaluationFailureReason]]] = None

    def __post_init__(self) -> None:
        _strict_uuid(self.contract_id, "contract_id")
        _strict_optional_uuid(self.employee_id, "employee_id")
        for name in ("issue_code_before", "issue_code_after", "issue_message_before", "issue_message_after"):
            object.__setattr__(self, name, _strict_optional_str(getattr(self, name), name))
        if type(self.status) is not ContractSalaryControlIssueStatus:
            raise TypeError("status doit être un ContractSalaryControlIssueStatus.")
        if type(self.evolution_type) is not ContractSalaryControlIssueEvolutionType:
            raise TypeError("evolution_type doit être un ContractSalaryControlIssueEvolutionType.")
        _strict_optional_status(self.salary_status_before, "salary_status_before")
        _strict_optional_status(self.salary_status_after, "salary_status_after")
        _strict_optional_failure_reason(self.failure_reason_before, "failure_reason_before")
        _strict_optional_failure_reason(self.failure_reason_after, "failure_reason_after")
        _strict_optional_decimal(self.shortfall_amount_before, "shortfall_amount_before")
        _strict_optional_decimal(self.shortfall_amount_after, "shortfall_amount_after")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlIssueHistory:
    before_snapshot_id: UUID
    after_snapshot_id: UUID
    before_reference_date: date
    after_reference_date: date
    before_executed_at: datetime
    after_executed_at: datetime
    rows: tuple[ContractSalaryControlIssueHistoryRow, ...]
    total_issues: int
    new_issues: int
    resolved_issues: int
    ongoing_issues: int
    unknown_issues: int

    def __post_init__(self) -> None:
        _strict_uuid(self.before_snapshot_id, "before_snapshot_id")
        _strict_uuid(self.after_snapshot_id, "after_snapshot_id")
        _strict_date(self.before_reference_date)
        _strict_date(self.after_reference_date)
        if type(self.before_executed_at) is not datetime or type(self.after_executed_at) is not datetime:
            raise TypeError("Les dates d'exécution doivent être des datetime stricts.")
        if type(self.rows) is not tuple or any(type(row) is not ContractSalaryControlIssueHistoryRow for row in self.rows):
            raise TypeError("rows doit être un tuple de ContractSalaryControlIssueHistoryRow.")


class TrackContractSalaryControlIssuesService:
    def track(self, before: ContractSalaryControlSnapshot, after: ContractSalaryControlSnapshot) -> ContractSalaryControlIssueHistory:
        if type(before) is not ContractSalaryControlSnapshot or type(after) is not ContractSalaryControlSnapshot:
            raise TypeError("Le suivi attend deux ContractSalaryControlSnapshot stricts.")
        if before.snapshot_id == after.snapshot_id:
            raise ValueError("Deux snapshots différents sont nécessaires pour suivre les anomalies salariales.")
        before_issues = {issue.stable_key: issue for issue in self._issues(before)}
        after_issues = {issue.stable_key: issue for issue in self._issues(after)}
        before_by_contract = self._by_contract(before_issues)
        after_by_contract = self._by_contract(after_issues)
        rows = []
        for key in sorted(set(before_issues) | set(after_issues), key=self._sort_key):
            old = before_issues.get(key)
            new = after_issues.get(key)
            if old is not None and new is not None:
                rows.append(self._row(old, new))
            elif new is not None:
                replaced = self._replacement_key(before_by_contract.get(new.contract_id, ()), after_issues)
                rows.append(self._row(None, new, replacement_issue_key=replaced))
            elif old is not None:
                replacement = self._replacement_key(after_by_contract.get(old.contract_id, ()), before_issues)
                rows.append(self._row(old, None, replacement_issue_key=replacement))
        history_rows = tuple(rows)
        return ContractSalaryControlIssueHistory(
            before.snapshot_id, after.snapshot_id, before.reference_date, after.reference_date, before.executed_at, after.executed_at,
            history_rows, len(history_rows),
            sum(1 for row in history_rows if row.status is ContractSalaryControlIssueStatus.NEW),
            sum(1 for row in history_rows if row.status is ContractSalaryControlIssueStatus.RESOLVED),
            sum(1 for row in history_rows if row.status is ContractSalaryControlIssueStatus.ONGOING),
            sum(1 for row in history_rows if row.status is ContractSalaryControlIssueStatus.UNKNOWN),
        )

    def _issues(self, snapshot: ContractSalaryControlSnapshot) -> tuple[ContractSalaryControlIssue, ...]:
        return tuple(issue for row in snapshot.rows if (issue := self._issue(row)) is not None)

    def _issue(self, row: ContractSalaryControlSnapshotRow) -> Optional[ContractSalaryControlIssue]:
        if row.status is ContractSalaryControlStatus.COMPLIANT and row.issue_code is None and row.failure_reason is None:
            return None
        if row.issue_code is not None:
            code = row.issue_code
        elif row.failure_reason is not None:
            code = "not_evaluated"
        elif row.status is ContractSalaryControlStatus.NON_COMPLIANT:
            code = "non_compliant"
        elif row.status is ContractSalaryControlStatus.NOT_EVALUATED:
            code = "not_evaluated"
        else:
            return None
        return ContractSalaryControlIssue(row.contract_id, row.employee_id, code, row.failure_reason, row.status, row.shortfall_amount, row.issue_message, row.failure_message, row.classification_code)

    def _row(self, old: Optional[ContractSalaryControlIssue], new: Optional[ContractSalaryControlIssue], *, replacement_issue_key=None) -> ContractSalaryControlIssueHistoryRow:
        source = new or old
        assert source is not None
        if old is None:
            status = ContractSalaryControlIssueStatus.NEW
            evolution = ContractSalaryControlIssueEvolutionType.REPLACED if replacement_issue_key else ContractSalaryControlIssueEvolutionType.NEW
        elif new is None:
            status = ContractSalaryControlIssueStatus.RESOLVED
            evolution = ContractSalaryControlIssueEvolutionType.REPLACED if replacement_issue_key else ContractSalaryControlIssueEvolutionType.RESOLVED
        else:
            status = ContractSalaryControlIssueStatus.ONGOING
            evolution = self._ongoing_evolution(old, new)
        return ContractSalaryControlIssueHistoryRow(
            source.contract_id, source.employee_id, old.issue_code if old else None, new.issue_code if new else None,
            status, evolution, old.status if old else None, new.status if new else None,
            old.failure_reason if old else None, new.failure_reason if new else None,
            old.issue_message if old else None, new.issue_message if new else None,
            old.shortfall_amount if old else None, new.shortfall_amount if new else None,
            replacement_issue_key,
        )

    def _ongoing_evolution(self, old, new):
        if old.status != new.status:
            return ContractSalaryControlIssueEvolutionType.STATUS_CHANGED
        if old.failure_reason != new.failure_reason or old.issue_message != new.issue_message or old.failure_message != new.failure_message:
            return ContractSalaryControlIssueEvolutionType.REASON_CHANGED
        if old.shortfall_amount != new.shortfall_amount:
            return ContractSalaryControlIssueEvolutionType.SEVERITY_CHANGED
        return ContractSalaryControlIssueEvolutionType.ONGOING

    def _by_contract(self, issues):
        result = {}
        for key in issues:
            result.setdefault(key[0], tuple())
            result[key[0]] = result[key[0]] + (key,)
        return result

    def _replacement_key(self, candidate_keys, excluded):
        for key in sorted(candidate_keys, key=self._sort_key):
            if key not in excluded:
                return key
        return None

    def _sort_key(self, key):
        contract_id, issue_code, failure_reason = key
        return (str(contract_id), issue_code, failure_reason.value if failure_reason else "")
