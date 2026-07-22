from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from application.presentation.salary_control_presenter import (
    ContractSalaryControlRowViewModel,
    format_euro_amount,
    format_french_date,
)
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus

_PERCENT = Decimal("0.01")
_ZERO = Decimal("0.00")
_HUNDRED = Decimal("100")


@dataclass(frozen=True, slots=True)
class ContractSalaryDashboardViewModel:
    reference_date: date
    reference_date_label: str
    total_contracts: int
    compliant_contracts: int
    non_compliant_contracts: int
    not_evaluated_contracts: int
    compliant_percentage: Decimal
    non_compliant_percentage: Decimal
    total_shortfall_amount: Decimal
    total_shortfall_amount_label: str
    valid: bool
    summary_label: str


@dataclass(frozen=True, slots=True)
class ContractSalaryDashboardPresenter:
    """Présentateur pur des indicateurs salariaux du périmètre d'audit courant."""

    def present(
        self,
        rows: tuple[ContractSalaryControlRowViewModel, ...],
    ) -> ContractSalaryDashboardViewModel:
        if type(rows) is not tuple:
            raise TypeError("rows doit être un tuple strict.")

        reference_date = None
        total_shortfall = _ZERO
        compliant = 0
        non_compliant = 0
        not_evaluated = 0
        seen_contract_ids = set()

        for row in rows:
            if type(row) is not ContractSalaryControlRowViewModel:
                raise TypeError("rows doit contenir des ContractSalaryControlRowViewModel stricts.")
            if row.contract_id in seen_contract_ids:
                raise ValueError("contract_id dupliqué dans le tableau de bord salarial.")
            seen_contract_ids.add(row.contract_id)
            if reference_date is None:
                reference_date = row.reference_date
            elif row.reference_date != reference_date:
                raise ValueError("Les lignes du tableau de bord doivent partager la même date de référence.")
            if type(row.shortfall_amount) is not Decimal:
                raise TypeError("shortfall_amount doit être un Decimal strict.")

            if row.status is ContractSalaryControlStatus.COMPLIANT:
                compliant += 1
            elif row.status is ContractSalaryControlStatus.NON_COMPLIANT:
                non_compliant += 1
            elif row.status is ContractSalaryControlStatus.NOT_EVALUATED:
                not_evaluated += 1
            else:
                raise ValueError("Statut salarial inconnu dans le tableau de bord.")
            total_shortfall += row.shortfall_amount

        total = len(rows)
        total_shortfall = total_shortfall.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        compliant_percentage = _percentage(compliant, total)
        non_compliant_percentage = _percentage(non_compliant, total)
        valid = total > 0 and non_compliant == 0 and not_evaluated == 0
        display_date = reference_date or date.min
        return ContractSalaryDashboardViewModel(
            reference_date=display_date,
            reference_date_label=format_french_date(display_date),
            total_contracts=total,
            compliant_contracts=compliant,
            non_compliant_contracts=non_compliant,
            not_evaluated_contracts=not_evaluated,
            compliant_percentage=compliant_percentage,
            non_compliant_percentage=non_compliant_percentage,
            total_shortfall_amount=total_shortfall,
            total_shortfall_amount_label=format_euro_amount(total_shortfall),
            valid=valid,
            summary_label=_summary_label(total, compliant, non_compliant, not_evaluated, total_shortfall, valid),
        )


def _percentage(count: int, total: int) -> Decimal:
    if total == 0:
        return _ZERO
    return ((Decimal(count) / Decimal(total)) * _HUNDRED).quantize(_PERCENT, rounding=ROUND_HALF_UP)


def _summary_label(total, compliant, non_compliant, not_evaluated, shortfall, valid):
    if total == 0:
        return "Aucun contrat salarial contrôlé dans le périmètre courant."
    status = "tableau de bord valide" if valid else "tableau de bord non valide"
    return (
        f"{total} contrat{'s' if total > 1 else ''} contrôlé{'s' if total > 1 else ''} : "
        f"{compliant} conforme{'s' if compliant > 1 else ''}, "
        f"{non_compliant} non conforme{'s' if non_compliant > 1 else ''}, "
        f"{not_evaluated} non évaluable{'s' if not_evaluated > 1 else ''}. "
        f"Écarts : {format_euro_amount(shortfall)} ; {status}."
    )
