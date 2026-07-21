from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Optional
from uuid import UUID, uuid4

from domain.contracts.contract import Contract
from domain.contracts.contract_salary_evaluation import (
    ContractSalaryEvaluationFailure,
    ContractSalaryEvaluationResult,
    ContractSalaryEvaluationService,
    _strict_date,
    _strict_uuid,
)
from domain.convention import ApplicableSalaryMinimumResult, SalaryMinimumAuditItem
from domain.convention.smic import SmicTerritory


_DUPLICATE_CONTRACT_MESSAGE = "Un même contrat ne peut pas être évalué plusieurs fois dans le même lot."


@dataclass(frozen=True, slots=True)
class ContractSalaryBatchEvaluationResult:
    reference_date: date
    evaluations: tuple[ContractSalaryEvaluationResult, ...]
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        _strict_date(self.reference_date)
        if type(self.evaluations) is not tuple:
            raise TypeError("evaluations doit être un tuple.")
        _strict_uuid(self.id, "id")
        seen_contract_ids: set[UUID] = set()
        for evaluation in self.evaluations:
            if type(evaluation) is not ContractSalaryEvaluationResult:
                raise TypeError("evaluations doit contenir des ContractSalaryEvaluationResult.")
            if evaluation.reference_date != self.reference_date:
                raise ValueError("Toutes les évaluations doivent porter la date de référence du lot.")
            contract_id = evaluation.contract_id()
            if contract_id in seen_contract_ids:
                raise ValueError(_DUPLICATE_CONTRACT_MESSAGE)
            seen_contract_ids.add(contract_id)
        if self.successful_count + self.failed_count != self.total_count:
            raise ValueError("Les compteurs du lot sont incohérents.")

    @property
    def total_count(self) -> int:
        return len(self.evaluations)

    @property
    def successful_count(self) -> int:
        return sum(1 for evaluation in self.evaluations if evaluation.is_successful())

    @property
    def failed_count(self) -> int:
        return sum(1 for evaluation in self.evaluations if evaluation.has_failure())

    def successful_evaluations(self) -> tuple[ContractSalaryEvaluationResult, ...]:
        return tuple(evaluation for evaluation in self.evaluations if evaluation.is_successful())

    def failed_evaluations(self) -> tuple[ContractSalaryEvaluationResult, ...]:
        return tuple(evaluation for evaluation in self.evaluations if evaluation.has_failure())

    def applicable_salary_minimum_results(self) -> tuple[ApplicableSalaryMinimumResult, ...]:
        return tuple(evaluation.result() for evaluation in self.successful_evaluations())

    def failures(self) -> tuple[ContractSalaryEvaluationFailure, ...]:
        return tuple(evaluation.failure for evaluation in self.failed_evaluations() if evaluation.failure is not None)

    def evaluation_for_contract(self, contract_id: UUID) -> Optional[ContractSalaryEvaluationResult]:
        contract = _strict_uuid(contract_id, "contract_id")
        matches = tuple(evaluation for evaluation in self.evaluations if evaluation.contract_id() == contract)
        if len(matches) > 1:
            raise ValueError("Plusieurs évaluations correspondent au même contract_id.")
        return matches[0] if matches else None

    def evaluations_for_employee(self, employee_id: UUID) -> tuple[ContractSalaryEvaluationResult, ...]:
        employee = _strict_uuid(employee_id, "employee_id")
        return tuple(evaluation for evaluation in self.evaluations if evaluation.employee_id() == employee)

    def has_successful_evaluations(self) -> bool:
        return self.successful_count > 0

    def has_failed_evaluations(self) -> bool:
        return self.failed_count > 0

    def to_salary_minimum_audit_items(self) -> tuple[SalaryMinimumAuditItem, ...]:
        return tuple(
            SalaryMinimumAuditItem(
                evaluation.result(),
                employee_id=evaluation.employee_id(),
                contract_id=evaluation.contract_id(),
            )
            for evaluation in self.successful_evaluations()
        )


@dataclass(frozen=True, slots=True)
class ContractSalaryBatchEvaluationService:
    contract_salary_evaluation_service: ContractSalaryEvaluationService

    def __post_init__(self) -> None:
        if type(self.contract_salary_evaluation_service) is not ContractSalaryEvaluationService:
            raise TypeError("contract_salary_evaluation_service doit être un ContractSalaryEvaluationService.")

    def evaluate(
        self,
        contracts: Iterable[Contract],
        reference_date: date,
        *,
        territory: Optional[SmicTerritory] = None,
    ) -> ContractSalaryBatchEvaluationResult:
        _strict_date(reference_date)
        if territory is not None and type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        if contracts is None:
            raise TypeError("contracts ne peut pas être None.")
        if isinstance(contracts, (str, bytes)):
            raise TypeError("contracts doit être un itérable de Contract.")
        try:
            materialized = tuple(contracts)
        except TypeError as exc:
            raise TypeError("contracts doit être itérable.") from exc

        evaluations: list[ContractSalaryEvaluationResult] = []
        seen_contract_ids: set[UUID] = set()
        for contract in materialized:
            if type(contract) is not Contract:
                raise TypeError("contracts doit contenir uniquement des Contract.")
            evaluation = self.contract_salary_evaluation_service.evaluate(
                contract,
                reference_date,
                territory=territory,
            )
            contract_id = evaluation.contract_id()
            if contract_id in seen_contract_ids:
                raise ValueError(_DUPLICATE_CONTRACT_MESSAGE)
            seen_contract_ids.add(contract_id)
            evaluations.append(evaluation)
        return ContractSalaryBatchEvaluationResult(reference_date, tuple(evaluations))
