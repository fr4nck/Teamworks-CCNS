from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Optional


CCNS_SENIORITY_RULE_CODE = "CCNS_SENIORITY_9_2_3_1"
CCNS_SENIORITY_SOURCE_REFERENCE = "CCNS, article 9.2.3.1 — Ancienneté d'entreprise"

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")
_ONE = Decimal("1.00")
_STANDARD_STEP_MONTHS = 24
_G1_EXCEPTIONAL_SENIORITY_MONTHS = 36
_STANDARD_STEP_PERCENT = Decimal("1.00")
_G1_EXCEPTIONAL_PERCENT = Decimal("5.00")
_MAX_TOTAL_PERCENT = Decimal("15.00")


def _quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def _group_number(group_code: str) -> Optional[int]:
    if type(group_code) is not str:
        raise TypeError("group_code doit être une chaîne.")
    normalized = group_code.strip().upper()
    if not normalized:
        raise ValueError("group_code est obligatoire.")
    if normalized.startswith("G"):
        normalized = normalized[1:]
    if not normalized.isdigit():
        return None
    number = int(normalized)
    return number if 1 <= number <= 8 else None


@dataclass(frozen=True, slots=True)
class CCNSSeniorityResult:
    group_code: str
    applicable: bool
    effective_work_months: int
    company_seniority_months: int
    work_ratio: Decimal
    smc_group3_monthly_amount: Decimal
    standard_rate_percent: Decimal
    g1_exceptional_rate_percent: Decimal
    total_rate_percent: Decimal
    full_time_reference_amount: Decimal
    monthly_due_amount: Decimal
    next_standard_increment_at_effective_work_month: Optional[int]
    next_g1_exceptional_at_company_seniority_month: Optional[int]
    rule_code: str = CCNS_SENIORITY_RULE_CODE
    source_reference: str = CCNS_SENIORITY_SOURCE_REFERENCE

    def __post_init__(self) -> None:
        for field_name in (
            "work_ratio",
            "smc_group3_monthly_amount",
            "standard_rate_percent",
            "g1_exceptional_rate_percent",
            "total_rate_percent",
            "full_time_reference_amount",
            "monthly_due_amount",
        ):
            if type(getattr(self, field_name)) is not Decimal:
                raise TypeError(f"{field_name} doit être un Decimal strict.")
        if self.effective_work_months < 0:
            raise ValueError("effective_work_months ne peut pas être négatif.")
        if self.company_seniority_months < 0:
            raise ValueError("company_seniority_months ne peut pas être négatif.")
        if not (_ZERO <= self.work_ratio <= _ONE):
            raise ValueError("work_ratio doit être compris entre 0 et 1.")
        if self.smc_group3_monthly_amount <= _ZERO:
            raise ValueError("smc_group3_monthly_amount doit être strictement positif.")
        if not (_ZERO <= self.total_rate_percent <= _MAX_TOTAL_PERCENT):
            raise ValueError("total_rate_percent doit être compris entre 0 et 15.")


class CCNSSeniorityService:
    """Calcule la prime d'ancienneté d'entreprise prévue par l'article 9.2.3.1.

    Le service ne reconstitue jamais l'ancienneté depuis l'historique des contrats.
    Il reçoit deux compteurs déjà reconnus/validés par l'employeur :

    * ``effective_work_months`` pour les paliers conventionnels de 24 mois ;
    * ``company_seniority_months`` pour le seuil exceptionnel G1 de 3 ans.

    La disposition historique de revalorisation de l'article 9.2.3.2 n'est pas
    incluse dans ce calcul courant et doit rester un traitement de migration/audit
    distinct lorsqu'un dossier ancien est concerné.
    """

    def evaluate(
        self,
        *,
        group_code: str,
        effective_work_months: int,
        company_seniority_months: int,
        smc_group3_monthly_amount: Decimal,
        work_ratio: Decimal = Decimal("1.00"),
    ) -> CCNSSeniorityResult:
        group_number = _group_number(group_code)
        if type(effective_work_months) is not int or isinstance(effective_work_months, bool):
            raise TypeError("effective_work_months doit être un entier strict.")
        if type(company_seniority_months) is not int or isinstance(company_seniority_months, bool):
            raise TypeError("company_seniority_months doit être un entier strict.")
        if type(smc_group3_monthly_amount) is not Decimal:
            raise TypeError("smc_group3_monthly_amount doit être un Decimal strict.")
        if type(work_ratio) is not Decimal:
            raise TypeError("work_ratio doit être un Decimal strict.")
        if effective_work_months < 0:
            raise ValueError("effective_work_months ne peut pas être négatif.")
        if company_seniority_months < 0:
            raise ValueError("company_seniority_months ne peut pas être négatif.")
        if smc_group3_monthly_amount <= _ZERO:
            raise ValueError("smc_group3_monthly_amount doit être strictement positif.")
        if not (_ZERO <= work_ratio <= _ONE):
            raise ValueError("work_ratio doit être compris entre 0 et 1.")

        applicable = group_number is not None and 1 <= group_number <= 6
        if not applicable:
            return CCNSSeniorityResult(
                group_code=group_code.strip().upper(),
                applicable=False,
                effective_work_months=effective_work_months,
                company_seniority_months=company_seniority_months,
                work_ratio=work_ratio,
                smc_group3_monthly_amount=smc_group3_monthly_amount,
                standard_rate_percent=_ZERO,
                g1_exceptional_rate_percent=_ZERO,
                total_rate_percent=_ZERO,
                full_time_reference_amount=_ZERO,
                monthly_due_amount=_ZERO,
                next_standard_increment_at_effective_work_month=None,
                next_g1_exceptional_at_company_seniority_month=None,
            )

        completed_steps = effective_work_months // _STANDARD_STEP_MONTHS
        standard_rate = min(Decimal(completed_steps) * _STANDARD_STEP_PERCENT, _MAX_TOTAL_PERCENT)
        g1_exceptional_rate = (
            _G1_EXCEPTIONAL_PERCENT
            if group_number == 1 and company_seniority_months >= _G1_EXCEPTIONAL_SENIORITY_MONTHS
            else _ZERO
        )
        total_rate = min(standard_rate + g1_exceptional_rate, _MAX_TOTAL_PERCENT)

        with localcontext() as ctx:
            ctx.prec = 28
            full_time_reference = _quantize_amount(
                smc_group3_monthly_amount * total_rate / Decimal("100")
            )
            monthly_due = _quantize_amount(
                smc_group3_monthly_amount * total_rate / Decimal("100") * work_ratio
            )

        next_standard_increment = None
        if total_rate < _MAX_TOTAL_PERCENT:
            next_standard_increment = (completed_steps + 1) * _STANDARD_STEP_MONTHS

        next_g1_exceptional = None
        if group_number == 1 and company_seniority_months < _G1_EXCEPTIONAL_SENIORITY_MONTHS:
            next_g1_exceptional = _G1_EXCEPTIONAL_SENIORITY_MONTHS

        return CCNSSeniorityResult(
            group_code=f"G{group_number}",
            applicable=True,
            effective_work_months=effective_work_months,
            company_seniority_months=company_seniority_months,
            work_ratio=work_ratio,
            smc_group3_monthly_amount=smc_group3_monthly_amount,
            standard_rate_percent=standard_rate,
            g1_exceptional_rate_percent=g1_exceptional_rate,
            total_rate_percent=total_rate,
            full_time_reference_amount=full_time_reference,
            monthly_due_amount=monthly_due,
            next_standard_increment_at_effective_work_month=next_standard_increment,
            next_g1_exceptional_at_company_seniority_month=next_g1_exceptional,
        )
