from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID

from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot


class DuplicateContractSalaryControlSnapshotError(ValueError):
    pass


@dataclass(slots=True)
class InMemoryContractSalaryControlSnapshotRepository:
    snapshots: list[ContractSalaryControlSnapshot] = field(default_factory=list)

    def save(self, snapshot: ContractSalaryControlSnapshot) -> ContractSalaryControlSnapshot:
        if any(existing.duplicate_key() == snapshot.duplicate_key() for existing in self.snapshots):
            raise DuplicateContractSalaryControlSnapshotError("Un snapshot salarial strictement identique existe déjà.")
        self.snapshots.append(snapshot)
        return snapshot

    def get(self, snapshot_id: UUID) -> Optional[ContractSalaryControlSnapshot]:
        return next((s for s in self.snapshots if s.snapshot_id == snapshot_id), None)

    def list_all(self) -> tuple[ContractSalaryControlSnapshot, ...]:
        return tuple(sorted(self.snapshots, key=lambda s: (s.executed_at, str(s.snapshot_id))))

    def list_by_reference_date(self, reference_date: date) -> tuple[ContractSalaryControlSnapshot, ...]:
        return tuple(s for s in self.list_all() if s.reference_date == reference_date)
