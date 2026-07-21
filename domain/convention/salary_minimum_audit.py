from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping, Optional
from uuid import UUID, uuid4

from domain.convention.applicable_salary_minimum import (
    ApplicableSalaryMinimumResult,
    ApplicableSalaryMinimumSource,
    ApplicableSalaryMinimumStatus,
)
from domain.engine.anomaly_level import AnomalyLevel

SALARY_MINIMUM_AUDIT_CODE = "REMUNERATION_BELOW_APPLICABLE_MINIMUM"
SALARY_MINIMUM_AUDIT_MESSAGE = "La rémunération brute mensuelle est inférieure au minimum salarial applicable."
_ZERO = Decimal("0.00")
_CENT = Decimal("0.01")


class SalaryMinimumAuditIssueType(str, Enum):
    REMUNERATION_BELOW_APPLICABLE_MINIMUM = "remuneration_below_applicable_minimum"


def _strict_uuid(value: object, field_name: str) -> Optional[UUID]:
    if value is None:
        return None
    if type(value) is not UUID:
        raise TypeError(f"{field_name} doit être None ou un UUID strict.")
    return value


def _strict_compliance_result(value: object) -> ApplicableSalaryMinimumResult:
    if type(value) is not ApplicableSalaryMinimumResult:
        raise TypeError("compliance_result doit être un ApplicableSalaryMinimumResult.")
    return value


@dataclass(frozen=True, slots=True)
class SalaryMinimumAuditIssue:
    issue_type: SalaryMinimumAuditIssueType
    level: AnomalyLevel
    code: str
    message: str
    compliance_result: ApplicableSalaryMinimumResult
    details: Mapping[str, object]
    employee_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.issue_type) is not SalaryMinimumAuditIssueType:
            raise TypeError("issue_type doit être un SalaryMinimumAuditIssueType.")
        if type(self.level) is not AnomalyLevel:
            raise TypeError("level doit être un AnomalyLevel.")
        if self.level is not AnomalyLevel.BLOCKING:
            raise ValueError("La gravité du déficit de minimum salarial doit être BLOCKING.")
        if self.code != SALARY_MINIMUM_AUDIT_CODE:
            raise ValueError("Le code d'audit salarial est incohérent.")
        if self.message != SALARY_MINIMUM_AUDIT_MESSAGE:
            raise ValueError("Le message d'audit salarial est incohérent.")
        result = _strict_compliance_result(self.compliance_result)
        if not result.is_non_compliant():
            raise ValueError("Une anomalie de minimum salarial exige un résultat non conforme.")
        _strict_uuid(self.employee_id, "employee_id")
        _strict_uuid(self.contract_id, "contract_id")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")
        if not isinstance(self.details, Mapping):
            raise TypeError("details doit être un mapping.")
        expected = _issue_details(result, self.employee_id, self.contract_id)
        if dict(self.details) != expected:
            raise ValueError("Les détails de l'anomalie sont incohérents avec le résultat source.")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))

    @property
    def person_id(self) -> Optional[str]:
        return str(self.employee_id) if self.employee_id is not None else None

    @property
    def object_type(self) -> str:
        return "contract" if self.contract_id is not None else "salary_minimum_audit"

    @property
    def object_id(self) -> str:
        return str(self.contract_id or self.compliance_result.id)

    def shortfall_amount(self) -> Decimal:
        return self.compliance_result.shortfall_amount()

    def applicable_source(self) -> ApplicableSalaryMinimumSource:
        return self.compliance_result.source


def _issue_details(
    result: ApplicableSalaryMinimumResult,
    employee_id: Optional[UUID],
    contract_id: Optional[UUID],
) -> dict[str, object]:
    return {
        "remuneration_amount": result.remuneration_amount,
        "required_minimum_amount": result.required_minimum_amount,
        "difference_amount": result.difference_amount,
        "shortfall_amount": result.shortfall_amount(),
        "ccns_minimum_amount": result.ccns_minimum_amount,
        "smic_required_minimum_amount": result.smic_required_minimum_amount,
        "source": result.source,
        "classification_group": result.classification_group,
        "reference_date": result.reference_date,
        "territory": result.territory,
        "weekly_hours": result.weekly_hours,
        "employee_id": employee_id,
        "contract_id": contract_id,
    }


@dataclass(frozen=True, slots=True)
class SalaryMinimumAuditResult:
    compliance_result: ApplicableSalaryMinimumResult
    valid: bool
    issues: tuple[SalaryMinimumAuditIssue, ...]
    employee_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        result = _strict_compliance_result(self.compliance_result)
        if type(self.valid) is not bool:
            raise TypeError("valid doit être un bool strict.")
        if type(self.issues) is not tuple:
            raise TypeError("issues doit être un tuple.")
        _strict_uuid(self.employee_id, "employee_id")
        _strict_uuid(self.contract_id, "contract_id")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")
        expected_valid = result.status is ApplicableSalaryMinimumStatus.COMPLIANT
        if self.valid is not expected_valid:
            raise ValueError("valid est incohérent avec le résultat de conformité.")
        if result.is_compliant() and self.issues:
            raise ValueError("Un résultat conforme ne doit pas porter d'anomalie.")
        seen = set()
        for issue in self.issues:
            if type(issue) is not SalaryMinimumAuditIssue:
                raise TypeError("issues doit contenir des SalaryMinimumAuditIssue.")
            if issue.issue_type in seen:
                raise ValueError("Une anomalie de même type est dupliquée.")
            seen.add(issue.issue_type)
            if issue.compliance_result is not result:
                raise ValueError("L'anomalie doit être rattachée au résultat source.")
            if issue.shortfall_amount() != result.shortfall_amount():
                raise ValueError("Le déficit de l'anomalie est incohérent.")
            if issue.applicable_source() is not result.source:
                raise ValueError("La source de l'anomalie est incohérente.")
            if issue.employee_id != self.employee_id or issue.contract_id != self.contract_id:
                raise ValueError("Les références de l'anomalie sont incohérentes.")
        if result.is_non_compliant() and len(self.issues) != 1:
            raise ValueError("Un résultat non conforme doit porter exactement une anomalie.")
        if result.difference_amount >= _ZERO and self.issues:
            raise ValueError("Aucune anomalie de rémunération insuffisante n'est autorisée sans déficit.")

    def is_valid(self) -> bool:
        return self.valid

    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def issue_count(self) -> int:
        return len(self.issues)

    def has_employee_reference(self) -> bool:
        return self.employee_id is not None

    def has_contract_reference(self) -> bool:
        return self.contract_id is not None

    def shortfall_amount(self) -> Decimal:
        return self.compliance_result.shortfall_amount()

    def applicable_source(self) -> ApplicableSalaryMinimumSource:
        return self.compliance_result.source


@dataclass(frozen=True, slots=True)
class SalaryMinimumAuditService:
    def audit(
        self,
        compliance_result: ApplicableSalaryMinimumResult,
        *,
        employee_id: Optional[UUID] = None,
        contract_id: Optional[UUID] = None,
    ) -> SalaryMinimumAuditResult:
        result = _strict_compliance_result(compliance_result)
        employee = _strict_uuid(employee_id, "employee_id")
        contract = _strict_uuid(contract_id, "contract_id")
        if result.is_compliant():
            issues: tuple[SalaryMinimumAuditIssue, ...] = ()
            return SalaryMinimumAuditResult(result, True, issues, employee, contract)
        issue = SalaryMinimumAuditIssue(
            issue_type=SalaryMinimumAuditIssueType.REMUNERATION_BELOW_APPLICABLE_MINIMUM,
            level=AnomalyLevel.BLOCKING,
            code=SALARY_MINIMUM_AUDIT_CODE,
            message=SALARY_MINIMUM_AUDIT_MESSAGE,
            compliance_result=result,
            details=_issue_details(result, employee, contract),
            employee_id=employee,
            contract_id=contract,
        )
        return SalaryMinimumAuditResult(result, False, (issue,), employee, contract)


_RATE_QUANT = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class SalaryMinimumAuditItem:
    compliance_result: ApplicableSalaryMinimumResult
    employee_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        _strict_compliance_result(self.compliance_result)
        _strict_uuid(self.employee_id, "employee_id")
        _strict_uuid(self.contract_id, "contract_id")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")

    def has_employee_reference(self) -> bool:
        return self.employee_id is not None

    def has_contract_reference(self) -> bool:
        return self.contract_id is not None

    def is_compliant(self) -> bool:
        return self.compliance_result.is_compliant()

    def is_non_compliant(self) -> bool:
        return self.compliance_result.is_non_compliant()

    def shortfall_amount(self) -> Decimal:
        return self.compliance_result.shortfall_amount()


@dataclass(frozen=True, slots=True)
class SalaryMinimumBatchAuditResult:
    items: tuple[SalaryMinimumAuditItem, ...]
    audit_results: tuple[SalaryMinimumAuditResult, ...]
    issues: tuple[SalaryMinimumAuditIssue, ...]
    valid: bool
    compliant_count: int
    non_compliant_count: int
    total_shortfall_amount: Decimal
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.items) is not tuple:
            raise TypeError("items doit être un tuple.")
        if type(self.audit_results) is not tuple:
            raise TypeError("audit_results doit être un tuple.")
        if type(self.issues) is not tuple:
            raise TypeError("issues doit être un tuple.")
        if type(self.valid) is not bool:
            raise TypeError("valid doit être un bool strict.")
        if type(self.compliant_count) is not int:
            raise TypeError("compliant_count doit être un int strict.")
        if type(self.non_compliant_count) is not int:
            raise TypeError("non_compliant_count doit être un int strict.")
        if self.compliant_count < 0 or self.non_compliant_count < 0:
            raise ValueError("Les compteurs ne peuvent pas être négatifs.")
        if type(self.total_shortfall_amount) is not Decimal:
            raise TypeError("total_shortfall_amount doit être un Decimal strict.")
        total = self.total_shortfall_amount
        if total != total.quantize(_CENT, rounding=ROUND_HALF_UP):
            raise ValueError("total_shortfall_amount doit être quantifié à deux décimales.")
        if total < _ZERO:
            raise ValueError("total_shortfall_amount ne peut pas être négatif.")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")
        if not self.items:
            raise ValueError("items ne peut pas être vide.")
        if len(self.items) != len(self.audit_results):
            raise ValueError("items et audit_results doivent avoir la même longueur.")

        expected_issues: list[SalaryMinimumAuditIssue] = []
        expected_total = _ZERO
        expected_compliant = 0
        expected_non_compliant = 0
        for item, result in zip(self.items, self.audit_results):
            if type(item) is not SalaryMinimumAuditItem:
                raise TypeError("items doit contenir des SalaryMinimumAuditItem.")
            if type(result) is not SalaryMinimumAuditResult:
                raise TypeError("audit_results doit contenir des SalaryMinimumAuditResult.")
            if result.compliance_result is not item.compliance_result:
                raise ValueError("Chaque résultat d'audit doit correspondre à l'item de même rang.")
            if result.employee_id != item.employee_id or result.contract_id != item.contract_id:
                raise ValueError("Les UUID salarié et contrat doivent correspondre.")
            expected_issues.extend(result.issues)
            expected_total += result.shortfall_amount()
            if result.is_valid():
                expected_compliant += 1
            else:
                expected_non_compliant += 1
        for issue in self.issues:
            if type(issue) is not SalaryMinimumAuditIssue:
                raise TypeError("issues doit contenir des SalaryMinimumAuditIssue.")
        if self.issues != tuple(expected_issues):
            raise ValueError("issues doit être la concaténation ordonnée des anomalies des résultats.")
        expected_valid = all(result.is_valid() for result in self.audit_results)
        if self.valid is not expected_valid:
            raise ValueError("valid doit refléter tous les résultats individuels.")
        if self.compliant_count != expected_compliant:
            raise ValueError("compliant_count est incohérent.")
        if self.non_compliant_count != expected_non_compliant:
            raise ValueError("non_compliant_count est incohérent.")
        if self.compliant_count + self.non_compliant_count != len(self.items):
            raise ValueError("La somme des compteurs doit être égale au nombre d'items.")
        expected_total = expected_total.quantize(_CENT, rounding=ROUND_HALF_UP)
        if total != expected_total:
            raise ValueError("total_shortfall_amount est incohérent avec les déficits individuels.")

    def is_valid(self) -> bool:
        return self.valid

    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def item_count(self) -> int:
        return len(self.items)

    def issue_count(self) -> int:
        return len(self.issues)

    def all_compliant(self) -> bool:
        return self.compliant_count == len(self.items)

    def has_non_compliant_items(self) -> bool:
        return self.non_compliant_count > 0

    def compliance_rate(self) -> Decimal:
        rate = Decimal(self.compliant_count) / Decimal(self.item_count())
        return rate.quantize(_RATE_QUANT, rounding=ROUND_HALF_UP)

    def results_for_employee(self, employee_id: UUID) -> tuple[SalaryMinimumAuditResult, ...]:
        employee = _strict_uuid(employee_id, "employee_id")
        return tuple(result for result in self.audit_results if result.employee_id == employee)

    def results_for_contract(self, contract_id: UUID) -> tuple[SalaryMinimumAuditResult, ...]:
        contract = _strict_uuid(contract_id, "contract_id")
        return tuple(result for result in self.audit_results if result.contract_id == contract)

    def issues_for_employee(self, employee_id: UUID) -> tuple[SalaryMinimumAuditIssue, ...]:
        employee = _strict_uuid(employee_id, "employee_id")
        return tuple(issue for issue in self.issues if issue.employee_id == employee)

    def issues_for_contract(self, contract_id: UUID) -> tuple[SalaryMinimumAuditIssue, ...]:
        contract = _strict_uuid(contract_id, "contract_id")
        return tuple(issue for issue in self.issues if issue.contract_id == contract)


@dataclass(frozen=True, slots=True)
class SalaryMinimumBatchAuditService:
    salary_minimum_audit_service: SalaryMinimumAuditService

    def __post_init__(self) -> None:
        if type(self.salary_minimum_audit_service) is not SalaryMinimumAuditService:
            raise TypeError("salary_minimum_audit_service doit être un SalaryMinimumAuditService.")

    def audit(self, items: Iterable[SalaryMinimumAuditItem]) -> SalaryMinimumBatchAuditResult:
        if items is None:
            raise TypeError("items ne peut pas être None.")
        if isinstance(items, (str, bytes)):
            raise TypeError("items doit être un itérable d'items d'audit salarial.")
        try:
            materialized = tuple(items)
        except TypeError as exc:
            raise TypeError("items doit être itérable.") from exc
        if not materialized:
            raise ValueError("items ne peut pas être vide.")
        seen: set[UUID] = set()
        for item in materialized:
            if type(item) is not SalaryMinimumAuditItem:
                raise TypeError("items doit contenir des SalaryMinimumAuditItem.")
            result_id = item.compliance_result.id
            if result_id in seen:
                raise ValueError("Un même résultat de conformité ne peut pas être audité plusieurs fois dans le même lot.")
            seen.add(result_id)

        audit_results = tuple(
            self.salary_minimum_audit_service.audit(
                item.compliance_result,
                employee_id=item.employee_id,
                contract_id=item.contract_id,
            )
            for item in materialized
        )
        issues = tuple(issue for result in audit_results for issue in result.issues)
        compliant_count = sum(1 for result in audit_results if result.is_valid())
        non_compliant_count = len(audit_results) - compliant_count
        total_shortfall = sum(
            (result.shortfall_amount() for result in audit_results),
            _ZERO,
        ).quantize(_CENT, rounding=ROUND_HALF_UP)
        return SalaryMinimumBatchAuditResult(
            items=materialized,
            audit_results=audit_results,
            issues=issues,
            valid=all(result.is_valid() for result in audit_results),
            compliant_count=compliant_count,
            non_compliant_count=non_compliant_count,
            total_shortfall_amount=total_shortfall,
        )
