from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum
from typing import Optional


CCNS_PART_TIME_ROUTE_SOURCE = "CCNS, article 5.1.5.2"
CCNS_PART_TIME_MINIMUM_SOURCE = "CCNS, article 5.1.5.2.1"
CCNS_PART_TIME_DEROGATION_STUDENT_SOURCE = "CCNS, article 5.1.5.2.2"
CCNS_PART_TIME_DEROGATION_EMPLOYEE_SOURCE = "CCNS, article 5.1.5.2.3"
CCNS_COMPLEMENTARY_HOURS_SOURCE = "CCNS, article 5.1.5 â€” Heures complÃ©mentaires"
CCNS_HOURS_AMENDMENT_SOURCE = "CCNS, article 5.1.5 â€” ComplÃ©ments d'heures par avenant"
CCNS_PART_TIME_MODULATION_SOURCE = "CCNS, article 5.2.4"
CODE_PART_TIME_FULL_TIME_THRESHOLD_SOURCE = "Code du travail, article L.3123-9"
CCNS_WEEKLY_MAXIMUM_SOURCE = "CCNS, article 5.1.3"

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




class PartTimePlannedWeekStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    COMPLEMENTARY_HOURS_LIMIT_EXCEEDED = "COMPLEMENTARY_HOURS_LIMIT_EXCEEDED"
    FULL_TIME_THRESHOLD_REACHED = "FULL_TIME_THRESHOLD_REACHED"
    ABSOLUTE_WEEKLY_MAXIMUM_EXCEEDED = "ABSOLUTE_WEEKLY_MAXIMUM_EXCEEDED"


@dataclass(frozen=True, slots=True)
class PartTimePlannedWeekResult:
    contractual_weekly_hours: Decimal
    planned_weekly_hours: Decimal
    status: PartTimePlannedWeekStatus
    compliant: bool
    recording_allowed: bool
    manual_override_used: bool
    manual_override_reason: str
    can_be_marked_compliant: bool
    source_references: tuple[str, ...]

    @property
    def requires_manual_override(self) -> bool:
        return not self.compliant

    @property
    def exceeds_or_reaches_full_time(self) -> bool:
        return self.planned_weekly_hours >= _LEGAL_WEEKLY_DURATION

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
    """RÃ¨gles CCNS de durÃ©e minimale et de dÃ©passement d'un temps partiel.

    Ce service ne dÃ©cide pas si un poste relÃ¨ve rÃ©ellement du CDI intermittent :
    cette qualification mÃ©tier doit Ãªtre fournie par la couche d'intÃ©gration.
    Il ne transforme pas non plus une simple case Ã  cocher en dÃ©rogation : les
    flags ``student_under_26_derogation`` et ``employee_requested_derogation``
    supposent que les justificatifs requis ont dÃ©jÃ  Ã©tÃ© validÃ©s.
    """

    def minimum_weekly_hours_for_days(
        self,
        days_per_worked_week: int,
        *,
        legal_minimum_for_six_days: Decimal = _SHORT_PART_TIME_LEGAL_REFERENCE,
    ) -> Decimal:
        if type(days_per_worked_week) is not int or isinstance(days_per_worked_week, bool):
            raise TypeError("days_per_worked_week doit Ãªtre un entier strict.")
        if not 1 <= days_per_worked_week <= 6:
            raise ValueError("days_per_worked_week doit Ãªtre compris entre 1 et 6.")
        if type(legal_minimum_for_six_days) is not Decimal:
            raise TypeError("legal_minimum_for_six_days doit Ãªtre un Decimal strict.")
        if legal_minimum_for_six_days <= _ZERO:
            raise ValueError("legal_minimum_for_six_days doit Ãªtre strictement positif.")
        if days_per_worked_week == 6:
            return legal_minimum_for_six_days
        return _MINIMUM_BY_DAYS[days_per_worked_week]

    def annual_cycle_minimum_hours(self, reference_fraction_of_year: Decimal = Decimal("1.00")) -> Decimal:
        if type(reference_fraction_of_year) is not Decimal:
            raise TypeError("reference_fraction_of_year doit Ãªtre un Decimal strict.")
        if not _ZERO < reference_fraction_of_year <= Decimal("1.00"):
            raise ValueError("reference_fraction_of_year doit Ãªtre > 0 et <= 1.")
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
            raise TypeError("contractual_weekly_hours doit Ãªtre un Decimal strict.")
        if not _ZERO < contractual_weekly_hours < _LEGAL_WEEKLY_DURATION:
            raise ValueError("contractual_weekly_hours doit Ãªtre > 0 et < 35 heures.")
        for name, value in (
            ("job_eligible_for_cdii", job_eligible_for_cdii),
            ("organization_allows_cdii", organization_allows_cdii),
            ("student_under_26_derogation", student_under_26_derogation),
            ("employee_requested_derogation", employee_requested_derogation),
        ):
            if type(value) is not bool:
                raise TypeError(f"{name} doit Ãªt²È="24€ÍÑ…ÑÕÌ€ôA…ÉÑQ¥µ•5¥¹¥µÕµMÑ…ÑÕÌ¹	1=]}5%9%5U4(€€€€€€€€€€€•™™•Ñ¥Ù•}µ¥¹¥µÕ´€ôµ¥¹¥µÕ´(€€€€€€€•±Í”è(€€€€€€€€€€€ÍÑ…ÑÕÌ€ôA…ÉÑQ¥µ•5¥¹¥µÕµMÑ…ÑÕÌ¹=5A1%9P(€€€€€€€€€€€•™™•Ñ¥Ù•}µ¥¹¥µÕ´€ôµ¥¹¥µÕ´((€€€€€€€É•ÑÕÉ¸A…ÉÑQ¥µ•5¥¹¥µÕµI•ÍÕ±Ð (€€€€€€€€€€€½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌõ½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ°(€€€€€€€€€€€‘…åÍ}Á•É}Ý½É­•‘}Ý••¬õ‘…åÍ}Á•É}Ý½É­•‘}Ý••¬°(€€€€€€€€€€€µ¥¹¥µÕµ}Ý••­±å}¡½ÕÉÌõ•™™•Ñ¥Ù•}µ¥¹¥µÕ´°(€€€€€€€€€€€ÍÑ…ÑÕÌõÍÑ…ÑÕÌ°(€€€€€€€€€€€ÍÑÕ‘•¹Ñ}Õ¹‘•É|ÈÙ}‘•É½…Ñ¥½¸õÍÑÕ‘•¹Ñ}Õ¹‘•É|ÈÙ}‘•É½…Ñ¥½¸°(€€€€€€€€€€€•µÁ±½å••}É•ÅÕ•ÍÑ•‘}‘•É½…Ñ¥½¸õ•µÁ±½å••}É•ÅÕ•ÍÑ•‘}‘•É½…Ñ¥½¸°(€€€€€€€€€€€Í¡½ÉÑ}Á…ÉÑ}Ñ¥µ•}¹Í}É½ÕÑ•}…±±½Ý•õÍ¡½ÉÑ}É½ÕÑ•}…±±½Ý•°(€€€€€€€€€€€‘•É½…Ñ¥½¹}Í½ÕÉ•}É•™•É•¹”ô (€€€€€€€€€€€€€€€9M}AIQ}Q%5}I=Q%=9}MQU9Q}M=UI(€€€€€€€€€€€€€€€¥˜ÍÑÕ‘•¹Ñ}Õ¹‘•É|ÈÙ}‘•É½…Ñ¥½¸(€€€€€€€€€€€€€€€•±Í”9M}AIQ}Q%5}I=Q%=9}5A1=e}M=UI(€€€€€€€€€€€€€€€¥˜•µÁ±½å••}É•ÅÕ•ÍÑ•‘}‘•É½…Ñ¥½¸(€€€€€€€€€€€€€€€•±Í”9½¹”(€€€€€€€€€€€€¤°(€€€€€€€€¤((€€€‘•˜•Ù…±Õ…Ñ•}½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ (€€€€€€€Í•±˜°(€€€€€€€€¨°(€€€€€€€½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌè•¥µ…°°(€€€€€€€½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌè•¥µ…°°(€€€€¤€´ø½µÁ±•µ•¹Ñ…Éå!½ÕÉÍI•ÍÕ±Ðè(€€€€€€€¥˜ÑåÁ”¡½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ¤¥Ì¹½Ð•¥µ…°è(€€€€€€€€€€€É…¥Í”QåÁ•ÉÉ½È ‰½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ‘½¥Ðƒ©ÑÉ”Õ¸•¥µ…°ÍÑÉ¥Ð¸ˆ¤(€€€€€€€¥˜ÑåÁ”¡½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ¤¥Ì¹½Ð•¥µ…°è(€€€€€€€€€€€É…¥Í”QåÁ•ÉÉ½È ‰½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ‘½¥Ðƒ©ÑÉ”Õ¸•¥µ…°ÍÑÉ¥Ð¸ˆ¤(€€€€€€€¥˜¹½Ð}iI<€ð½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ€ð}11}]-1e}UIQ%=8è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ‘½¥Ðƒ©ÑÉ”€ø€À•Ð€ð€ÌÔ¡•ÕÉ•Ì¸ˆ¤(€€€€€€€¥˜½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ€ð}iI<è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ¹”Á•ÕÐÁ…Ìƒ©ÑÉ”»¥…Ñ¥˜¸ˆ¤((€€€€€€€Ý¥Ñ ±½…±½¹Ñ•áÐ ¤…ÌÑàè(€€€€€€€€€€€Ñà¹ÁÉ•Œ€ô€Èà(€€€€€€€€€€€½¹•}Ñ¡¥É‘}±¥µ¥Ð€ô½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ€¼•¥µ…° ˆÌˆ¤(€€€€€€€€€€€É•ÍÕ±Ñ¥¹œ€ô½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ€¬½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ(€€€€€€€€€€€µ…¹‘…Ñ½Éå}±¥µ¥Ð€ô½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ€¨}59Q=Ie}=5A159QIe}IQ%=8((€€€€€€€Ý¥Ñ¡¥¹}½¹•}Ñ¡¥É€ô½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ€ðô½¹•}Ñ¡¥É‘}±¥µ¥Ð(€€€€€€€‰•±½Ý}±•…°€ôÉ•ÍÕ±Ñ¥¹œ€ð}11}]-1e}UIQ%=8(€€€€€€€É•ÑÕÉ¸½µÁ±•µ•¹Ñ…Éå!½ÕÉÍI•ÍÕ±Ð (€€€€€€€€€€€½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌõ½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ°(€€€€€€€€€€€½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌõ½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ°(€€€€€€€€€€€É•ÍÕ±Ñ¥¹}Ý••­±å}¡½ÕÉÌõÉ•ÍÕ±Ñ¥¹œ°(€€€€€€€€€€€½¹•}Ñ¡¥É‘}±¥µ¥Ñ}¡½ÕÉÌõ½¹•}Ñ¡¥É‘}±¥µ¥Ð°(€€€€€€€€€€€Ý¥Ñ¡¥¹}½¹•}Ñ¡¥É‘}±¥µ¥ÐõÝ¥Ñ¡¥¹}½¹•}Ñ¡¥É°(€€€€€€€€€€€‰•±½Ý}±•…±}‘ÕÉ…Ñ¥½¸õ‰•±½Ý}±•…°°(€€€€€€€€€€€½µÁ±¥…¹ÐõÝ¥Ñ¡¥¹}½¹•}Ñ¡¥É…¹‰•±½Ý}±•…°°(€€€€€€€€€€€•µÁ±½å••}µÕÍÑ}Á•É™½É´õ½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ€ðôµ…¹‘…Ñ½Éå}±¥µ¥Ð°(€€€€€€€€¤(((€€€‘•˜•Ù…±Õ…Ñ•}Á±…¹¹•‘}Ý••¬ (€€€€€€€Í•±˜°(€€€€€€€€¨°(€€€€€€€½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌè•¥µ…°°(€€€€€€€Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌè•¥µ…°°(€€€€€€€µ…¹Õ…±}½Ù•ÉÉ¥‘•}É•…Í½¸èÍÑÈ€ô€ˆˆ°(€€€€¤€´øA…ÉÑQ¥µ•A±…¹¹•‘]••­I•ÍÕ±Ðè(€€€€€€€€ˆˆ‰½¹ÑËÑ±”Õ¹”Í•µ…¥¹”Á±…¹¥™§¥”Í…¹Ì•µÃ©¡•È‘”Í…¥Í¥È±„Ë¥…±¥Ó¤¸((€€€€€€€U¹”¹½¸µ½¹™½Éµ¥Ó¤Á•ÕÐƒ©ÑÉ”•¹É•¥ÍÑË¥”±½ÉÍÅÕ”°ÕÑ¥±¥Í…Ñ•ÕÈ™½ÕÉ¹¥ÐÕ¸(€€€€€€€µ½Ñ¥˜•áÁ±¥¥Ñ”¸•Ð…ÅÕ¥ÑÑ•µ•¹Ð¹”É•¹©…µ…¥Ì±„Í•µ…¥¹”½¹™½Éµ”€è¥°(€€€€€€€Á•Éµ•ÐÍ•Õ±•µ•¹Ð‘”½¹Í•ÉÙ•ÈÕ¸Á±…¹¹¥¹œË¥•°½ÔÕ¹”¡åÁ½Ñ£¡Í”‘”ÑÉ…Ù…¥°¸(€€€€€€€€ˆˆˆ(€€€€€€€¥˜ÑåÁ”¡½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ¤¥Ì¹½Ð•¥µ…°è(€€€€€€€€€€€É…¥Í”QåÁ•ÉÉ½È ‰½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ‘½¥Ðƒ©ÑÉ”Õ¸•¥µ…°ÍÑÉ¥Ð¸ˆ¤(€€€€€€€¥˜ÑåÁ”¡Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌ¤¥Ì¹½Ð•¥µ…°è(€€€€€€€€€€€É…¥Í”QåÁ•ÉÉ½È ‰Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌ‘½¥Ðƒ©ÑÉ”Õ¸•¥µ…°ÍÑÉ¥Ð¸ˆ¤(€€€€€€€¥˜ÑåÁ”¡µ…¹Õ…±}½Ù•ÉÉ¥‘•}É•…Í½¸¤¥Ì¹½ÐÍÑÈè(€€€€€€€€€€€É…¥Í”QåÁ•ÉÉ½È ‰µ…¹Õ…±}½Ù•ÉÉ¥‘•}É•…Í½¸‘½¥Ðƒ©ÑÉ”Õ¹”¡‡¹¹”¸ˆ¤(€€€€€€€¥˜¹½Ð}iI<€ð½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ€ð}11}]-1e}UIQ%=8è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ‘½¥Ðƒ©ÑÉ”€ø€À•Ð€ð€ÌÔ¡•ÕÉ•Ì¸ˆ¤(€€€€€€€¥˜Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌ€ðô}iI<è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌ‘½¥Ðƒ©ÑÉ”ÍÑÉ¥Ñ•µ•¹ÐÁ½Í¥Ñ¥˜¸ˆ¤((€€€€€€€É•…Í½¸€ôµ…¹Õ…±}½Ù•ÉÉ¥‘•}É•…Í½¸¹ÍÑÉ¥À ¤(€€€€€€€Í½ÕÉ•ÌèÑÕÁ±•mÍÑÈ°€¸¸¹t(€€€€€€€¥˜Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌ€ø•¥µ…° ˆÐà¸ÀÀˆ¤è(€€€€€€€€€€€ÍÑ…ÑÕÌ€ôA…ÉÑQ¥µ•A±…¹¹•‘]••­MÑ…ÑÕÌ¹	M=1UQ}]-1e}5a%5U5}a(€€€€€€€€€€€Í½ÕÉ•Ì€ô€¡9M}]-1e}5a%5U5}M=UI°9M}AIQ}Q%5}5=U1Q%=9}M=UI¤(€€€€€€€•±¥˜Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌ€øô}11}]-1e}UIQ%=8è(€€€€€€€€€€€ÍÑ…ÑÕÌ€ôA…ÉÑQ¥µ•A±…¹¹•‘]••­MÑ…ÑÕÌ¹U11}Q%5}Q!IM!=1}I!(€€€€€€€€€€€Í½ÕÉ•Ì€ô€¡9M}AIQ}Q%5}5=U1Q%=9}M=UI°=}AIQ}Q%5}U11}Q%5}Q!IM!=1}M=UI¤(€€€€€€€•±¥˜Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌ€ø½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌè(€€€€€€€€€€€½µÁ±•µ•¹Ñ…Éä€ôÍ•±˜¹•Ù…±Õ…Ñ•}½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌ (€€€€€€€€€€€€€€€½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌõ½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ°(€€€€€€€€€€€€€€€½µÁ±•µ•¹Ñ…Éå}¡½ÕÉÌõÁ±…¹¹•‘}Ý••­±å}¡½ÕÉÌ€´½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ°(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜½µÁ±•µ•¹Ñ…Éä¹½µÁ±¥…¹Ðè(€€€€€€€€€€€€€€€ÍÑ…ÑÕÌ€ôA…ÉÑQ¥µ•A±…¹¹•‘]••­MÑ…ÑÕÌ¹=5A1%9P(€€€€€€€€€€€€€€€Í½ÕÉ•Ì€ô€¡9M}=5A159QIe}!=UIM}M=UI°¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€ÍÑ…ÑÕÌ€ôA…ÉÑQ¥µ•A±…¹¹•‘]••­MÑ…ÑÕÌ¹=5A159QIe}!=UIM}1%5%Q}a(€€€€€€€€€€€€€€€Í½ÕÉ•Ì€ô€¡9M}=5A159QIe}!=UIM}M=UI°¤(€€€€€€€•±Í”è(€€€€€€€€€€€ÍÑ…ÑÕÌ€ôA…ÉÑQ¥µ•A±…¹¹•‘]••­MÑ…ÑÕÌ¹=5A1%9P(€€€€€€€€€€€Í½ÕÉ•Ì€ô€¡9M}AIQ}Q%5}5=U1Q%=9}M=UI°¤((€€€€€€€½µÁ±¥…¹Ð€ôÍÑ…ÑÕÌ¥ÌA…ÉÑQ¥µ•A±…¹¹•‘]••­MÑ…ÑÕÌ¹=5A1%9P(€€€€€€€½Ù•ÉÉ¥‘•}ÕÍ•€ô€¡¹½Ð½µÁ±¥…¹Ð¤…¹‰½½°¡É•…Í½¸¤(€€€€€€€É•ÑÕÉ¸A…ÉÑQ¥µ•A±…¹¹•‘]••­I•ÍÕ±Ð (€€€€€€€€€€€½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌõ½¹ÑÉ…ÑÕ…±}Ý••­±å}¡½ÕÉÌ°(€€€€€€€€€€€Á±…¹¹•‘}Ý••­±å}¡½ÕÉÌõÁ±…¹¹•‘}Ý••­±å}¡½ÕÉÌ°(€€€€€€€€€€€ÍÑ…ÑÕÌõÍÑ…ÑÕÌ°(€€€€€€€€€€€½µÁ±¥…¹Ðõ½µÁ±¥…¹Ð°(€€€€€€€€€€€É•½É‘¥¹}…±±½Ý•õ½µÁ±¥…¹Ð½È½Ù•ÉÉ¥‘•}ÕÍ•°(€€€€€€€€€€€µ…¹Õ…±}½Ù•ÉÉ¥‘•}ÕÍ•õ½Ù•ÉÉ¥‘•}ÕÍ•°(€€€€€€€€€€€µ…¹Õ…±}½Ù•ÉÉ¥‘•}É•…Í½¸õÉ•…Í½¸°(€€€€€€€€€€€…¹}‰•}µ…É­•‘}½µÁ±¥…¹Ðõ½µÁ±¥…¹Ð°(€€€€€€€€€€€Í½ÕÉ•}É•™•É•¹•ÌõÍ½ÕÉ•Ì°(€€€€€€€€¤((€€€‘•˜•Ù…±Õ…Ñ•}¡½ÕÉÍ}…µ•¹‘µ•¹Ñ}…Á…¥Ñä (€€€€€€€Í•±˜°(€€€€€€€€¨°(€€€€€€€…µ•¹‘µ•¹ÑÍ}ÕÍ•‘}‰•™½É”è¥¹Ð°(€€€€€€€Ý••­Í}ÕÍ•‘}‰•™½É”è¥¹Ð°(€€€€€€€Á±…¹¹•‘}Ý••­Ìè¥¹Ð°(€€€€€€€É•Á±…•µ•¹Ñ}…Ñ}±•…ÍÑ}½¹•}µ½¹Ñ è‰½½°€ô…±Í”°(€€€€¤€´ø!½ÕÉÍµ•¹‘µ•¹Ñ…Á…¥ÑåI•ÍÕ±Ðè(€€€€€€€™½È¹…µ”°Ù…±Õ”¥¸€ (€€€€€€€€€€€€ ‰…µ•¹‘µ•¹ÑÍ}ÕÍ•‘}‰•™½É”ˆ°…µ•¹‘µ•¹ÑÍ}ÕÍ•‘}‰•™½É”¤°(€€€€€€€€€€€€ ‰Ý••­Í}ÕÍ•‘}‰•™½É”ˆ°Ý••­Í}ÕÍ•‘}‰•™½É”¤°(€€€€€€€€€€€€ ‰Á±…¹¹•‘}Ý••­Ìˆ°Á±…¹¹•‘}Ý••­Ì¤°(€€€€€€€€¤è(€€€€€€€€€€€¥˜ÑåÁ”¡Ù…±Õ”¤¥Ì¹½Ð¥¹Ð½È¥Í¥¹ÍÑ…¹”¡Ù…±Õ”°‰½½°¤è(€€€€€€€€€€€€€€€É…¥Í”QåÁ•ÉÉ½È¡˜‰í¹…µ•ô‘½¥Ðƒ©ÑÉ”Õ¸•¹Ñ¥•ÈÍÑÉ¥Ð¸ˆ¤(€€€€€€€€€€€¥˜Ù…±Õ”€ð€Àè(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È¡˜‰í¹…µ•ô¹”Á•ÕÐÁ…Ìƒ©ÑÉ”»¥…Ñ¥˜¸ˆ¤(€€€€€€€¥˜ÑåÁ”¡É•Á±…•µ•¹Ñ}…Ñ}±•…ÍÑ}½¹•}µ½¹Ñ ¤¥Ì¹½Ð‰½½°è(€€€€€€€€€€€É…¥Í”QåÁ•ÉÉ½È ‰É•Á±…•µ•¹Ñ}…Ñ}±•…ÍÑ}½¹•}µ½¹Ñ ‘½¥Ðƒ©ÑÉ”Õ¸‰½½³¥•¸ÍÑÉ¥Ð¸ˆ¤(€€€€€€€¥˜Á±…¹¹•‘}Ý••­Ì€ôô€Àè(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Á±…¹¹•‘}Ý••­Ì‘½¥Ðƒ©ÑÉ”ÍÑÉ¥Ñ•µ•¹ÐÁ½Í¥Ñ¥˜¸ˆ¤((€€€€€€€…µ•¹‘µ•¹Ñ}¹Õµ‰•É}…™Ñ•È€ô…µ•¹‘µ•¹ÑÍ}ÕÍ•‘}‰•™½É”€¬€Ä(€€€€€€€½Õ¹Ñ•‘}Ý••­Í}…™Ñ•È€ôÝ••­Í}ÕÍ•‘}‰•™½É”€¬€ À¥˜É•Á±…•µ•¹Ñ}…Ñ}±•…ÍÑ}½¹•}µ½¹Ñ •±Í”Á±…¹¹•‘}Ý••­Ì¤(€€€€€€€…µ•¹‘µ•¹Ñ}½¬€ô…µ•¹‘µ•¹Ñ}¹Õµ‰•É}…™Ñ•È€ðô€à(€€€€€€€Ý••­Í}½¬€ô½Õ¹Ñ•‘}Ý••­Í}…™Ñ•È€ðô€ä(€€€€€€€É•ÑÕÉ¸!½ÕÉÍµ•¹‘µ•¹Ñ…Á…¥ÑåI•ÍÕ±Ð (€€€€€€€€€€€…µ•¹‘µ•¹ÑÍ}ÕÍ•‘}‰•™½É”õ…µ•¹‘µ•¹ÑÍ}ÕÍ•‘}‰•™½É”°(€€€€€€€€€€€Ý••­Í}ÕÍ•‘}‰•™½É”õÝ••­Í}ÕÍ•‘}‰•™½É”°(€€€€€€€€€€€Á±…¹¹•‘}Ý••­ÌõÁ±…¹¹•‘}Ý••­Ì°(€€€€€€€€€€€É•Á±…•µ•¹Ñ}…Ñ}±•…ÍÑ}½¹•}µ½¹Ñ õÉ•Á±…•µ•¹Ñ}…Ñ}±•…ÍÑ}½¹•}µ½¹Ñ °(€€€€€€€€€€€…µ•¹‘µ•¹Ñ}¹Õµ‰•É}…™Ñ•Èõ…µ•¹‘µ•¹Ñ}¹Õµ‰•É}…™Ñ•È°(€€€€€€€€€€€½Õ¹Ñ•‘}Ý••­Í}…™Ñ•Èõ½Õ¹Ñ•‘}Ý••­Í}…™Ñ•È°(€€€€€€€€€€€…µ•¹‘µ•¹Ñ}½Õ¹Ñ}½µÁ±¥…¹Ðõ…µ•¹‘µ•¹Ñ}½¬°(€€€€€€€€€€€Ý••­Í}½Õ¹Ñ}½µÁ±¥…¹ÐõÝ••­Í}½¬°(€€€€€€€€€€€½µÁ±¥…¹Ðõ…µ•¹‘µ•¹Ñ}½¬…¹Ý••­Í}½¬°(€€€€€€€€¤(