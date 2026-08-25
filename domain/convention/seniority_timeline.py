from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True, slots=True)
class CCNSContractSeniorityTimelineResult:
    current_contract_start: date
    evaluation_date: date
    current_contract_end: Optional[date]
    elapsed_contract_months: int
    recognized_effective_work_months_at_start: Optional[int]
    recognized_company_seniority_months_at_start: Optional[int]
    excluded_current_contract_effective_months: int
    effective_work_months: int
    company_seniority_months: int
    history_complete: bool

    @property
    def prior_history_requires_review(self) -> bool:
        return not self.history_complete

    @property
    def current_contract_effective_months(self) -> int:
        return max(0, self.elapsed_contract_months - self.excluded_current_contract_effective_months)


class CCNSContractSeniorityTimelineService:
    """Construit les compteurs d'ancienneté utilisables par le moteur CCNS.

    L'ancienneté acquise pendant le contrat en cours est toujours calculée à la
    date d'évaluation. L'historique antérieur n'est ajouté que s'il a été
    explicitement reconnu/validé. Une valeur ``None`` n'est donc jamais assimilée
    silencieusement à une ancienneté historique nulle : le résultat reste exploitable
    comme minimum connu, mais ``history_complete`` vaut ``False``.

    ``excluded_current_contract_effective_months`` permet de retrancher, après
    validation métier, des mois du contrat en cours qui ne doivent pas compter
    comme travail effectif pour les paliers de l'article 9.2.3.1. Cette exclusion
    ne réduit pas l'ancienneté d'entreprise calendaire.
    """

    def evaluate(
        self,
        *,
        current_contract_start: date,
        evaluation_date: date,
        current_contract_end: Optional[date] = None,
        recognized_effective_work_months_at_start: Optional[int] = None,
        recognized_company_seniority_months_at_start: Optional[int] = None,
        excluded_current_contract_effective_months: int = 0,
    ) -> CCNSContractSeniorityTimelineResult:
        for name, value in (
            ("current_contract_start", current_contract_start),
            ("evaluation_date", evaluation_date),
        ):
            if type(value) is not date:
                raise TypeError(f"{name} doit être une date stricte.")
        if current_contract_end is not None and type(current_contract_end) is not date:
            raise TypeError("current_contract_end doit être une date stricte ou None.")
        if evaluation_date < current_contract_start:
            raise ValueError("evaluation_date ne peut pas précéder le début du contrat courant.")
        if current_contract_end is not None and current_contract_end < current_contract_start:
            raise ValueError("current_contract_end ne peut pas précéder le début du contrat courant.")

        for name, value in (
            ("recognized_effective_work_months_at_start", recognized_effective_work_months_at_start),
            ("recognized_company_seniority_months_at_start", recognized_company_seniority_months_at_start),
        ):
            if value is not None:
                if type(value) is not int or isinstance(value, bool):
                    raise TypeError(f"{name} doit être un entier strict ou None.")
                if value < 0:
                    raise ValueError(f"{name} ne peut pas être négatif.")

        if type(excluded_current_contract_effective_months) is not int or isinstance(
            excluded_current_contract_effective_months, bool
        ):
            raise TypeError("excluded_current_contract_effective_months doit être un entier strict.")
        if excluded_current_contract_effective_months < 0:
            raise ValueError("excluded_current_contract_effective_months ne peut pas être négatif.")

        accrual_end = evaluation_date
        if current_contract_end is not None and current_contract_end < accrual_end:
            accrual_end = current_contract_end
        elapsed = self.completed_calendar_months(current_contract_start, accrual_end)
        if excluded_current_contract_effective_months > elapsed:
            raise ValueError(
                "excluded_current_contract_effective_months ne peut pas dépasser les mois écoulés du contrat courant."
            )

        effective_base = recognized_effective_work_months_at_start or 0
        company_base = recognized_company_seniority_months_at_start or 0
        effective_current = elapsed - excluded_current_contract_effective_months
        history_complete = (
            recognized_effective_work_months_at_start is not None
            and recognized_company_seniority_months_at_start is not None
        )

        return CCNSContractSeniorityTimelineResult(
            current_contract_start=current_contract_start,
            evaluation_date=evaluation_date,
            current_contract_end=current_contract_end,
            elapsed_contract_months=elapsed,
            recognized_effective_work_months_at_start=recognized_effective_work_months_at_start,
            recognized_company_seniority_months_at_start=recognized_company_seniority_months_at_start,
            excluded_current_contract_effective_months=excluded_current_contract_effective_months,
            effective_work_months=effective_base + effective_current,
            company_seniority_months=company_base + elapsed,
            history_complete=history_complete,
        )

    @staticmethod
    def completed_calendar_months(start: date, end: date) -> int:
        if type(start) is not date or type(end) is not date:
            raise TypeError("start et end doivent être des dates strictes.")
        if end < start:
            raise ValueError("end ne peut pas précéder start.")

        months = (end.year - start.year) * 12 + (end.month - start.month)
        anniversary = _add_months_clamped(start, months)
        if anniversary > end:
            months -= 1
        return max(0, months)


def _add_months_clamped(value: date, months: int) -> date:
    if type(value) is not date:
        raise TypeError("value doit être une date stricte.")
    if type(months) is not int or isinstance(months, bool):
        raise TypeError("months doit être un entier strict.")
    total_month = value.year * 12 + (value.month - 1) + months
    year, month_index = divmod(total_month, 12)
    month = month_index + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
