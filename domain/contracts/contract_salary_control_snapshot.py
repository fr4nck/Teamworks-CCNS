from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID, uuid4

from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason, _strict_date, _strict_uuid
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")
CURRENT_SCHEMA_VERSION = 1


def _strict_datetime(value: object, field_name: str) -> None:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} doit être un datetime strict.")


def _strict_int(value: object, field_name: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field_name} doit être un int strict.")
    if value < 0:
        raise ValueError(f"{field_name} ne peut pas être négatif.")


def _strict_optional_decimal(value: object, field_name: str) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être None ou un Decimal strict.")
    if value != value.quantize(_CENT, rounding=ROUND_HALF_UP):
        raise ValueError(f"{field_name} doit être quantifié à deux décimales.")


def _strict_optional_uuid(value: object, field_name: str) -> None:
    if value is not None:
        _strict_uuid(value, field_name)


def _strict_optional_str(value: object, field_name: str) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise TypeError(f"{field_name} doit être None ou une chaîne.")
    cleaned = value.strip()
    return cleaned or None


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshotRow:
    contract_id: UUID
    employee_id: Optional[UUID]
    status: ContractSalaryControlStatus
    remuneration_amount: Optional[Decimal]
    applicable_minimum_amount: Optional[Decimal]
    shortfall_amount: Decimal
    classification_code: Optional[str]
    minimum_source: Optional[ApplicableSalaryMinimumSource]
    territory: Optional[SmicTerritory]
    failure_reason: Optional[ContractSalaryEvaluationFailureReason]
    failure_message: Optional[str]
    issue_code: Optional[str]
    issue_message: Optional[str]

    def __post_init__(self) -> None:
        _strict_uuid(self.contract_id, "contract_id")
        _strict_optional_uuid(self.employee_id, "employee_id")
        if type(self.status) is not ContractSalaryControlStatus:
            raise TypeError("status doit être un ContractSalaryControlStatus.")
        _strict_optional_decimal(self.remuneration_amount, "remuneration_amount")
        _strict_optional_decimal(self.applicable_minimum_amount, "applicable_minimum_amount")
        if type(self.shortfall_amount) is not Decimal:
            raise TypeError("shortfall_amount doit être un Decimal strict.")
        if self.shortfall_amount != self.shortfall_amount.quantize(_CENT, rounding=ROUND_HALF_UP):
            raise ValueError("shortfall_amount doit être quantifié à deux décimales.")
        object.__setattr__(self, "classification_code", _strict_optional_str(self.classification_code, "classification_code"))
        if self.minimum_source is not None and type(self.minimum_source) is not ApplicableSalaryMinimumSource:
            raise TypeError("minimum_source doit être None ou un ApplicableSalaryMinimumSource.")
        if self.territory is not None and type(self.territory) is not SmicTerritory:
            raise TypeError("territory doit être None ou un SmicTerritory.")
        if self.failure_reason is not None and type(self.failure_reason) is not ContractSalaryEvaluationFailureReason:
            raise TypeError("failure_reason doit être None ou un ContractSalaryEvaluationFailureReason.")
        object.__setattr__(self, "failure_message", _strict_optional_str(self.failure_message, "failure_message"))
        object.__setattr__(self, "issue_code", _strict_optional_str(self.issue_code, "issue_code"))
        object.__setattr__(self, "issue_message", _strict_optional_str(self.issue_message, "issue_message"))


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshot:
    snapshot_id: UUID
    reference_date: date
    executed_at: datetime
    total_contracts: int
    compliant_contracts: int
    non_compliant_contracts: int
    not_evaluated_contracts: int
    total_shortfall_amount: Decimal
    rows: tuple[ContractSalaryControlSnapshotRow, ...]
    created_by: Optional[str] = None
    schema_version: int = CURRENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _strict_uuid(self.snapshot_id, "snapshot_id")
        _strict_date(self.reference_date)
        _strict_datetime(self.executed_at, "executed_at")
        for name in ("total_contracts", "compliant_contracts", "non_compliant_contracts", "not_evaluated_contracts", "schema_version"):
            _strict_int(getattr(self, name), name)
        if type(self.total_shortfall_amount) is not Decimal:
            raise TypeError("total_shortfall_amount doit être un Decimal strict.")
        if self.total_shortfall_amount != self.total_shortfall_amount.quantize(_CENT, rounding=ROUND_HALF_UP):
            raise ValueError("total_shortfall_amount doit être quantifié à deux décimales.")
        if type(self.rows) is not tuple:
            raise TypeError("rows doit être un tuple strict.")
        object.__setattr__(self, "created_by", _strict_optional_str(self.created_by, "created_by"))
        seen: set[UUID] = set()
        for row in self.rows:
            if type(row) is not ContractSalaryControlSnapshotRow:
                raise TypeError("rows doit contenir des ContractSalaryControlSnapshotRow.")
            if row.contract_id in seen:
                raise ValueError("Plusieurs lignes portent le même contract_id.")
            seen.add(row.contract_id)
        if self.total_contracts != len(self.rows):
            raise ValueError("total_contracts doit correspondre au nombre de lignes.")
        if self.compliant_contracts + self.non_compliant_contracts + self.not_evaluated_contracts != self.total_contracts:
            raise ValueError("Les compteurs de statuts doivent correspondre au total.")
        if self.total_shortfall_amount != sum((row.shortfall_amount for row in self.rows), _ZERO).quantize(_CENT):
            raise ValueError("total_shortfall_amount doit correspondre à la somme exacte des lignes.")

    def duplicate_key(self) -> tuple:
        return (
            self.reference_date,
            tuple((r.contract_id, r.status, r.remuneration_amount, r.applicable_minimum_amount, r.shortfall_amount, r.failure_reason, r.failure_message, r.issue_code, r.issue_message) for r in self.rows),
        )

    @classmethod
    def new_empty(cls, reference_date: date, executed_at: datetime, *, snapshot_id: UUID | None = None, created_by: str | None = None):
        return cls(snapshot_id or uuid4(), reference_date, executed_at, 0, 0, 0, 0, _ZERO, (), created_by)
