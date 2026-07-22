from __future__ import annotations

from datetime import date
from typing import Optional, Protocol
from uuid import UUID

from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot


class ContractSalaryControlSnapshotRepository(Protocol):
    def save(self, snapshot: ContractSalaryControlSnapshot) -> ContractSalaryControlSnapshot: ...
    def get(self, snapshot_id: UUID) -> Optional[ContractSalaryControlSnapshot]: ...
    def list_all(self) -> tuple[ContractSalaryControlSnapshot, ...]: ...
    def list_by_reference_date(self, reference_date: date) -> tuple[ContractSalaryControlSnapshot, ...]: ...
