from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional
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
