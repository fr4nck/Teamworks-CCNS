from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from uuid import UUID, uuid4

from domain.convention.classification import CCNSClassification
from domain.convention.part_time_minimum_increase import increase_rate_for_weekly_hours
from domain.convention.salary_grid_catalog import SalaryGridCatalog
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity
from domain.convention.salary_grid_version import SalaryGridVersion

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")
_ONE = Decimal("1.00")
_FULL_TIME_WEEKLY_HOURS = Decimal("35.00")


class SalaryMinimumComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"


def _strict_decimal(value: object, field_name: str) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être un Decimal strict.")
    return value


def _strict_date(value: object, field_name: str = "reference_date") -> date:
    if type(value) is not date:
        raise TypeError(f"{field_name} doit être une date stricte.")
    return value


def _quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class SalaryMinimumComplianceResult:
    classification_group: CCNSClassification
    reference_date: date
    remuneration_amount: Decimal
    remuneration_periodicity: SalaryMinimumPeriodicity
    full_time_minimum_amount: Decimal
    required_minimum_amount: Decimal
    difference_amount: Decimal
    weekly_hours: Decimal
    part_time_increase_rate: Decimal
    status: SalaryMinimumComplianceStatus
    salary_grid_version: SalaryGridVersion
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.classification_group) is not CCNSClassification:
            raise TypeError("classification_group doit être un CCNSClassification.")
        _strict_date(self.reference_date)
        if type(self.remuneration_periodicity) is not SalaryMinimumPeriodicity:
            raise TypeError("remuneration_periodicity doit être un SalaryMinimumPeriodicity.")
        if type(self.status) is not SalaryMinimumComplianceStatus:
            raise TypeError("status doit être un SalaryMinimumComplianceStatus.")
        if type(self.salary_grid_version) is not SalaryGridVersion:
            raise TypeError("salary_grid_version doit être un SalaryGridVersion.")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")

        remuneration = _strict_decimal(self.remuneration_amount, "remuneration_amount")
        full_time_minimum = _strict_decimal(self.full_time_minimum_amount, "full_time_minimum_amount")
        required_minimum = _strict_decimal(self.required_minimum_amount, "required_minimum_amount")
        difference = _strict_decimal(self.difference_amount, "difference_amount")
        weekly_hours = _strict_decimal(self.weekly_hours, "weekly_hours")
        increase_rate = _strict_decimal(self.part_time_increase_rate, "part_time_increase_rate")

        if remuneration < _ZERO:
            raise ValueError("Le montant de rémunération ne peut pas être négatif.")
        if full_time_minimum <= _ZERO or required_minimum <= _ZERO:
            raise ValueError("Les minima doivent être strictement supérieurs à zéro.")
        if weekly_hours <= _ZERO:
            raise ValueError("La durée hebdomadaire doit être strictement positive.")
        if increase_rate < _ZERO:
            raise ValueError("Le taux de majoration ne peut pas être négatif.")
        for amount in (remuneration, full_time_minimum, required_minimum, difference):
            if amount != _quantize_amount(amount):
                raise ValueError("Les montants doivent être quantifiés à deux décimales.")
        if difference != remuneration - required_minimum:
            raise ValueError("La différence doit être égale à la rémunération moins le minimum exigé.")
        expected_status = (
            SalaryMinimumComplianceStatus.COMPLIANT
            if difference >= _ZERO
            else SalaryMinimumComplianceStatus.NON_COMPLIANT
        )
        if self.status is not expected_status:
            raise ValueError("Le statut est incohérent avec la différence de rémunération.")

    def is_compliant(self) -> bool:
        return self.status is SalaryMinimumComplianceStatus.COMPLIANT

    def is_non_compliant(self) -> bool:
        return self.status is SalaryMinimumComplianceStatus.NON_COMPLIANT

    def has_shortfall(self) -> bool:
        return self.difference_amount < _ZERO

    def shortfall_amount(self) -> Decimal:
        return -self.difference_amount if self.has_shortfall() else _ZERO

    def has_surplus(self) -> bool:
        return self.difference_amount > _ZERO

    def surplus_amount(self) -> Decimal:
        return self.difference_amount if self.has_surplus() else _ZERO

    def is_exactly_at_minimum(self) -> bool:
        return self.difference_amount == _ZERO

    def uses_part_time_increase(self) -> bool:
        return self.part_time_increase_rate > _ZERO


@dataclass(frozen=True, slots=True)
class SalaryMinimumComplianceService:
    salary_grid_catalog: SalaryGridCatalog

    def __post_init__(self) -> None:
        if type(self.salary_grid_catalog) is not SalaryGridCatalog:
            raise TypeError("salary_grid_catalog doit être un SalaryGridCatalog.")

    def evaluate(
        self,
        classification_group: CCNSClassification,
        reference_date: date,
        remuneration_amount: Decimal,
        remuneration_periodicity: SalaryMinimumPeriodicity,
        weekly_hours: Decimal,
    ) -> SalaryMinimumComplianceResult:
        if type(classification_group) is not CCNSClassification:
            raise TypeError("classification_group doit être un CCNSClassification.")
        _strict_date(reference_date)
        remuneration = _strict_decimal(remuneration_amount, "remuneration_amount")
        weekly = _strict_decimal(weekly_hours, "weekly_hours")
        if remuneration < _ZERO:
            raise ValueError("Le montant de rémunération ne peut pas être négatif.")
        if weekly <= _ZERO:
            raise ValueError("La durée hebdomadaire doit être strictement positive.")
        if type(remuneration_periodicity) is not SalaryMinimumPeriodicity:
            raise TypeError("remuneration_periodicity doit être un SalaryMinimumPeriodicity.")

        version = self.salary_grid_catalog.version_applicable_on(reference_date)
        entry = version.entry_for_group(classification_group)
        if remuneration_periodicity is not entry.periodicity:
            raise ValueError("La périodicité de la rémunération ne correspond pas à celle du minimum CCNS.")

        full_time_minimum = entry.amount
        if entry.periodicity is SalaryMinimumPeriodicity.ANNUAL or weekly >= _FULL_TIME_WEEKLY_HOURS:
            required_minimum = full_time_minimum
            increase_rate = _ZERO
        else:
            increase_rate = increase_rate_for_weekly_hours(weekly)
            required_minimum = full_time_minimum * weekly / _FULL_TIME_WEEKLY_HOURS * (_ONE + increase_rate)

        required_minimum = _quantize_amount(required_minimum)
        remuneration = _quantize_amount(remuneration)
        difference = _quantize_amount(remuneration - required_minimum)
        status = (
            SalaryMinimumComplianceStatus.COMPLIANT
            if difference >= _ZERO
            else SalaryMinimumComplianceStatus.NON_COMPLIANT
        )
        return SalaryMinimumComplianceResult(
            classification_group=classification_group,
            reference_date=reference_date,
            remuneration_amount=remuneration,
            remuneration_periodicity=remuneration_periodicity,
            full_time_minimum_amount=full_time_minimum,
            required_minimum_amount=required_minimum,
            difference_amount=difference,
            weekly_hours=weekly,
            part_time_increase_rate=increase_rate,
            status=status,
            salary_grid_version=version,
        )
