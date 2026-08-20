from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum
from typing import Optional


CCNS_PART_TIME_ROUTE_SOURCE = "CCNS, article 5.1.5.2"
CCNS_PART_TIME_MINIMUM_SOURCE = "CCNS, article 5.1.5.2.1"
CCNS_PART_TIME_DEROGATION_STUDENT_SOURCE = "CCNS, article 5.1.5.2.2"
CCNS_PART_TIME_DEROGATION_EMPLOYEE_SOURCE = "CCNS, article 5.1.5.2.3"
CCNS_COMPLEMENTARY_HOURS_SOURCE = "CCNS, article 5.1.5 — Heures complémentaires"
CCNS_HOURS_AMENDMENT_SOURCE = "CCNS, article 5.1.5 — Compléments d'heures par avenant"

_ZERO = Decimal("0.00")
_LEGAL_WEEKLY_DURATION = Decimal("35.00")
_SHORT_PART_TIME_LEGAL_REFERENCE = Decimal("24.00")
_COMPLEMENTARY_LIMIT_FRACTION = Decimal("0.3333333333333333333333333333")
_MANDATORY_COMPLEMENTARY_FRACTION = Decimal("0.10")
_COMPLEMENTARY_INCREASE_RATE = Decimal("0.10")
_AFTER_AMENDMENT_INCREASE_RATE = Decimal("0.25")
_ANNUAL_CYCLE_MINIMUM_HOURS = Decimal("304.00")

_MINIMUM_BY_DAYS = {
    1: Decimal("2.00"),
    2: Decimal("3.00"),
    3: Decimal("5.00"),
    4: Decimal("8.00"),
    5: Decimal("10.00"),
}


class PartTimeMinimumStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    BELOW_MINIMUM = "BELOW_MINIMUM"
    DEROGATION_APPLIES = "DEROGATION_APPLIES"


@dataclass(frozen=True, slots=True)
class PartTimeMinimumResult:
    contractual_weekly_hours: Decimal
    days_per_worked_week: int
    minimum_weekly_hours: Optional[Decimal]
    status: PartTimeMinimumStatus
    student_under_26_derogation: bool
    employee_requested_derogation: bool
    short_part_time_ccns_route_allowed: bool
    derogation_source_reference: Optional[str]
    source_reference: str = CCNS_PART_TIME_MINIMUM_SOURCE
    route_source_reference: str = CCNS_PART_TIME_ROUTE_SOURCE

    @property
    def minimum_compliant(self) -> bool:
        return self.status in {
            PartTimeMinimumStatus.COMPLIANT,
            PartTimeMinimumStatus.DEROGATION_APPLIES,
        }

    @property
    def requires_non_cdii_route_justification(self) -> bool:
        return (
            self.contractual_weekly_hours < _SHORT_PART_TIME_LEGAL_REFERENCE
            and not self.short_part_time_ccns_route_allowed
        )

    @property
    def compliant(self) -> bool:
        return self.minimum_compliant and not self.requires_non_cdii_route_justification


@dataclass(frozen=True, slots=True)
class ComplementaryHoursResult:
    contractual_weekly_hours: Decimal
    complementary_hours: Decimal
    resulting_weekly_hours: Decimal
    one_third_limit_hours: Decimal
    within_one_third_limit: bool
    below_legal_duration: bool
    compliant: bool
    employee_must_perform: bool
    increase_rate: Decimal = _COMPLEMENTARY_INCREASE_RATE
    source_reference: str = CCNS_COMPLEMENTARY_HOURS_SOURCE


@dataclass(frozen=True, slots=True)
class HoursAmendmentCapacityResult:
    amendments_used_before: int
    weeks_used_before: int
    planned_weeks: int
    replacement_at_least_one_month: bool
    amendment_number_after: int
    counted_weeks_after: int
    amendment_count_compliant: bool
    weeks_count_compliant: bool
    compliant: bool
    overtime_beyond_amendment_increase_rate: Decimal = _AFTER_AMENDMENT_INCREASE_RATE
    source_reference: str = CCNS_HOURS_AMENDMENT_SOURCE


class CCNSPartTimeWorkingTimeService:
    """Règles CCNS de durée minimale et de dépassement d'un temps partiel.

    Ce service ne décide pas si un poste relève réellement du CDI intermittent :
    cette qualification métier doit être fournie par la couche d'intégration.
    Il ne transforme pas non plus une simple case à cocher en dérogation : les
    flags ``student_under_26_derogation`` et ``employee_requested_derogation``
    supposent que les justificatifs requis ont déjà été validés.
    """

    def minimum_weekly_hours_for_days(
        self,
        days_per_worked_week: int,
        *,
        legal_minimum_for_six_days: Decimal = _SHORT_PART_TIME_LEGAL_REFERENCE,
    ) -> Decimal:
        if type(days_per_worked_week) is not int or isinstance(days_per_worked_week, bool):
            raise TypeError("days_per_worked_week doit être un entier strict.")
        if not 1 <= days_per_worked_week <= 6:
            raise ValueError("days_per_worked_week doit être compris entre 1 et 6.")
        if type(legal_minimum_for_six_days) is not Decimal:
            raise TypeError("legal_minimum_for_six_days doit être un Decimal strict.")
        if legal_minimum_for_six_days <= _ZERO:
            raise ValueError("legal_minimum_for_six_days doit être strictement positif.")
        if days_per_worked_week == 6:
            return legal_minimum_for_six_days
        return _MINIMUM_BY_DAYS[days_per_worked_week]

    def annual_cycle_minimum_hours(self, reference_fraction_of_year: Decimal = Decimal("1.00")) -> Decimal:
        if type(reference_fraction_of_year) is not Decimal:
            raise TypeError("reference_fraction_of_year doit être un Decimal strict.")
        if not _ZERO < reference_fraction_of_year <= Decimal("1.00"):
            raise ValueError("reference_fraction_of_year doit être > 0 et <= 1.")
        with localcontext() as ctx:
            ctx.prec = 28
            return _ANNUAL_CYCLE_MINIMUM_HOURS * reference_fraction_of_year

    def evaluate_minimum(
        self,
        *,
        contractual_weekly_hours: Decimal,
        days_per_worked_week: int,
        job_eligible_for_cdii: bool,
        organization_allows_cdii: bool,
        student_under_26_derogation: bool = False,
        employee_requested_derogation: bool = False,
        legal_minimum_for_six_days: Decimal = _SHORT_PART_TIME_LEGAL_REFERENCE,
    ) -> PartTimeMinimumResult:
        if type(contractual_weekly_hours) is not Decimal:
            raise TypeError("contractual_weekly_hours doit être un Decimal strict.")
        if not _ZERO < contractual_weekly_hours < _LEGAL_WEEKLY_DURATION:
            raise ValueError("contractual_weekly_hours doit être > 0 et < 35 heures.")
        for name, value in (
            ("job_eligible_for_cdii", job_eligible_for_cdii),
            ("organization_allows_cdii", organization_allows_cdii),
            ("student_under_26_derogation", student_under_26_derogation),
            ("employee_requested_derogation", employee_requested_derogation),
        ):
            if type(value) is not bool:
                raise TypeError(f"{name} doit être un booléen strict.")

        minimum = self.minimum_weekly_hours_for_days(
            days_per_worked_week,
            legal_minimum_for_six_days=legal_minimum_for_six_days,
        )
        short_route_allowed = not (job_eligible_for_cdii and organization_allows_cdii)

        if student_under_26_derogation or employee_requested_derogation:
            status = PartTimeMinimumStatus.DEROGATION_APPLIES
            effective_minimum = None
        elif contractual_weekly_hours < minimum:
            status = PartTimeMinimumStatus.BELOW_MINIMUM
            effective_minimum = minimum
        else:
            status = PartTimeMinimumStatus.COMPLIANT
            effective_minimum = minimum

        return PartTimeMinimumResult(
            contractual_weekly_hours=contractual_weekly_hours,
            days_per_worked_week=days_per_worked_week,
            minimum_weekly_hours=effective_minimum,
            status=status,
            student_under_26_derogation=student_under_26_derogation,
            employee_requested_derogation=employee_requested_derogation,
            short_part_time_ccns_route_allowed=short_route_allowed,
            derogation_source_reference=(
                CCNS_PART_TIME_DEROGATION_STUDENT_SOURCE
                if student_under_26_derogation
                else CCNS_PART_TIME_DEROGATION_EMPLOYEE_SOURCE
                if employee_requested_derogation
                else None
            ),
        )

    def evaluate_complementary_hours(
        self,
        *,
        contractual_weekly_hours: Decimal,
        complementary_hours: Decimal,
    ) -> ComplementaryHoursResult:
        if type(contractual_weekly_hours) is not Decimal:
            raise TypeError("contractual_weekly_hours doit être un Decimal strict.")
        if type(complementary_hours) is not Decimal:
            raise TypeError("complementary_hours doit être un Decimal strict.")
        if not _ZERO < contractual_weekly_hours < _LEGAL_WEEKLY_DURATION:
            raise ValueError("contractual_weekly_hours doit être > 0 et < 35 heures.")
        if complementary_hours < _ZERO:
            raise ValueError("complementary_hours ne peut pas être négatif.")

        with localcontext() as ctx:
            ctx.prec = 28
            one_third_limit = contractual_weekly_hours / Decimal("3")
            resulting = contractual_weekly_hours + complementary_hours
            mandatory_limit = contractual_weekly_hours * _MANDATORY_COMPLEMENTARY_FRACTION

        within_one_third = complementary_hours <= one_third_limit
        below_legal = resulting < _LEGAL_WEEKLY_DURATION
        return ComplementaryHoursResult(
            contractual_weekly_hours=contractual_weekly_hours,
            complementary_hours=complementary_hours,
            resulting_weekly_hours=resulting,
            one_third_limit_hours=one_third_limit,
            within_one_third_limit=within_one_third,
            below_legal_duration=below_legal,
            compliant=within_one_third and below_legal,
            employee_must_perform=complementary_hours <= mandatory_limit,
        )

    def evaluate_hours_amendment_capacity(
        self,
        *,
        amendments_used_before: int,
        weeks_used_before: int,
        planned_weeks: int,
        replacement_at_least_one_month: bool = False,
    ) -> HoursAmendmentCapacityResult:
        for name, value in (
            ("amendments_used_before", amendments_used_before),
            ("weeks_used_before", weeks_used_before),
            ("planned_weeks", planned_weeks),
        ):
            if type(value) is not int or isinstance(value, bool):
                raise TypeError(f"{name} doit être un entier strict.")
            if value < 0:
                raise ValueError(f"{name} ne peut pas être négatif.")
        if type(replacement_at_least_one_month) is not bool:
            raise TypeError("replacement_at_least_one_month doit être un booléen strict.")
        if planned_weeks == 0:
            raise ValueError("planned_weeks doit être strictement positif.")

        amendment_number_after = amendments_used_before + 1
        counted_weeks_after = weeks_used_before + (0 if replacement_at_least_one_month else planned_weeks)
        amendment_ok = amendment_number_after <= 8
        weeks_ok = counted_weeks_after <= 9
        return HoursAmendmentCapacityResult(
            amendments_used_before=amendments_used_before,
            weeks_used_before=weeks_used_before,
            planned_weeks=planned_weeks,
            replacement_at_least_one_month=replacement_at_least_one_month,
            amendment_number_after=amendment_number_after,
            counted_weeks_after=counted_weeks_after,
            amendment_count_compliant=amendment_ok,
            weeks_count_compliant=weeks_ok,
            compliant=amendment_ok and weeks_ok,
        )
