from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, date
from typing import Callable, Optional
from uuid import UUID, uuid4
from decimal import Decimal

from application.presentation.salary_control_presenter import ContractSalaryControlRowViewModel, ContractSalaryControlViewModel
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot, ContractSalaryControlSnapshotRow
from domain.repositories.contract_salary_control_snapshot_repository import ContractSalaryControlSnapshotRepository


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshotFactory:
    snapshot_id_factory: Callable[[], UUID] = uuid4
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)

    def from_view_model(self, view_model: ContractSalaryControlViewModel, *, created_by: Optional[str] = None) -> ContractSalaryControlSnapshot:
        if type(view_model) is not ContractSalaryControlViewModel:
            raise TypeError("view_model doit être un ContractSalaryControlViewModel strict.")
        return self.from_rows(
            view_model.rows,
            reference_date=view_model.reference_date,
            total_contracts=view_model.global_total_count,
            compliant_contracts=view_model.global_compliant_count,
            non_compliant_contracts=view_model.global_non_compliant_count,
            not_evaluated_contracts=view_model.global_not_evaluated_count,
            created_by=created_by,
        )

    def from_rows(
        self,
        rows: tuple[ContractSalaryControlRowViewModel, ...],
        *,
        reference_date: date | None = None,
        total_contracts: int | None = None,
        compliant_contracts: int | None = None,
        non_compliant_contracts: int | None = None,
        not_evaluated_contracts: int | None = None,
        created_by: Optional[str] = None,
    ) -> ContractSalaryControlSnapshot:
        if type(rows) is not tuple:
            raise TypeError("rows doit être un tuple strict.")
        for row in rows:
            if type(row) is not ContractSalaryControlRowViewModel:
                raise TypeError("rows doit contenir des ContractSalaryControlRowViewModel.")
        if reference_date is None:
            reference_date = rows[0].reference_date if rows else date.today()
        seen = set()
        snapshot_rows = []
        for row in rows:
            if row.reference_date != reference_date:
                raise ValueError("Toutes les lignes doivent porter la même date de référence que le snapshot.")
            if row.contract_id in seen:
                raise ValueError("Plusieurs lignes portent le même contract_id.")
            seen.add(row.contract_id)
            snapshot_rows.append(ContractSalaryControlSnapshotRow(
                contract_id=row.contract_id,
                employee_id=row.employee_id,
                status=row.status,
                remuneration_amount=row.remuneration_amount,
                applicable_minimum_amount=row.applicable_minimum_amount,
                shortfall_amount=row.shortfall_amount,
                classification_code=row.classification_code,
                minimum_source=row.minimum_source,
                territory=row.territory,
                failure_reason=row.failure_reason,
                failure_message=row.failure_message,
                issue_code=row.issue_code,
                issue_message=row.issue_message,
            ))
        ordered = tuple(snapshot_rows)
        compliant = sum(1 for row in ordered if row.status is ContractSalaryControlStatus.COMPLIANT)
        non_compliant = sum(1 for row in ordered if row.status is ContractSalaryControlStatus.NON_COMPLIANT)
        not_evaluated = sum(1 for row in ordered if row.status is ContractSalaryControlStatus.NOT_EVALUATED)
        return ContractSalaryControlSnapshot(
            snapshot_id=self.snapshot_id_factory(),
            reference_date=reference_date,
            executed_at=self.clock(),
            total_contracts=len(ordered) if total_contracts is None else total_contracts,
            compliant_contracts=compliant if compliant_contracts is None else compliant_contracts,
            non_compliant_contracts=non_compliant if non_compliant_contracts is None else non_compliant_contracts,
            not_evaluated_contracts=not_evaluated if not_evaluated_contracts is None else not_evaluated_contracts,
            total_shortfall_amount=sum((row.shortfall_amount for row in ordered), Decimal('0.00')),
            rows=ordered,
            created_by=created_by,
        )


@dataclass(frozen=True, slots=True)
class SaveContractSalaryControlSnapshotUseCase:
    repository: ContractSalaryControlSnapshotRepository
    factory: ContractSalaryControlSnapshotFactory = ContractSalaryControlSnapshotFactory()

    def execute(self, view_model: ContractSalaryControlViewModel, *, created_by: Optional[str] = None) -> ContractSalaryControlSnapshot:
        snapshot = self.factory.from_view_model(view_model, created_by=created_by)
        return self.repository.save(snapshot)


@dataclass(frozen=True, slots=True)
class ListContractSalaryControlSnapshotsUseCase:
    repository: ContractSalaryControlSnapshotRepository

    def execute(self, *, reference_date: date | None = None) -> tuple[ContractSalaryControlSnapshot, ...]:
        if reference_date is None:
            return self.repository.list_all()
        return self.repository.list_by_reference_date(reference_date)
