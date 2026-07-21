from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from domain.contracts.contract_salary_batch_audit import ContractSalaryBatchAuditResult
from domain.contracts.contract_salary_evaluation import (
    ContractSalaryEvaluationFailureReason,
    ContractSalaryEvaluationResult,
    _strict_date,
    _strict_uuid,
)
from domain.convention import ApplicableSalaryMinimumSource, SalaryMinimumAuditResult
from domain.convention.smic import SmicTerritory

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")


class ContractSalaryControlStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_EVALUATED = "not_evaluated"


def _strict_optional_uuid(value: object, field_name: str) -> Optional[UUID]:
    if value is None:
        return None
    return _strict_uuid(value, field_name)


def _strict_optional_decimal(value: object, field_name: str) -> Optional[Decimal]:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être None ou un Decimal strict.")
    if value != value.quantize(_CENT, rounding=ROUND_HALF_UP):
        raise ValueError(f"{field_name} doit être quantifié à deux décimales.")
    return value


def _strict_non_empty_optional_str(value: object, field_name: str) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise TypeError(f"{field_name} doit être None ou une chaîne.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} ne peut pas être vide.")
    return cleaned


def _classification_code(evaluation: ContractSalaryEvaluationResult) -> Optional[str]:
    classification = evaluation.contract.ccns_classification
    return classification.code if classification is not None else evaluation.contract.ccns_classification_code


@dataclass(frozen=True, slots=True)
class ContractSalaryControlRow:
    contract_id: UUID
    employee_id: Optional[UUID]
    reference_date: date
    status: ContractSalaryControlStatus
    classification_code: Optional[str]
    remuneration_amount: Optional[Decimal]
    applicable_minimum_amount: Optional[Decimal]
    shortfall_amount: Decimal
    minimum_source: Optional[ApplicableSalaryMinimumSource]
    territory: Optional[SmicTerritory]
    failure_reason: Optional[ContractSalaryEvaluationFailureReason]
    failure_message: Optional[str]
    issue_code: Optional[str]
    issue_message: Optional[str]
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        _strict_uuid(self.contract_id, "contract_id")
        _strict_optional_uuid(self.employee_id, "employee_id")
        _strict_date(self.reference_date)
        if type(self.status) is not ContractSalaryControlStatus:
            raise TypeError("status doit être un ContractSalaryControlStatus.")
        object.__setattr__(self, "classification_code", _strict_non_empty_optional_str(self.classification_code, "classification_code"))
        _strict_optional_decimal(self.remuneration_amount, "remuneration_amount")
        _strict_optional_decimal(self.applicable_minimum_amount, "applicable_minimum_amount")
        if type(self.shortfall_amount) is not Decimal:
            raise TypeError("shortfall_amount doit être un Decimal strict.")
        if self.shortfall_amount != self.shortfall_amount.quantize(_CENT, rounding=ROUND_HALF_UP):
            raise ValueError("shortfall_amount doit être quantifié à deux décimales.")
        if self.shortfall_amount < _ZERO:
            raise ValueError("shortfall_amount ne peut pas être négatif.")
        if self.minimum_source is not None and type(self.minimum_source) is not ApplicableSalaryMinimumSource:
            raise TypeError("minimum_source doit être None ou un ApplicableSalaryMinimumSource.")
        if self.territory is not None and type(self.territory) is not SmicTerritory:
            raise TypeError("territory doit être None ou un SmicTerritory.")
        if self.failure_reason is not None and type(self.failure_reason) is not ContractSalaryEvaluationFailureReason:
            raise TypeError("failure_reason doit être None ou un ContractSalaryEvaluationFailureReason.")
        object.__setattr__(self, "failure_message", _strict_non_empty_optional_str(self.failure_message, "failure_message"))
        object.__setattr__(self, "issue_code", _strict_non_empty_optional_str(self.issue_code, "issue_code"))
        object.__setattr__(self, "issue_message", _strict_non_empty_optional_str(self.issue_message, "issue_message"))
        _strict_uuid(self.id, "id")
        self._validate_status_consistency()

    def _validate_status_consistency(self) -> None:
        if self.status is ContractSalaryControlStatus.COMPLIANT:
            if self.remuneration_amount is None or self.applicable_minimum_amount is None:
                raise ValueError("Une ligne conforme doit exposer la rémunération et le minimum applicable.")
            if self.shortfall_amount != _ZERO:
                raise ValueError("Une ligne conforme ne doit pas porter de manque salarial.")
            if self.failure_reason is not None or self.failure_message is not None:
                raise ValueError("Une ligne conforme ne doit pas porter d'échec d'évaluation.")
            if self.issue_code is not None or self.issue_message is not None:
                raise ValueError("Une ligne conforme ne doit pas porter d'anomalie.")
            if self.minimum_source is None or self.territory is None:
                raise ValueError("Une ligne conforme doit exposer la source et le territoire du minimum.")
        elif self.status is ContractSalaryControlStatus.NON_COMPLIANT:
            if self.remuneration_amount is None or self.applicable_minimum_amount is None:
                raise ValueError("Une ligne non conforme doit exposer la rémunération et le minimum applicable.")
            if self.shortfall_amount <= _ZERO:
                raise ValueError("Une ligne non conforme doit porter un manque salarial strictement positif.")
            if self.issue_code is None or self.issue_message is None:
                raise ValueError("Une ligne non conforme doit porter les informations d'anomalie.")
            if self.failure_reason is not None or self.failure_message is not None:
                raise ValueError("Une ligne non conforme ne doit pas porter d'échec d'évaluation.")
            if self.minimum_source is None or self.territory is None:
                raise ValueError("Une ligne non conforme doit exposer la source et le territoire du minimum.")
        else:
            if self.failure_reason is None or self.failure_message is None:
                raise ValueError("Une ligne non évaluée doit porter le motif et le message d'échec.")
            if self.shortfall_amount != _ZERO:
                raise ValueError("Une ligne non évaluée ne doit pas porter de manque salarial.")
            if any(value is not None for value in (self.remuneration_amount, self.applicable_minimum_amount, self.minimum_source, self.issue_code, self.issue_message)):
                raise ValueError("Une ligne non évaluée ne doit pas inventer de données salariales ou d'anomalie.")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlProjection:
    reference_date: date
    rows: tuple[ContractSalaryControlRow, ...]
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        _strict_date(self.reference_date)
        if type(self.rows) is not tuple:
            raise TypeError("rows doit être un tuple.")
        _strict_uuid(self.id, "id")
        seen: set[UUID] = set()
        for row in self.rows:
            if type(row) is not ContractSalaryControlRow:
                raise TypeError("rows doit contenir des ContractSalaryControlRow.")
            if row.reference_date != self.reference_date:
                raise ValueError("Toutes les lignes doivent porter la date de référence de la projection.")
            if row.contract_id in seen:
                raise ValueError("Plusieurs lignes portent le même contract_id.")
            seen.add(row.contract_id)

    @property
    def total_count(self) -> int:
        return len(self.rows)

    @property
    def compliant_count(self) -> int:
        return len(self.rows_for_status(ContractSalaryControlStatus.COMPLIANT))

    @property
    def non_compliant_count(self) -> int:
        return len(self.rows_for_status(ContractSalaryControlStatus.NON_COMPLIANT))

    @property
    def not_evaluated_count(self) -> int:
        return len(self.rows_for_status(ContractSalaryControlStatus.NOT_EVALUATED))

    @property
    def total_shortfall_amount(self) -> Decimal:
        return sum((row.shortfall_amount for row in self.rows), _ZERO).quantize(_CENT, rounding=ROUND_HALF_UP)

    @property
    def valid(self) -> bool:
        return all(row.status is ContractSalaryControlStatus.COMPLIANT for row in self.rows)

    def compliant_rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.rows_for_status(ContractSalaryControlStatus.COMPLIANT)

    def non_compliant_rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.rows_for_status(ContractSalaryControlStatus.NON_COMPLIANT)

    def not_evaluated_rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.rows_for_status(ContractSalaryControlStatus.NOT_EVALUATED)

    def row_for_contract(self, contract_id: UUID) -> Optional[ContractSalaryControlRow]:
        contract = _strict_uuid(contract_id, "contract_id")
        matches = tuple(row for row in self.rows if row.contract_id == contract)
        if len(matches) > 1:
            raise ValueError("Plusieurs lignes correspondent au même contract_id.")
        return matches[0] if matches else None

    def rows_for_employee(self, employee_id: UUID) -> tuple[ContractSalaryControlRow, ...]:
        employee = _strict_uuid(employee_id, "employee_id")
        return tuple(row for row in self.rows if row.employee_id == employee)

    def rows_for_status(self, status: ContractSalaryControlStatus) -> tuple[ContractSalaryControlRow, ...]:
        if type(status) is not ContractSalaryControlStatus:
            raise TypeError("status doit être un ContractSalaryControlStatus.")
        return tuple(row for row in self.rows if row.status is status)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlProjectionService:
    def project(self, audit_result: ContractSalaryBatchAuditResult) -> ContractSalaryControlProjection:
        if type(audit_result) is not ContractSalaryBatchAuditResult:
            raise TypeError("audit_result doit être un ContractSalaryBatchAuditResult.")
        rows = tuple(self._row_for_evaluation(audit_result, evaluation) for evaluation in audit_result.evaluations)
        return ContractSalaryControlProjection(audit_result.reference_date, rows)

    def _row_for_evaluation(self, audit_result: ContractSalaryBatchAuditResult, evaluation: ContractSalaryEvaluationResult) -> ContractSalaryControlRow:
        contract_id = evaluation.contract_id()
        employee_id = evaluation.employee_id()
        classification_code = _classification_code(evaluation)
        if evaluation.has_failure():
            if audit_result.audit_result_for_contract(contract_id) is not None:
                raise ValueError("Une évaluation échouée ne doit pas avoir de résultat d'audit.")
            failure = evaluation.failure
            if failure is None:
                raise ValueError("Une évaluation échouée doit porter un échec métier.")
            return ContractSalaryControlRow(contract_id, employee_id, evaluation.reference_date, ContractSalaryControlStatus.NOT_EVALUATED, classification_code, None, None, _ZERO, None, evaluation.resolved_territory, failure.reason, failure.message, None, None)
        audit = audit_result.audit_result_for_contract(contract_id)
        if audit is None:
            raise ValueError("Une évaluation réussie doit avoir un résultat d'audit.")
        return self._row_for_audited_evaluation(evaluation, audit, classification_code)

    def _row_for_audited_evaluation(self, evaluation: ContractSalaryEvaluationResult, audit: SalaryMinimumAuditResult, classification_code: Optional[str]) -> ContractSalaryControlRow:
        result = evaluation.result()
        if audit.compliance_result is not result:
            raise ValueError("Le résultat d'audit ne correspond pas à l'évaluation.")
        issues = audit.issues
        if audit.is_valid():
            if issues:
                raise ValueError("Un audit conforme ne doit pas porter d'anomalie.")
            status = ContractSalaryControlStatus.COMPLIANT
            issue_code = issue_message = None
        else:
            if len(issues) != 1:
                raise ValueError("Le domaine garantit exactement une anomalie salariale par résultat non conforme.")
            status = ContractSalaryControlStatus.NON_COMPLIANT
            issue_code = issues[0].code
            issue_message = issues[0].message
        return ContractSalaryControlRow(evaluation.contract_id(), evaluation.employee_id(), evaluation.reference_date, status, classification_code, result.remuneration_amount, result.required_minimum_amount, audit.shortfall_amount(), result.source, result.territory, None, None, issue_code, issue_message)
