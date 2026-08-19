from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity
from domain.convention.smic import SmicTerritory


@dataclass(frozen=True, slots=True)
class ContractCompensationPreflight:
    compliant: bool
    message: str
    required_minimum: Optional[Decimal] = None
    proposed_amount: Optional[Decimal] = None
    control_scope: str = ""


def validate_ccns_monthly_compensation(
    *,
    group_code: str,
    reference_date: date,
    weekly_hours: Decimal,
    gross_monthly_salary: Optional[Decimal],
    territory: SmicTerritory = SmicTerritory.METROPOLITAN_FRANCE,
) -> ContractCompensationPreflight:
    presenter = CCNSContractCompliancePresenter()
    choices = presenter.group_choices(reference_date)
    choice = next((item for item in choices if item.code == (group_code or "").strip().upper()), None)
    if choice is None:
        return ContractCompensationPreflight(False, "Groupe CCNS inconnu ou non applicable à cette date.", control_scope="CCNS")
    if choice.periodicity is SalaryMinimumPeriodicity.ANNUAL:
        return ContractCompensationPreflight(
            True,
            "Minimum CCNS annuel : aucun contrôle mensuel artificiel n'est appliqué à G7/G8.",
            required_minimum=choice.minimum_amount,
            proposed_amount=gross_monthly_salary,
            control_scope="CCNS_ANNUAL",
        )
    if gross_monthly_salary is None or gross_monthly_salary <= Decimal("0"):
        return ContractCompensationPreflight(False, "La rémunération brute mensuelle est obligatoire.", control_scope="CCNS_MONTHLY")
    if weekly_hours <= Decimal("0"):
        return ContractCompensationPreflight(False, "La durée hebdomadaire doit être strictement positive.", control_scope="CCNS_MONTHLY")

    preview = presenter.evaluate_monthly(
        group_code=choice.code,
        reference_date=reference_date,
        weekly_hours=weekly_hours,
        remuneration_amount=gross_monthly_salary,
        territory=territory,
    )
    if not preview.compliant:
        return ContractCompensationPreflight(
            False,
            "La rémunération est inférieure au minimum CCNS/SMIC applicable.",
            required_minimum=preview.required_minimum_amount,
            proposed_amount=preview.remuneration_amount,
            control_scope="CCNS_MONTHLY",
        )
    return ContractCompensationPreflight(
        True,
        "Rémunération conforme au minimum CCNS/SMIC applicable.",
        required_minimum=preview.required_minimum_amount,
        proposed_amount=preview.remuneration_amount,
        control_scope="CCNS_MONTHLY",
    )


def validate_cee_daily_compensation(
    *,
    qualification: Optional[str],
    employer_daily_rate: Optional[Decimal],
    legal_minimum_daily_rate: Decimal,
) -> ContractCompensationPreflight:
    if not qualification:
        return ContractCompensationPreflight(False, "La qualification ou le statut CEE est obligatoire.", control_scope="CEE")
    if employer_daily_rate is None:
        return ContractCompensationPreflight(False, "Aucun barème employeur CEE n'est applicable à cette date.", required_minimum=legal_minimum_daily_rate, control_scope="CEE")
    if employer_daily_rate < legal_minimum_daily_rate:
        return ContractCompensationPreflight(
            False,
            "Le barème employeur CEE est inférieur au minimum légal applicable.",
            required_minimum=legal_minimum_daily_rate,
            proposed_amount=employer_daily_rate,
            control_scope="CEE",
        )
    return ContractCompensationPreflight(
        True,
        "Barème CEE conforme au minimum légal applicable.",
        required_minimum=legal_minimum_daily_rate,
        proposed_amount=employer_daily_rate,
        control_scope="CEE",
    )
