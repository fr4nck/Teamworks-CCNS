from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional
from uuid import UUID, uuid4

from domain.contracts.contract import Contract
from domain.contracts.contract_salary_batch_audit import ContractSalaryBatchAuditResult, ContractSalaryBatchAuditService
from domain.contracts.contract_salary_control_projection import (
    ContractSalaryControlProjection,
    ContractSalaryControlProjectionService,
    ContractSalaryControlRow,
    ContractSalaryControlStatus,
)
from domain.contracts.contract_salary_evaluation import _strict_date, _strict_uuid
from domain.convention.smic import SmicTerritory

_ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlResult:
    """Résultat composite du contrôle salarial direct d'un lot de contrats."""

    batch_audit_result: ContractSalaryBatchAuditResult
    projection: ContractSalaryControlProjection
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.batch_audit_result) is not ContractSalaryBatchAuditResult:
            raise TypeError("batch_audit_result doit être un ContractSalaryBatchAuditResult.")
        if type(self.projection) is not ContractSalaryControlProjection:
            raise TypeError("projection doit être un ContractSalaryControlProjection.")
        _strict_uuid(self.id, "id")
        self._validate_consistency()

    def _validate_consistency(self) -> None:
        if self.batch_audit_result.reference_date != self.projection.reference_date:
            raise ValueError("Le résultat d'audit et la projection doivent porter la même date de référence.")
        evaluations = self.batch_audit_result.evaluations
        rows = self.projection.rows
        if len(evaluations) != len(rows):
            raise ValueError("Le nombre d'évaluations doit correspondre au nombre de lignes projetées.")
        if self.batch_audit_result.total_contract_count != self.projection.total_count:
            raise ValueError("Le nombre de contrats audités doit correspondre au nombre de lignes projetées.")

        for evaluation, row in zip(evaluations, rows):
            if type(row) is not ContractSalaryControlRow:
                raise TypeError("projection.rows doit contenir des ContractSalaryControlRow.")
            contract_id = evaluation.contract_id()
            employee_id = evaluation.employee_id()
            if row.contract_id != contract_id:
                raise ValueError("L'ordre des contract_id projetés doit reprendre exactement celui des évaluations.")
            if row.employee_id != employee_id:
                raise ValueError("Chaque ligne doit correspondre au même employee_id que l'évaluation.")
            if evaluation.is_successful():
                if row.status not in (ContractSalaryControlStatus.COMPLIANT, ContractSalaryControlStatus.NON_COMPLIANT):
                    raise ValueError("Une évaluation réussie doit produire une ligne conforme ou non conforme.")
                audit = self.batch_audit_result.audit_result_for_contract(contract_id)
                if audit is None:
                    raise ValueError("Une évaluation réussie doit produire exactement une ligne et un résultat d'audit.")
                expected_shortfall = audit.shortfall_amount()
                if row.shortfall_amount != expected_shortfall:
                    raise ValueError("Le manque salarial de la ligne est incohérent avec le résultat d'audit.")
                if audit.is_valid() and row.status is not ContractSalaryControlStatus.COMPLIANT:
                    raise ValueError("Un audit réussi doit produire une ligne conforme.")
                if not audit.is_valid() and row.status is not ContractSalaryControlStatus.NON_COMPLIANT:
                    raise ValueError("Un audit non conforme doit produire une ligne non conforme.")
            else:
                if row.status is not ContractSalaryControlStatus.NOT_EVALUATED:
                    raise ValueError("Un échec métier doit produire une ligne non évaluée.")
                if row.shortfall_amount != _ZERO:
                    raise ValueError("Une ligne non évaluée ne doit pas porter de manque salarial.")
                if self.batch_audit_result.audit_result_for_contract(contract_id) is not None:
                    raise ValueError("Un échec métier ne doit pas produire de résultat d'audit.")

        if self.projection.compliant_count != self.batch_audit_result.compliant_contract_count:
            raise ValueError("Le compteur des lignes conformes est incohérent avec l'audit.")
        if self.projection.non_compliant_count != self.batch_audit_result.non_compliant_contract_count:
            raise ValueError("Le compteur des lignes non conformes est incohérent avec l'audit.")
        if self.projection.not_evaluated_count != self.batch_audit_result.failed_contract_count:
            raise ValueError("Le compteur des lignes non évaluées est incohérent avec l'audit.")
        if self.projection.total_shortfall_amount != self.batch_audit_result.total_shortfall_amount:
            raise ValueError("Le manque salarial total projeté est incohérent avec l'audit.")
        if self.valid is not self.projection.valid:
            raise ValueError("La validité exposée doit être exactement celle de la projection.")

    @property
    def reference_date(self) -> date:
        return self.projection.reference_date

    @property
    def rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.projection.rows

    @property
    def total_count(self) -> int:
        return self.projection.total_count

    @property
    def compliant_count(self) -> int:
        return self.projection.compliant_count

    @property
    def non_compliant_count(self) -> int:
        return self.projection.non_compliant_count

    @property
    def not_evaluated_count(self) -> int:
        return self.projection.not_evaluated_count

    @property
    def total_shortfall_amount(self) -> Decimal:
        return self.projection.total_shortfall_amount

    @property
    def valid(self) -> bool:
        return self.projection.valid

    def compliant_rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.projection.compliant_rows()

    def non_compliant_rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.projection.non_compliant_rows()

    def not_evaluated_rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.projection.not_evaluated_rows()

    def row_for_contract(self, contract_id: UUID) -> Optional[ContractSalaryControlRow]:
        return self.projection.row_for_contract(contract_id)

    def rows_for_employee(self, employee_id: UUID) -> tuple[ContractSalaryControlRow, ...]:
        return self.projection.rows_for_employee(employee_id)

    def rows_for_status(self, status: ContractSalaryControlStatus) -> tuple[ContractSalaryControlRow, ...]:
        return self.projection.rows_for_status(status)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlService:
    contract_salary_batch_audit_service: ContractSalaryBatchAuditService
    contract_salary_control_projection_service: ContractSalaryControlProjectionService

    def __post_init__(self) -> None:
        if type(self.contract_salary_batch_audit_service) is not ContractSalaryBatchAuditService:
            raise TypeError("contract_salary_batch_audit_service doit être un ContractSalaryBatchAuditService.")
        if type(self.contract_salary_control_projection_service) is not ContractSalaryControlProjectionService:
            raise TypeError("contract_salary_control_projection_service doit être un ContractSalaryControlProjectionService.")

    def control(
        self,
        contracts: Iterable[Contract],
        reference_date: date,
        *,
        territory: Optional[SmicTerritory] = None,
    ) -> ContractSalaryControlResult:
        _strict_date(reference_date)
        if territory is not None and type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        batch_audit_result = self.contract_salary_batch_audit_service.audit(
            contracts,
            reference_date,
            territory=territory,
        )
        projection = self.contract_salary_control_projection_service.project(batch_audit_result)
        return ContractSalaryControlResult(batch_audit_result, projection)
