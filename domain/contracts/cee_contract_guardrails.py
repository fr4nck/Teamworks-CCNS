from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


CEE_80_DAY_SOURCE = "CASF, article L.432-4"
CEE_48H_AVERAGE_SOURCE = "CASF, article L.432-4"
YOUNG_WORKER_DURATION_SOURCE = "Code du travail, article L.3162-1"

_CEE_MAX_DAYS_ROLLING_12M = 80
_CEE_MAX_AVERAGE_WEEKLY_HOURS_6M = Decimal("48.00")
_YOUNG_WORKER_MAX_DAILY_HOURS = Decimal("8.00")
_YOUNG_WORKER_MAX_WEEKLY_HOURS = Decimal("35.00")


@dataclass(frozen=True, slots=True)
class CEEContractGuardrailResult:
    days_rolling_12_months: Optional[int]
    days_limit_compliant: Optional[bool]
    average_weekly_hours_all_contracts_6m: Optional[Decimal]
    average_hours_compliant: Optional[bool]
    worker_age_years: Optional[int]
    planned_max_daily_hours: Optional[Decimal]
    planned_max_weekly_hours: Optional[Decimal]
    minor_daily_hours_compliant: Optional[bool]
    minor_weekly_hours_compliant: Optional[bool]
    require_average_hours_check: bool
    require_minor_schedule_check: bool

    @property
    def is_minor(self) -> bool:
        return self.worker_age_years is not None and self.worker_age_years < 18

    @property
    def has_known_non_compliance(self) -> bool:
        return any(
            value is False
            for value in (
                self.days_limit_compliant,
                self.average_hours_compliant,
                self.minor_daily_hours_compliant,
                self.minor_weekly_hours_compliant,
            )
        )

    @property
    def requires_review(self) -> bool:
        if self.days_limit_compliant is None:
            return True
        if self.require_average_hours_check and self.average_hours_compliant is None:
            return True
        if self.worker_age_years is None:
            return True
        if self.is_minor and self.require_minor_schedule_check:
            return (
                self.minor_daily_hours_compliant is None
                or self.minor_weekly_hours_compliant is None
            )
        return False

    @property
    def compliant(self) -> bool:
        return not self.has_known_non_compliance and not self.requires_review


class CEEContractGuardrailService:
    """Contrôles légaux CEE utilisables par la création et l'audit.

    Le plafond des 80 jours est apprécié sur 12 mois consécutifs. La moyenne de
    48 h tient compte de l'ensemble des contrats. Pour un jeune travailleur, la
    règle de base de l'animation reste 8 h par jour et 35 h par semaine ; les
    dérogations automatiques de certains secteurs de chantier ne sont pas
    appliquées à l'animation.

    Les données qui ne sont pas disponibles ne sont jamais transformées en
    conformité implicite : le résultat demande alors une revue.
    """

    def evaluate(
        self,
        *,
        days_rolling_12_months: Optional[int],
        average_weekly_hours_all_contracts_6m: Optional[Decimal] = None,
        worker_age_years: Optional[int] = None,
        planned_max_daily_hours: Optional[Decimal] = None,
        planned_max_weekly_hours: Optional[Decimal] = None,
        require_average_hours_check: bool = False,
        require_minor_schedule_check: bool = True,
    ) -> CEEContractGuardrailResult:
        if days_rolling_12_months is not None:
            if type(days_rolling_12_months) is not int or isinstance(days_rolling_12_months, bool):
                raise TypeError("days_rolling_12_months doit être un entier strict ou None.")
            if days_rolling_12_months < 0:
                raise ValueError("days_rolling_12_months ne peut pas être négatif.")
        if average_weekly_hours_all_contracts_6m is not None:
            if type(average_weekly_hours_all_contracts_6m) is not Decimal:
                raise TypeError("average_weekly_hours_all_contracts_6m doit être un Decimal strict ou None.")
            if average_weekly_hours_all_contracts_6m < Decimal("0.00"):
                raise ValueError("average_weekly_hours_all_contracts_6m ne peut pas être négatif.")
        if worker_age_years is not None:
            if type(worker_age_years) is not int or isinstance(worker_age_years, bool):
                raise TypeError("worker_age_years doit être un entier strict ou None.")
            if worker_age_years < 0:
                raise ValueError("worker_age_years ne peut pas être négatif.")
        for name, value in (
            ("planned_max_daily_hours", planned_max_daily_hours),
            ("planned_max_weekly_hours", planned_max_weekly_hours),
        ):
            if value is not None:
                if type(value) is not Decimal:
                    raise TypeError(f"{name} doit être un Decimal strict ou None.")
                if value < Decimal("0.00"):
                    raise ValueError(f"{name} ne peut pas être négatif.")
        for name, value in (
            ("require_average_hours_check", require_average_hours_check),
            ("require_minor_schedule_check", require_minor_schedule_check),
        ):
            if type(value) is not bool:
                raise TypeError(f"{name} doit être un booléen strict.")

        days_ok = None if days_rolling_12_months is None else days_rolling_12_months <= _CEE_MAX_DAYS_ROLLING_12M
        average_ok = (
            None
            if average_weekly_hours_all_contracts_6m is None
            else average_weekly_hours_all_contracts_6m <= _CEE_MAX_AVERAGE_WEEKLY_HOURS_6M
        )

        is_minor = worker_age_years is not None and worker_age_years < 18
        daily_ok: Optional[bool] = None
        weekly_ok: Optional[bool] = None
        if is_minor:
            if planned_max_daily_hours is not None:
                daily_ok = planned_max_daily_hours <= _YOUNG_WORKER_MAX_DAILY_HOURS
            if planned_max_weekly_hours is not None:
                weekly_ok = planned_max_weekly_hours <= _YOUNG_WORKER_MAX_WEEKLY_HOURS

        return CEEContractGuardrailResult(
            days_rolling_12_months=days_rolling_12_months,
            days_limit_compliant=days_ok,
            average_weekly_hours_all_contracts_6m=average_weekly_hours_all_contracts_6m,
            average_hours_compliant=average_ok,
            worker_age_years=worker_age_years,
            planned_max_daily_hours=planned_max_daily_hours,
            planned_max_weekly_hours=planned_max_weekly_hours,
            minor_daily_hours_compliant=daily_ok,
            minor_weekly_hours_compliant=weekly_ok,
            require_average_hours_check=require_average_hours_check,
            require_minor_schedule_check=require_minor_schedule_check,
        )
