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
from domain.convention import ApplicableSalaryMinimumSource

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")


class ContractSalaryControlSnapshotChangeType(str, Enum):
    NEW_CONTRACT = "new_contract"
    REMOVED_CONTRACT = "removed_contract"
    BECAME_COMPLIANT = "became_compliant"
    BECAME_NON_COMPLIANT = "became_non_compliant"
    BECAME_NOT_EVALUATED = "became_not_evaluated"
    REMAINS_COMPLIANT = "remains_compliant"
    REMAINS_NON_COMPLIANT = "remains_non_compliant"
    REMAINS_NOT_EVALUATED = "remains_not_evaluated"
    STATUS_CHANGED_OTHER = "status_changed_other"
    UNCHANGED = "unchanged"


def _strict_optional_uuid(value: object, field_name: str) -> None:
    if value is not None:
        _strict_uuid(value, field_name)


def _strict_decimal(value: object, field_name: str) -> None:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être un Decimal strict.")
    if value != value.quantize(_CENT, rounding=ROUND_HALF_UP):
        raise ValueError(f"{field_name} doit être quantifié à deux décimales.")


def _strict_optional_decimal(value: object, field_name: str) -> None:
    if value is not None:
        _strict_decimal(value, field_name)


def _strict_optional_str(value: object, field_name: str) -> None:
    if value is not None and type(value) is not str:
        raise TypeError(f"{field_name} doit être None ou une chaîne.")


def _strict_optional_status(value: object, field_name: str) -> None:
    if value is not None and type(value) is not ContractSalaryControlStatus:
        raise TypeError(f"{field_name} doit être None ou un ContractSalaryControlStatus.")


def _strict_optional_source(value: object, field_name: str) -> None:
    if value is not None and type(value) is not ApplicableSalaryMinimumSource:
        raise TypeError(f"{field_name} doit être None ou un ApplicableSalaryMinimumSource.")


def _strict_optional_failure_reason(value: object, field_name: str) -> None:
    if value is not None and type(value) is not ContractSalaryEvaluationFailureReason:
        raise TypeError(f"{field_name} doit être None ou un ContractSalaryEvaluationFailureReason.")


def _amount(value: Optional[Decimal]) -> Decimal:
    return value if value is not None else _ZERO


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshotComparisonRow:
    contract_id: UUID
    employee_id_before: Optional[UUID]
    employee_id_after: Optional[UUID]
    status_before: Optional[ContractSalaryControlStatus]
    status_after: Optional[ContractSalaryControlStatus]
    change_type: ContractSalaryControlSnapshotChangeType
    remuneration_amount_before: Optional[Decimal]
    remuneration_amount_after: Optional[Decimal]
    remuneration_delta: Decimal
    applicable_minimum_amount_before: Optional[Decimal]
    applicable_minimum_amount_after: Optional[Decimal]
    minimum_delta: Decimal
    shortfall_amount_before: Optional[Decimal]
    shortfall_amount_after: Optional[Decimal]
    shortfall_delta: Decimal
    classification_code_before: Optional[str]
    classification_code_after: Optional[str]
    minimum_source_before: Optional[ApplicableSalaryMinimumSource]
    minimum_source_after: Optional[ApplicableSalaryMinimumSource]
    issue_code_before: Optional[str]
    issue_code_after: Optional[str]
    failure_reason_before: Optional[ContractSalaryEvaluationFailureReason]
    failure_reason_after: Optional[ContractSalaryEvaluationFailureReason]

    def __post_init__(self) -> None:
        _strict_uuid(self.contract_id, "contract_id")
        _strict_optional_uuid(self.employee_id_before, "employee_id_before")
        _strict_optional_uuid(self.employee_id_after, "employee_id_after")
        _strict_optional_status(self.status_before, "status_before")
        _strict_optional_status(self.status_after, "status_after")
        if type(self.change_type) is not ContractSalaryControlSnapshotChangeType:
            raise TypeError("change_type doit être un ContractSalaryControlSnapshotChangeType.")
        for name in ("remuneration_amount_before", "remuneration_amount_after", "applicable_minimum_amount_before", "applicable_minimum_amount_after", "shortfall_amount_before", "shortfall_amount_after"):
            _strict_optional_decimal(getattr(self, name), name)
        for name in ("remuneration_delta", "minimum_delta", "shortfall_delta"):
            _strict_decimal(getattr(self, name), name)
        for name in ("classification_code_before", "classification_code_after", "issue_code_before", "issue_code_after"):
            _strict_optional_str(getattr(self, name), name)
        _strict_optional_source(self.minimum_source_before, "minimum_source_before")
        _strict_optional_source(self.minimum_source_after, "minimum_source_after")
        _strict_optional_failure_reason(self.failure_reason_before, "failure_reason_before")
        _strict_optional_failure_reason(self.failure_reason_after, "failure_reason_after")

    @property
    def changed(self) -> bool:
        return self.change_type is not ContractSalaryControlSnapshotChangeType.UNCHANGED


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshotComparison:
    before_snapshot_id: UUID
    after_snapshot_id: UUID
    before_reference_date: date
    after_reference_date: date
    before_executed_at: datetime
    after_executed_at: datetime
    rows: tuple[ContractSalaryControlSnapshotComparisonRow, ...]
    total_before: int
    total_after: int
    common_contracts: int
    new_contracts: int
    removed_contracts: int
    became_compliant: int
    became_non_compliant: int
    became_not_evaluated: int
    unchanged_contracts: int
    total_shortfall_before: Decimal
    total_shortfall_after: Decimal
    total_shortfall_delta: Decimal
    improved: bool
    degraded: bool
    unchanged: bool

    def __post_init__(self) -> None:
        _strict_uuid(self.before_snapshot_id, "before_snapshot_id")
        _strict_uuid(self.after_snapshot_id, "after_snapshot_id")
        _strict_date(self.before_reference_date)
        _strict_date(self.after_reference_date)
        if type(self.before_executed_at) is not datetime or type(self.after_executed_at) is not datetime:
            raise TypeError("Les dates d'exécution doivent être des datetime stricts.")
        if type(self.rows) is not tuple or any(type(r) is not ContractSalaryControlSnapshotComparisonRow for r in self.rows):
            raise TypeError("rows doit être un tuple de lignes de comparaison.")
        for name in ("total_shortfall_before", "total_shortfall_after", "total_shortfall_delta"):
            _strict_decimal(getattr(self, name), name)


class CompareContractSalaryControlSnapshotsService:
    def compare(self, before: ContractSalaryControlSnapshot, after: ContractSalaryControlSnapshot) -> ContractSalaryControlSnapshotComparison:
        if type(before) is not ContractSalaryControlSnapshot:
            raise TypeError("before doit être un ContractSalaryControlSnapshot strict.")
        if type(after) is not ContractSalaryControlSnapshot:
            raise TypeError("after doit être un ContractSalaryControlSnapshot strict.")
        if before.snapshot_id == after.snapshot_id:
            raise ValueError("Deux snapshots différents sont nécessaires pour comparer un contrôle salarial.")
        after_by_contract = {row.contract_id: row for row in after.rows}
        before_ids = {row.contract_id for row in before.rows}
        rows = [self._compare_rows(row, after_by_contract.get(row.contract_id)) for row in before.rows]
        rows.extend(self._compare_rows(None, row) for row in after.rows if row.contract_id not in before_ids)
        comparison_rows = tuple(rows)
        improving_status = sum(1 for r in comparison_rows if r.change_type is ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT)
        degrading_status = sum(1 for r in comparison_rows if r.change_type in (ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT, ContractSalaryControlSnapshotChangeType.BECAME_NOT_EVALUATED))
        amount_improved = after.total_shortfall_amount < before.total_shortfall_amount
        amount_degraded = after.total_shortfall_amount > before.total_shortfall_amount
        any_content_changed = any(r.changed for r in comparison_rows)
        unchanged = not any_content_changed and after.total_shortfall_amount == before.total_shortfall_amount
        return ContractSalaryControlSnapshotComparison(
            before.snapshot_id, after.snapshot_id, before.reference_date, after.reference_date, before.executed_at, after.executed_at,
            comparison_rows, before.total_contracts, after.total_contracts,
            sum(1 for r in comparison_rows if r.status_before is not None and r.status_after is not None),
            sum(1 for r in comparison_rows if r.change_type is ContractSalaryControlSnapshotChangeType.NEW_CONTRACT),
            sum(1 for r in comparison_rows if r.change_type is ContractSalaryControlSnapshotChangeType.REMOVED_CONTRACT),
            improving_status,
            sum(1 for r in comparison_rows if r.change_type is ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT),
            sum(1 for r in comparison_rows if r.change_type is ContractSalaryControlSnapshotChangeType.BECAME_NOT_EVALUATED),
            sum(1 for r in comparison_rows if r.change_type is ContractSalaryControlSnapshotChangeType.UNCHANGED),
            before.total_shortfall_amount, after.total_shortfall_amount, (after.total_shortfall_amount - before.total_shortfall_amount).quantize(_CENT),
            (amount_improved or improving_status > 0) and not unchanged,
            (amount_degraded or degrading_status > 0) and not unchanged,
            unchanged,
        )

    def _compare_rows(self, before: Optional[ContractSalaryControlSnapshotRow], after: Optional[ContractSalaryControlSnapshotRow]) -> ContractSalaryControlSnapshotComparisonRow:
        source = before or after
        assert source is not None
        change_type = self._change_type(before, after)
        return ContractSalaryControlSnapshotComparisonRow(
            source.contract_id,
            before.employee_id if before else None,
            after.employee_id if after else None,
            before.status if before else None,
            after.status if after else None,
            change_type,
            before.remuneration_amount if before else None,
            after.remuneration_amount if after else None,
            (_amount(after.remuneration_amount if after else None) - _amount(before.remuneration_amount if before else None)).quantize(_CENT),
            before.applicable_minimum_amount if before else None,
            after.applicable_minimum_amount if after else None,
            (_amount(after.applicable_minimum_amount if after else None) - _amount(before.applicable_minimum_amount if before else None)).quantize(_CENT),
            before.shortfall_amount if before else None,
            after.shortfall_amount if after else None,
            (_amount(after.shortfall_amount if after else None) - _amount(before.shortfall_amount if before else None)).quantize(_CENT),
            before.classification_code if before else None,
            after.classification_code if after else None,
            before.minimum_source if before else None,
            after.minimum_source if after else None,
            before.issue_code if before else None,
            after.issue_code if after else None,
            before.failure_reason if before else None,
            after.failure_reason if after else None,
        )

    def _change_type(self, before, after):
        if before is None:
            return ContractSalaryControlSnapshotChangeType.NEW_CONTRACT
        if after is None:
            return ContractSalaryControlSnapshotChangeType.REMOVED_CONTRACT
        if before == after:
            return ContractSalaryControlSnapshotChangeType.UNCHANGED
        if after.status is ContractSalaryControlStatus.COMPLIANT and before.status is not ContractSalaryControlStatus.COMPLIANT:
            return ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT
        if after.status is ContractSalaryControlStatus.NON_COMPLIANT and before.status is not ContractSalaryControlStatus.NON_COMPLIANT:
            return ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT
        if after.status is ContractSalaryControlStatus.NOT_EVALUATED and before.status is not ContractSalaryControlStatus.NOT_EVALUATED:
            return ContractSalaryControlSnapshotChangeType.BECAME_NOT_EVALUATED
        if before.status is after.status is ContractSalaryControlStatus.COMPLIANT:
            return ContractSalaryControlSnapshotChangeType.REMAINS_COMPLIANT
        if before.status is after.status is ContractSalaryControlStatus.NON_COMPLIANT:
            return ContractSalaryControlSnapshotChangeType.REMAINS_NON_COMPLIANT
        if before.status is after.status is ContractSalaryControlStatus.NOT_EVALUATED:
            return ContractSalaryControlSnapshotChangeType.REMAINS_NOT_EVALUATED
        return ContractSalaryControlSnapshotChangeType.STATUS_CHANGED_OTHER
