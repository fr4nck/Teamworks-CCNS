from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from application.presentation.salary_control_presenter import ContractSalaryControlRowViewModel
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory


@dataclass(frozen=True, slots=True)
class ContractSalaryControlDetailViewModel:
    contract_id: UUID
    employee_id: Optional[UUID]
    employee_id_label: str
    reference_date: date
    reference_date_label: str
    status: ContractSalaryControlStatus
    status_label: str
    classification_code: Optional[str]
    classification_code_label: str
    remuneration_amount: Optional[Decimal]
    remuneration_amount_label: str
    applicable_minimum_amount: Optional[Decimal]
    applicable_minimum_amount_label: str
    minimum_source: Optional[ApplicableSalaryMinimumSource]
    minimum_source_label: str
    shortfall_amount: Decimal
    shortfall_amount_label: str
    territory: Optional[SmicTerritory]
    territory_label: str
    failure_reason: Optional[ContractSalaryEvaluationFailureReason]
    failure_reason_label: str
    failure_message: Optional[str]
    failure_message_label: str
    issue_code: Optional[str]
    issue_code_label: str
    issue_message: Optional[str]
    issue_message_label: str


@dataclass(frozen=True, slots=True)
class ContractSalaryControlDetailPresenter:
    """Construit la fiche détail depuis une ligne salariale déjà présentée."""

    def present(self, row: ContractSalaryControlRowViewModel) -> ContractSalaryControlDetailViewModel:
        if type(row) is not ContractSalaryControlRowViewModel:
            raise TypeError("row doit être un ContractSalaryControlRowViewModel strict.")
        return ContractSalaryControlDetailViewModel(
            contract_id=row.contract_id,
            employee_id=row.employee_id,
            employee_id_label=row.employee_id_label,
            reference_date=row.reference_date,
            reference_date_label=row.reference_date_label,
            status=row.status,
            status_label=row.status_label,
            classification_code=row.classification_code,
            classification_code_label=row.classification_code_label,
            remuneration_amount=row.remuneration_amount,
            remuneration_amount_label=row.remuneration_amount_label,
            applicable_minimum_amount=row.applicable_minimum_amount,
            applicable_minimum_amount_label=row.applicable_minimum_amount_label,
            minimum_source=row.minimum_source,
            minimum_source_label=row.minimum_source_label,
            shortfall_amount=row.shortfall_amount,
            shortfall_amount_label=row.shortfall_amount_label,
            territory=row.territory,
            territory_label=row.territory_label,
            failure_reason=row.failure_reason,
            failure_reason_label=row.failure_reason_label,
            failure_message=row.failure_message,
            failure_message_label=row.failure_message_label,
            issue_code=row.issue_code,
            issue_code_label=row.issue_code_label,
            issue_message=row.issue_message,
            issue_message_label=row.issue_message_label,
        )


def detail_from_audit_row(row) -> ContractSalaryControlDetailViewModel:
    salary_row = _salary_row_from_audit_row(row)
    return ContractSalaryControlDetailPresenter().present(salary_row)


def _salary_row_from_audit_row(row) -> ContractSalaryControlRowViewModel:
    if isinstance(row, dict):
        salary_row = row.get("salary_control_row")
    else:
        salary_row = getattr(row, "salary_control_row", None)
    if salary_row is None:
        raise ValueError("Aucun détail salarial n'est disponible pour cette ligne d'audit.")
    if type(salary_row) is not ContractSalaryControlRowViewModel:
        raise TypeError("salary_control_row doit être un ContractSalaryControlRowViewModel strict.")
    return salary_row
