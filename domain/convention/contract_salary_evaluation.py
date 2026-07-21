from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from domain.contracts.contract import Contract
from domain.convention.applicable_salary_minimum import ApplicableSalaryMinimumResult, ApplicableSalaryMinimumService
from domain.convention.classification import CCNSClassification
from domain.convention.smic import SmicTerritory


class ContractSalaryEvaluationStatus(str, Enum):
    SUCCESS = "success"
    MISSING_TERRITORY = "missing_territory"


@dataclass(frozen=True, slots=True)
class ContractSalaryEvaluationResult:
    contract: Contract
    reference_date: date
    status: ContractSalaryEvaluationStatus
    resolved_territory: Optional[SmicTerritory]
    applicable_salary_minimum_result: Optional[ApplicableSalaryMinimumResult]
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.contract) is not Contract:
            raise TypeError("contract doit être un Contract.")
        if type(self.reference_date) is not date:
            raise TypeError("reference_date doit être une date stricte.")
        if type(self.status) is not ContractSalaryEvaluationStatus:
            raise TypeError("status doit être un ContractSalaryEvaluationStatus.")
        if self.resolved_territory is not None and type(self.resolved_territory) is not SmicTerritory:
            raise TypeError("resolved_territory doit être un SmicTerritory lorsqu’il est renseigné.")
        if self.applicable_salary_minimum_result is not None and type(self.applicable_salary_minimum_result) is not ApplicableSalaryMinimumResult:
            raise TypeError("applicable_salary_minimum_result doit être un ApplicableSalaryMinimumResult lorsqu’il est renseigné.")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")

        contract_territory = self.contract.smic_territory
        if contract_territory is not None and type(contract_territory) is not SmicTerritory:
            raise TypeError("contract.smic_territory doit être un SmicTerritory lorsqu’il est renseigné.")

        if self.status is ContractSalaryEvaluationStatus.SUCCESS:
            if self.resolved_territory is None:
                raise ValueError("resolved_territory est obligatoire pour une évaluation réussie.")
            if self.applicable_salary_minimum_result is None:
                raise ValueError("applicable_salary_minimum_result est obligatoire pour une évaluation réussie.")
            if self.applicable_salary_minimum_result.territory is not self.resolved_territory:
                raise ValueError("Le résultat du minimum applicable est incohérent avec le territoire résolu.")
            if contract_territory is not None and self.resolved_territory is not contract_territory:
                raise ValueError("Le territoire résolu est incohérent avec le territoire du contrat.")
        elif self.status is ContractSalaryEvaluationStatus.MISSING_TERRITORY:
            if self.resolved_territory is not None:
                raise ValueError("resolved_territory doit être None lorsque le territoire est manquant.")
            if self.applicable_salary_minimum_result is not None:
                raise ValueError("applicable_salary_minimum_result doit être None lorsque le territoire est manquant.")

    def is_success(self) -> bool:
        return self.status is ContractSalaryEvaluationStatus.SUCCESS


@dataclass(frozen=True, slots=True)
class ContractSalaryEvaluationService:
    applicable_salary_minimum_service: ApplicableSalaryMinimumService

    def __post_init__(self) -> None:
        if type(self.applicable_salary_minimum_service) is not ApplicableSalaryMinimumService:
            raise TypeError("applicable_salary_minimum_service doit être un ApplicableSalaryMinimumService.")

    def evaluate(
        self,
        contract: Contract,
        reference_date: date,
        territory: Optional[SmicTerritory] = None,
    ) -> ContractSalaryEvaluationResult:
        if type(contract) is not Contract:
            raise TypeError("contract doit être un Contract.")
        if type(reference_date) is not date:
            raise TypeError("reference_date doit être une date stricte.")
        if territory is not None and type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory lorsqu’il est renseigné.")
        contract_territory = contract.smic_territory
        if contract_territory is not None and type(contract_territory) is not SmicTerritory:
            raise TypeError("contract.smic_territory doit être un SmicTerritory lorsqu’il est renseigné.")
        resolved_territory = contract_territory if contract_territory is not None else territory
        if resolved_territory is None:
            return ContractSalaryEvaluationResult(
                contract=contract,
                reference_date=reference_date,
                status=ContractSalaryEvaluationStatus.MISSING_TERRITORY,
                resolved_territory=None,
                applicable_salary_minimum_result=None,
            )

        classification = CCNSClassification(code=contract.ccns_classification_code or "G1", label=contract.ccns_classification_code or "G1")
        result = self.applicable_salary_minimum_service.evaluate(
            classification,
            reference_date,
            resolved_territory,
            Decimal(str(contract.base_salary_amount)),
            Decimal(str(contract.weekly_reference_hours)),
        )
        return ContractSalaryEvaluationResult(
            contract=contract,
            reference_date=reference_date,
            status=ContractSalaryEvaluationStatus.SUCCESS,
            resolved_territory=resolved_territory,
            applicable_salary_minimum_result=result,
        )
