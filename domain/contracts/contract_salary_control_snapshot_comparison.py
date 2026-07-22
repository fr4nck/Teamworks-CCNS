from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import UUID

from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot, ContractSalaryControlSnapshotRow


class ContractSalaryControlSnapshotChangeType(Enum):
    BECAME_COMPLIANT = "became_compliant"
    BECAME_NON_COMPLIANT = "became_non_compliant"
    STATUS_CHANGED = "status_changed"
    NEW_CONTRACT = "new_contract"
    MISSING_CONTRACT = "missing_contract"
    SHORTFALL_INCREASED = "shortfall_increased"
    SHORTFALL_DECREASED = "shortfall_decreased"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshotRowComparison:
    contract_id: UUID
    previous_row: ContractSalaryControlSnapshotRow | None
    current_row: ContractSalaryControlSnapshotRow | None
    change_type: ContractSalaryControlSnapshotChangeType
    previous_status: ContractSalaryControlStatus | None
    current_status: ContractSalaryControlStatus | None
    previous_shortfall_amount: Decimal
    current_shortfall_amount: Decimal
    shortfall_delta: Decimal


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshotComparison:
    previous_snapshot: ContractSalaryControlSnapshot
    current_snapshot: ContractSalaryControlSnapshot
    rows: tuple[ContractSalaryControlSnapshotRowComparison, ...]
    total_contracts: int
    became_compliant_contracts: int
    became_non_compliant_contracts: int
    new_contracts: int
    missing_contracts: int
    increased_shortfall_contracts: int
    decreased_shortfall_contracts: int
    total_shortfall_delta: Decimal


def compare_contract_salary_control_snapshots(
    previous_snapshot: ContractSalaryControlSnapshot,
    current_snapshot: ContractSalaryControlSnapshot,
) -> ContractSalaryControlSnapshotComparison:
    """Compare deux snapshots sans réévaluer les règles salariales métier."""
    if type(previous_snapshot) is not ContractSalaryControlSnapshot:
        raise TypeError("previous_snapshot doit être un ContractSalaryControlSnapshot strict.")
    if type(current_snapshot) is not ContractSalaryControlSnapshot:
        raise TypeError("current_snapshot doit être un ContractSalaryControlSnapshot strict.")

    previous_rows = {row.contract_id: row for row in previous_snapshot.rows}
    current_rows = {row.contract_id: row for row in current_snapshot.rows}
    comparisons = tuple(
        _compare_row(contract_id, previous_rows.get(contract_id), current_rows.get(contract_id))
        for contract_id in sorted(previous_rows.keys() | current_rows.keys(), key=str)
    )
    return ContractSalaryControlSnapshotComparison(
        previous_snapshot=previous_snapshot,
        current_snapshot=current_snapshot,
        rows=comparisons,
        total_contracts=len(comparisons),
        became_compliant_contracts=_count(comparisons, ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT),
        became_non_compliant_contracts=_count(comparisons, ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT),
        new_contracts=_count(comparisons, ContractSalaryControlSnapshotChangeType.NEW_CONTRACT),
        missing_contracts=_count(comparisons, ContractSalaryControlSnapshotChangeType.MISSING_CONTRACT),
        increased_shortfall_contracts=sum(1 for row in comparisons if row.shortfall_delta > 0),
        decreased_shortfall_contracts=sum(1 for row in comparisons if row.shortfall_delta < 0),
        total_shortfall_delta=current_snapshot.total_shortfall_amount - previous_snapshot.total_shortfall_amount,
    )


def _compare_row(
    contract_id: UUID,
    previous_row: ContractSalaryControlSnapshotRow | None,
    current_row: ContractSalaryControlSnapshotRow | None,
) -> ContractSalaryControlSnapshotRowComparison:
    previous_shortfall = previous_row.shortfall_amount if previous_row is not None else Decimal("0.00")
    current_shortfall = current_row.shortfall_amount if current_row is not None else Decimal("0.00")
    previous_status = previous_row.status if previous_row is not None else None
    current_status = current_row.status if current_row is not None else None
    return ContractSalaryControlSnapshotRowComparison(
        contract_id=contract_id,
        previous_row=previous_row,
        current_row=current_row,
        change_type=_change_type(previous_row, current_row),
        previous_status=previous_status,
        current_status=current_status,
        previous_shortfall_amount=previous_shortfall,
        current_shortfall_amount=current_shortfall,
        shortfall_delta=current_shortfall - previous_shortfall,
    )


def _change_type(previous_row, current_row):
    if previous_row is None:
        return ContractSalaryControlSnapshotChangeType.NEW_CONTRACT
    if current_row is None:
        return ContractSalaryControlSnapshotChangeType.MISSING_CONTRACT
    if previous_row.status is not current_row.status:
        if current_row.status is ContractSalaryControlStatus.COMPLIANT:
            return ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT
        if current_row.status is ContractSalaryControlStatus.NON_COMPLIANT:
            return ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT
        return ContractSalaryControlSnapshotChangeType.STATUS_CHANGED
    if current_row.shortfall_amount > previous_row.shortfall_amount:
        return ContractSalaryControlSnapshotChangeType.SHORTFALL_INCREASED
    if current_row.shortfall_amount < previous_row.shortfall_amount:
        return ContractSalaryControlSnapshotChangeType.SHORTFALL_DECREASED
    return ContractSalaryControlSnapshotChangeType.UNCHANGED


def _count(rows, change_type):
    return sum(1 for row in rows if row.change_type is change_type)
