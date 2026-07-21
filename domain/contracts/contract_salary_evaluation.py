from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from domain.contracts.contract import Contract
from domain.convention.applicable_salary_minimum import (
    ApplicableSalaryMinimumResult,
    ApplicableSalaryMinimumService,
)
from domain.convention.classification import CCNSClassification
from domain.convention.smic import SmicTerritory


class ContractSalaryEvaluationStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class ContractSalaryEvaluationFailureReason(str, Enum):
    MISSING_CLASSIFICATION = "missing_classification"
    MISSING_REFERENCE_DATE = "missing_reference_date"
    MISSING_REMUNERATION = "missing_remuneration"
    MISSING_WEEKLY_HOURS = "missing_weekly_hours"
    MISSING_TERRITORY = "missing_territory"


def _strict_date(value: object, field_name: str = "reference_date") -> date:
    if type(value) is not date:
        raise TypeError(f"{field_name} doit être une date stricte.")
    return value


def _strict_decimal(value: object, field_name: str) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être un Decimal strict.")
    return value


@dataclass(frozen=True, slots=True)
class ContractSalaryEvaluationResult:
    contract: Contract
    status: ContractSalaryEvaluationStatus
    applicable_salary_minimum_result: Optional[ApplicableSalaryMinimumResult]
    failure_reason: Optional[ContractSalaryEvaluationFailureReason]
    resolved_territory: Optional[SmicTerritory]
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.contract) is not Contract:
            raise TypeError("contract doit être un Contract.")
        if type(self.status) is not ContractSalaryEvaluationStatus:
            raise TypeError("status doit être un ContractSalaryEvaluationStatus.")
        if self.applicable_salary_minimum_result is not None and type(self.applicable_salary_minimum_result) is not ApplicableSalaryMinimumResult:
            raise TypeError("applicable_salary_minimum_result doit être un ApplicableSalaryMinimumResult.")
        if self.failure_reason is not None and type(self.failure_reason) is not ContractSalaryEvaluationFailureReason:
            raise TypeError("failure_reason doit être un ContractSalaryEvaluationFailureReason.")
        if self.resolved_territory is not None and type(self.resolved_territory) is not SmicTerritory:
            raise TypeError("resolved_territory doit être un SmicTerritory.")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")

        if self.status is ContractSalaryEvaluationStatus.SUCCESS:
            if self.applicable_salary_minimum_result is None:
                raise ValueError("Un succès doit contenir un résultat de minimum salarial applicable.")
            if self.failure_reason is not None:
                raise ValueError("Un succès ne doit pas contenir de motif d'échec.")
            if self.resolved_territory is None:
                raise ValueError("Un succès doit contenir le territoire résolu.")
            if self.contract.smic_territory is not None and self.resolved_territory is not self.contract.smic_territory:
                raise ValueError("Le territoire résolu doit respecter celui du contrat.")
            if self.applicable_salary_minimum_result.territory is not self.resolved_territory:
                raise ValueError("Le territoire du minimum applicable doit être le territoire résolu.")
            return

        if self.applicable_salary_minimum_result is not None:
            raise ValueError("Un échec ne doit pas contenir de résultat de minimum salarial applicable.")
        if self.failure_reason is None:
            raise ValueError("Un échec doit contenir un motif.")
        if self.failure_reason is ContractSalaryEvaluationFailureReason.MISSING_TERRITORY and self.resolved_territory is not None:
            raise ValueError("Un échec MISSING_TERRITORY ne doit pas contenir de territoire résolu.")

    def is_success(self) -> bool:
        return self.status is ContractSalaryEvaluationStatus.SUCCESS

    def is_failure(self) -> bool:
        return self.status is ContractSalaryEvaluationStatus.FAILURE


@dataclass(frozen=True, slots=True)
class ContractSalaryEvaluationService:
    applicable_salary_minimum_service: ApplicableSalaryMinimumService

    def __post_init__(self) -> None:
        if type(self.applicable_salary_minimum_service) is not ApplicableSalaryMinimumService:
            raise TypeError("applicable_salary_minimum_service doit être un ApplicableSalaryMinimumService.")

    def evaluate(
        self,
        contract: Contract,
        reference_date: Optional[date] = None,
        territory: Optional[SmicTerritory] = None,
    ) -> ContractSalaryEvaluationResult:
        if type(contract) is not Contract:
            raise TypeError("contract doit être un Contract.")
        if reference_date is not None:
            _strict_date(reference_date)
        if territory is not None and type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")

        if contract.ccns_classification is None:
            return self._failure(contract, ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION, None)
        if type(contract.ccns_classification) is not CCNSClassification:
            raise TypeError("contract.ccns_classification doit être un CCNSClassification.")

        resolved_reference_date = reference_date or contract.start_date
        if resolved_reference_date is None:
            return self._failure(contract, ContractSalaryEvaluationFailureReason.MISSING_REFERENCE_DATE, None)
        if contract.base_salary_amount is None:
            return self._failure(contract, ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION, None)
        remuneration = _strict_decimal(contract.base_salary_amount, "contract.base_salary_amount")
        if contract.weekly_reference_hours is None:
            return self._failure(contract, ContractSalaryEvaluationFailureReason.MISSING_WEEKLY_HOURS, None)
        weekly_hours = _strict_decimal(contract.weekly_reference_hours, "contract.weekly_reference_hours")

        resolved_territory = contract.smic_territory if contract.smic_territory is not None else territory
        if resolved_territory is None:
            return self._failure(contract, ContractSalaryEvaluationFailureReason.MISSING_TERRITORY, None)
        if type(resolved_territory) is not SmicTerritory:
            raise TypeError("resolved_territory doit être un SmicTerritory.")

        result = self.applicable_salary_minimum_service.evaluate(
            contract.ccns_classification,
            resolved_reference_date,
            resolved_territory,
            remuneration,
            weekly_hours,
        )
        return ContractSalaryEvaluationResult(
            contract=contract,
            status=ContractSalaryEvaluationStatus.SUCCESS,
            applicable_salary_minimum_result=result,
            failure_reason=None,
            resolved_territory=resolved_territory,
        )

    @staticmethod
    def _failure(
        contract: Contract,
        reason: ContractSalaryEvaluationFailureReason,
        resolved_territory: Optional[SmicTerritory],
    ) -> ContractSalaryEvaluationResult:
        return ContractSalaryEvaluationResult(
            contract=contract,
            status=ContractSalaryEvaluationStatus.FAILURE,
            applicable_salary_minimum_result=None,
            failure_reason=reason,
            resolved_territory=resolved_territory,
        )
