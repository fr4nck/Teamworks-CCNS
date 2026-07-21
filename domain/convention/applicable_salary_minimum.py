from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from uuid import UUID, uuid4

from domain.convention.classification import CCNSClassification
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity
from domain.convention.salary_minimum_compliance import (
    SalaryMinimumComplianceResult,
    SalaryMinimumComplianceService,
)
from domain.convention.smic import SmicCatalog, SmicTerritory, SmicVersion

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")
_FULL_TIME_WEEKLY_HOURS = Decimal("35.00")
_ANNUAL_MINIMUM_MESSAGE = "Le contrôle du minimum le plus favorable est limité aux minima CCNS mensuels."


class ApplicableSalaryMinimumSource(str, Enum):
    CCNS = "ccns"
    SMIC = "smic"
    EQUAL = "equal"


class ApplicableSalaryMinimumStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"


def _strict_date(value: object, field_name: str = "reference_date") -> date:
    if type(value) is not date:
        raise TypeError(f"{field_name} doit être une date stricte.")
    return value


def _strict_decimal(value: object, field_name: str) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être un Decimal strict.")
    return value


def _quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def _source_for(ccns_minimum: Decimal, smic_minimum: Decimal) -> ApplicableSalaryMinimumSource:
    if ccns_minimum > smic_minimum:
        return ApplicableSalaryMinimumSource.CCNS
    if smic_minimum > ccns_minimum:
        return ApplicableSalaryMinimumSource.SMIC
    return ApplicableSalaryMinimumSource.EQUAL


@dataclass(frozen=True, slots=True)
class ApplicableSalaryMinimumResult:
    classification_group: CCNSClassification
    reference_date: date
    territory: SmicTerritory
    remuneration_amount: Decimal
    weekly_hours: Decimal
    ccns_minimum_amount: Decimal
    smic_full_time_monthly_amount: Decimal
    smic_required_minimum_amount: Decimal
    required_minimum_amount: Decimal
    difference_amount: Decimal
    source: ApplicableSalaryMinimumSource
    status: ApplicableSalaryMinimumStatus
    ccns_compliance_result: SalaryMinimumComplianceResult
    smic_version: SmicVersion
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.classification_group) is not CCNSClassification:
            raise TypeError("classification_group doit être un CCNSClassification.")
        _strict_date(self.reference_date)
        if type(self.territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        if type(self.source) is not ApplicableSalaryMinimumSource:
            raise TypeError("source doit être un ApplicableSalaryMinimumSource.")
        if type(self.status) is not ApplicableSalaryMinimumStatus:
            raise TypeError("status doit être un ApplicableSalaryMinimumStatus.")
        if type(self.ccns_compliance_result) is not SalaryMinimumComplianceResult:
            raise TypeError("ccns_compliance_result doit être un SalaryMinimumComplianceResult.")
        if type(self.smic_version) is not SmicVersion:
            raise TypeError("smic_version doit être un SmicVersion.")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")

        remuneration = _strict_decimal(self.remuneration_amount, "remuneration_amount")
        weekly = _strict_decimal(self.weekly_hours, "weekly_hours")
        amounts = (
            remuneration,
            _strict_decimal(self.ccns_minimum_amount, "ccns_minimum_amount"),
            _strict_decimal(self.smic_full_time_monthly_amount, "smic_full_time_monthly_amount"),
            _strict_decimal(self.smic_required_minimum_amount, "smic_required_minimum_amount"),
            _strict_decimal(self.required_minimum_amount, "required_minimum_amount"),
            _strict_decimal(self.difference_amount, "difference_amount"),
        )
        if remuneration < _ZERO:
            raise ValueError("Le montant de rémunération ne peut pas être négatif.")
        if weekly <= _ZERO:
            raise ValueError("La durée hebdomadaire doit être strictement positive.")
        for minimum in amounts[1:5]:
            if minimum <= _ZERO:
                raise ValueError("Les minima doivent être strictement supérieurs à zéro.")
        for amount in amounts:
            if amount != _quantize_amount(amount):
                raise ValueError("Les montants doivent être quantifiés à deux décimales.")

        if self.required_minimum_amount != max(self.ccns_minimum_amount, self.smic_required_minimum_amount):
            raise ValueError("Le minimum exigé doit être égal au maximum des minima CCNS et SMIC.")
        if self.source is not _source_for(self.ccns_minimum_amount, self.smic_required_minimum_amount):
            raise ValueError("La source est incohérente avec la comparaison des minima.")
        if self.difference_amount != self.remuneration_amount - self.required_minimum_amount:
            raise ValueError("La différence doit être égale à la rémunération moins le minimum exigé.")
        expected_status = (
            ApplicableSalaryMinimumStatus.COMPLIANT
            if self.difference_amount >= _ZERO
            else ApplicableSalaryMinimumStatus.NON_COMPLIANT
        )
        if self.status is not expected_status:
            raise ValueError("Le statut est incohérent avec la différence de rémunération.")
        if self.ccns_compliance_result.classification_group != self.classification_group:
            raise ValueError("Le résultat CCNS est incohérent avec la classification.")
        if self.ccns_compliance_result.reference_date != self.reference_date:
            raise ValueError("Le résultat CCNS est incohérent avec la date de référence.")
        if self.ccns_compliance_result.remuneration_amount != self.remuneration_amount:
            raise ValueError("Le résultat CCNS est incohérent avec la rémunération.")
        if self.ccns_compliance_result.weekly_hours != self.weekly_hours:
            raise ValueError("Le résultat CCNS est incohérent avec la durée hebdomadaire.")
        if self.ccns_compliance_result.remuneration_periodicity is not SalaryMinimumPeriodicity.MONTHLY:
            raise ValueError(_ANNUAL_MINIMUM_MESSAGE)
        if self.ccns_compliance_result.required_minimum_amount != self.ccns_minimum_amount:
            raise ValueError("Le résultat CCNS est incohérent avec le minimum CCNS.")
        if self.smic_version.territory is not self.territory:
            raise ValueError("La version de SMIC est incohérente avec le territoire.")
        if not self.smic_version.applies_on(self.reference_date):
            raise ValueError("La version de SMIC est incohérente avec la date de référence.")
        if self.smic_full_time_monthly_amount != self.smic_version.monthly_gross_amount_35h:
            raise ValueError("Le montant SMIC temps plein est incohérent avec la version de SMIC.")

    def is_compliant(self) -> bool:
        return self.status is ApplicableSalaryMinimumStatus.COMPLIANT

    def is_non_compliant(self) -> bool:
        return self.status is ApplicableSalaryMinimumStatus.NON_COMPLIANT

    def is_ccns_minimum(self) -> bool:
        return self.source is ApplicableSalaryMinimumSource.CCNS

    def is_smic_minimum(self) -> bool:
        return self.source is ApplicableSalaryMinimumSource.SMIC

    def are_minimums_equal(self) -> bool:
        return self.source is ApplicableSalaryMinimumSource.EQUAL

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

    def required_increase_amount(self) -> Decimal:
        return self.shortfall_amount() if self.is_non_compliant() else _ZERO


@dataclass(frozen=True, slots=True)
class ApplicableSalaryMinimumService:
    salary_minimum_compliance_service: SalaryMinimumComplianceService
    smic_catalog: SmicCatalog

    def __post_init__(self) -> None:
        if type(self.salary_minimum_compliance_service) is not SalaryMinimumComplianceService:
            raise TypeError("salary_minimum_compliance_service doit être un SalaryMinimumComplianceService.")
        if type(self.smic_catalog) is not SmicCatalog:
            raise TypeError("smic_catalog doit être un SmicCatalog.")

    def evaluate(
        self,
        classification_group: CCNSClassification,
        reference_date: date,
        territory: SmicTerritory,
        remuneration_amount: Decimal,
        weekly_hours: Decimal,
    ) -> ApplicableSalaryMinimumResult:
        if type(classification_group) is not CCNSClassification:
            raise TypeError("classification_group doit être un CCNSClassification.")
        _strict_date(reference_date)
        if type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        remuneration = _strict_decimal(remuneration_amount, "remuneration_amount")
        weekly = _strict_decimal(weekly_hours, "weekly_hours")
        if remuneration < _ZERO:
            raise ValueError("Le montant de rémunération ne peut pas être négatif.")
        if weekly <= _ZERO:
            raise ValueError("La durée hebdomadaire doit être strictement positive.")

        try:
            ccns_result = self.salary_minimum_compliance_service.evaluate(
                classification_group,
                reference_date,
                remuneration,
                SalaryMinimumPeriodicity.MONTHLY,
                weekly,
            )
        except ValueError as exc:
            if "périodicité" in str(exc):
                raise ValueError(_ANNUAL_MINIMUM_MESSAGE) from exc
            raise

        smic_version = self.smic_catalog.version_applicable_on(reference_date, territory)
        smic_full_time = smic_version.monthly_gross_amount_35h
        smic_required = smic_full_time if weekly >= _FULL_TIME_WEEKLY_HOURS else smic_full_time * weekly / _FULL_TIME_WEEKLY_HOURS
        smic_required = _quantize_amount(smic_required)
        ccns_minimum = _quantize_amount(ccns_result.required_minimum_amount)
        remuneration = _quantize_amount(remuneration)
        source = _source_for(ccns_minimum, smic_required)
        required = ccns_minimum if source is not ApplicableSalaryMinimumSource.SMIC else smic_required
        difference = _quantize_amount(remuneration - required)
        status = (
            ApplicableSalaryMinimumStatus.COMPLIANT
            if difference >= _ZERO
            else ApplicableSalaryMinimumStatus.NON_COMPLIANT
        )
        return ApplicableSalaryMinimumResult(
            classification_group=classification_group,
            reference_date=reference_date,
            territory=territory,
            remuneration_amount=remuneration,
            weekly_hours=weekly,
            ccns_minimum_amount=ccns_minimum,
            smic_full_time_monthly_amount=smic_full_time,
            smic_required_minimum_amount=smic_required,
            required_minimum_amount=required,
            difference_amount=difference,
            source=source,
            status=status,
            ccns_compliance_result=ccns_result,
            smic_version=smic_version,
        )
