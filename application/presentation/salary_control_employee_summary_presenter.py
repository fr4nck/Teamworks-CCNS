from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from application.presentation.salary_control_presenter import (
    ContractSalaryControlRowViewModel,
    format_euro_amount,
    format_french_date,
)
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlEmployeeSummaryViewModel:
    employee_id: UUID
    employee_id_label: str
    reference_date: date
    reference_date_label: str
    rows: tuple[ContractSalaryControlRowViewModel, ...]
    total_count: int
    compliant_count: int
    non_compliant_count: int
    not_evaluated_count: int
    total_shortfall_amount: Decimal
    total_shortfall_amount_label: str
    valid: bool
    empty: bool
    summary_label: str


@dataclass(frozen=True, slots=True)
class ContractSalaryControlEmployeeSummaryPresenter:
    """Présentateur pur de la synthèse salariale d'un salarié."""

    def present(
        self,
        rows: tuple[ContractSalaryControlRowViewModel, ...],
        employee_id: UUID,
    ) -> ContractSalaryControlEmployeeSummaryViewModel:
        if type(rows) is not tuple:
            raise TypeError("rows doit être un tuple strict.")
        if type(employee_id) is not UUID:
            raise TypeError("employee_id doit être un UUID strict.")

        selected = []
        seen_contract_ids = set()
        reference_date = None
        for row in rows:
            if type(row) is not ContractSalaryControlRowViewModel:
                raise TypeError("rows doit contenir des ContractSalaryControlRowViewModel stricts.")
            if row.employee_id != employee_id:
                continue
            if row.contract_id in seen_contract_ids:
                raise ValueError("contract_id dupliqué dans la synthèse salariale.")
            seen_contract_ids.add(row.contract_id)
            if reference_date is None:
                reference_date = row.reference_date
            elif row.reference_date != reference_date:
                raise ValueError("Les lignes de synthèse doivent partager la même date de référence.")
            if type(row.shortfall_amount) is not Decimal:
                raise TypeError("shortfall_amount doit être un Decimal strict.")
            selected.append(row)

        selected_rows = tuple(selected)
        compliant = sum(1 for row in selected_rows if row.status is ContractSalaryControlStatus.COMPLIANT)
        non_compliant = sum(1 for row in selected_rows if row.status is ContractSalaryControlStatus.NON_COMPLIANT)
        not_evaluated = sum(1 for row in selected_rows if row.status is ContractSalaryControlStatus.NOT_EVALUATED)
        total_shortfall = sum((row.shortfall_amount for row in selected_rows), _ZERO).quantize(_CENT, rounding=ROUND_HALF_UP)
        empty = len(selected_rows) == 0
        valid = not empty and non_compliant == 0 and not_evaluated == 0
        display_date = reference_date or date.min
        return ContractSalaryControlEmployeeSummaryViewModel(
            employee_id=employee_id,
            employee_id_label=str(employee_id),
            reference_date=display_date,
            reference_date_label=format_french_date(display_date),
            rows=selected_rows,
            total_count=len(selected_rows),
            compliant_count=compliant,
            non_compliant_count=non_compliant,
            not_evaluated_count=not_evaluated,
            total_shortfall_amount=total_shortfall,
            total_shortfall_amount_label=format_euro_amount(total_shortfall),
            valid=valid,
            empty=empty,
            summary_label=_summary_label(len(selected_rows), compliant, non_compliant, not_evaluated, total_shortfall, valid, empty),
        )


def _summary_label(total, compliant, non_compliant, not_evaluated, shortfall, valid, empty):
    if empty:
        return "Aucun contrat salarial chargé pour ce salarié dans le périmètre courant."
    status = "synthèse valide" if valid else "synthèse non valide"
    return (
        f"{total} contrat{'s' if total > 1 else ''} chargé{'s' if total > 1 else ''} "
        f"dans le périmètre courant : {compliant} conforme{'s' if compliant > 1 else ''}, "
        f"{non_compliant} non conforme{'s' if non_compliant > 1 else ''}, "
        f"{not_evaluated} non évaluable{'s' if not_evaluated > 1 else ''}. "
        f"Écarts : {format_euro_amount(shortfall)} ; {status}."
    )
