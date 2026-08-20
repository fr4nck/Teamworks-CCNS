from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext


_ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class VacationWeekCapImpact:
    total_vacation_weeks: int
    paid_leave_weeks_in_vacations: int
    worked_vacation_weeks: int
    current_vacation_week_hours: Decimal
    capped_vacation_week_hours: Decimal
    current_vacation_hours: Decimal
    capped_vacation_hours: Decimal
    annual_hours_lost: Decimal
    school_weeks: int
    equivalent_hours_per_school_week: Decimal


class WorkingTimeScenarioService:
    """Comparaisons arithmétiques de scénarios, sans qualifier leur légalité.

    Les scénarios permettent de mesurer l'impact RH d'une contrainte avant de
    choisir le régime contractuel approprié. La conformité juridique reste du
    ressort des moteurs CCNS dédiés.
    """

    def vacation_week_cap_impact(
        self,
        *,
        total_vacation_weeks: int,
        paid_leave_weeks_in_vacations: int,
        current_vacation_week_hours: Decimal,
        capped_vacation_week_hours: Decimal,
        school_weeks: int,
    ) -> VacationWeekCapImpact:
        for name, value in (
            ("total_vacation_weeks", total_vacation_weeks),
            ("paid_leave_weeks_in_vacations", paid_leave_weeks_in_vacations),
            ("school_weeks", school_weeks),
        ):
            if type(value) is not int or isinstance(value, bool):
                raise TypeError(f"{name} doit être un entier strict.")
            if value < 0:
                raise ValueError(f"{name} ne peut pas être négatif.")
        if paid_leave_weeks_in_vacations > total_vacation_weeks:
            raise ValueError("Les congés pris pendant les vacances ne peuvent pas dépasser les semaines de vacances.")
        if school_weeks <= 0:
            raise ValueError("school_weeks doit être strictement positif.")
        for name, value in (
            ("current_vacation_week_hours", current_vacation_week_hours),
            ("capped_vacation_week_hours", capped_vacation_week_hours),
        ):
            if type(value) is not Decimal:
                raise TypeError(f"{name} doit être un Decimal strict.")
            if value < _ZERO:
                raise ValueError(f"{name} ne peut pas être négatif.")

        worked_weeks = total_vacation_weeks - paid_leave_weeks_in_vacations
        with localcontext() as ctx:
            ctx.prec = 28
            worked = Decimal(worked_weeks)
            current_total = current_vacation_week_hours * worked
            capped_total = capped_vacation_week_hours * worked
            lost = max(_ZERO, current_total - capped_total)
            per_school_week = lost / Decimal(school_weeks)
        return VacationWeekCapImpact(
            total_vacation_weeks=total_vacation_weeks,
            paid_leave_weeks_in_vacations=paid_leave_weeks_in_vacations,
            worked_vacation_weeks=worked_weeks,
            current_vacation_week_hours=current_vacation_week_hours,
            capped_vacation_week_hours=capped_vacation_week_hours,
            current_vacation_hours=current_total,
            capped_vacation_hours=capped_total,
            annual_hours_lost=lost,
            school_weeks=school_weeks,
            equivalent_hours_per_school_week=per_school_week,
        )
