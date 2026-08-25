from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Optional

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from domain.convention.part_time_minimum_increase import increase_rate_for_weekly_hours
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


_FULL_TIME_WEEKLY_HOURS = Decimal("35.00")
_CENT = Decimal("0.01")


def _quantize_cents(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def validate_ccns_annual_compensation(
    *,
    group_code: str,
    reference_date: date,
    weekly_hours: Decimal,
    gross_annual_salary: Optional[Decimal],
    reference_period_months: int = 12,
) -> ContractCompensationPreflight:
    """Contrôle le minimum annuel G7/G8 sans conversion mensuelle artificielle.

    La CCNS 9.2.1 définit G7/G8 par un minimum annuel à temps plein et prévoit
    un prorata selon le nombre de mois écoulés sur la période concernée. Le
    prorata temps partiel découle du principe de proportionnalité de la
    rémunération prévu par l'article L.3123-5 du Code du travail. La majoration
    CCNS des temps partiels de moins de 24 h reste appliquée.

    ``gross_annual_salary`` doit être exprimé sur la même période que
    ``reference_period_months``. Dans l'assistant de création, le champ est une
    rémunération annuelle de référence : on contrôle donc 12 mois.
    """
    if type(reference_date) is not date:
        raise TypeError("reference_date doit être une date stricte.")
    if type(weekly_hours) is not Decimal:
        raise TypeError("weekly_hours doit être un Decimal strict.")
    if weekly_hours <= Decimal("0.00"):
        return ContractCompensationPreflight(
            False,
            "La durée hebdomadaire doit être strictement positive.",
            control_scope="CCNS_ANNUAL",
        )
    if type(reference_period_months) is not int or isinstance(reference_period_months, bool):
        raise TypeError("reference_period_months doit être un entier strict.")
    if not 1 <= reference_period_months <= 12:
        raise ValueError("reference_period_months doit être compris entre 1 et 12.")

    presenter = CCNSContractCompliancePresenter()
    choices = presenter.group_choices(reference_date)
    choice = next((item for item in choices if item.code == (group_code or "").strip().upper()), None)
    if choice is None:
        return ContractCompensationPreflight(
            False,
            "Groupe CCNS inconnu ou non applicable à cette date.",
            control_scope="CCNS_ANNUAL",
        )
    if choice.periodicity is not SalaryMinimumPeriodicity.ANNUAL:
        return ContractCompensationPreflight(
            False,
            "Le groupe sélectionné ne relève pas d'un minimum annuel CCNS.",
            control_scope="CCNS_ANNUAL",
        )
    if gross_annual_salary is None or gross_annual_salary <= Decimal("0.00"):
        return ContractCompensationPreflight(
            False,
            "La rémunération brute annuelle de référence est obligatoire pour G7/G8.",
            control_scope="CCNS_ANNUAL",
        )

    with localcontext() as context:
        context.prec = 28
        work_ratio = min(weekly_hours, _FULL_TIME_WEEKLY_HOURS) / _FULL_TIME_WEEKLY_HOURS
        increase_rate = increase_rate_for_weekly_hours(weekly_hours) if weekly_hours < _FULL_TIME_WEEKLY_HOURS else Decimal("0.00")
        period_ratio = Decimal(reference_period_months) / Decimal("12")
        required = choice.minimum_amount * work_ratio * (Decimal("1.00") + increase_rate) * period_ratio
    required = _quantize_cents(required)
    proposed = _quantize_cents(gross_annual_salary)
    compliant = proposed >= required
    return ContractCompensationPreflight(
        compliant,
        (
            "Rémunération annuelle conforme au minimum CCNS applicable."
            if compliant
            else "La rémunération annuelle est inférieure au minimum CCNS applicable."
        ),
        required_minimum=required,
        proposed_amount=proposed,
        control_scope="CCNS_ANNUAL",
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
