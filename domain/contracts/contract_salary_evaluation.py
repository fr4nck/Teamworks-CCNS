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

_ANNUAL_MINIMUM_ENGINE_MESSAGE = "Le contrôle du minimum le plus favorable est limité aux minima CCNS mensuels."
_ANNUAL_MINIMUM_CONTRACT_MESSAGE = "Le contrôle salarial direct du contrat est limité aux minima CCNS mensuels."


class ContractSalaryEvaluationFailureReason(str, Enum):
    CONTRACT_NOT_ACTIVE_ON_REFERENCE_DATE = "contract_not_active_on_reference_date"
    MISSING_CLASSIFICATION = "missing_classification"
    MISSING_REMUNERATION = "missing_remuneration"
    UNSUPPORTED_REMUNERATION_PERIODICITY = "unsupported_remuneration_periodicity"
    MISSING_WEEKLY_HOURS = "missing_weekly_hours"
    MISSING_TERRITORY = "missing_territory"
    ANNUAL_CCNS_MINIMUM_NOT_SUPPORTED = "annual_ccns_minimum_not_supported"
    HISTORICAL_FIXED_TERM_MISSING_END_DATE = "historical_fixed_term_missing_end_date"


def _strict_date(value: object, field_name: str = "reference_date") -> date:
    if type(value) is not date:
        raise TypeError(f"{field_name} doit être une date stricte.")
    return value


def _strict_uuid(value: object, field_name: str) -> UUID:
    if type(value) is not UUID:
        raise TypeError(f"{field_name} doit être un UUID strict.")
    return value


def _contract_identifier(contract: Contract) -> UUID:
    raw = contract.id
    if type(raw) is UUID:
        return raw
    if type(raw) is str:
        return UUID(raw)
    raise TypeError("L'identifiant du contrat doit être un UUID.")


def _employee_identifier(contract: Contract) -> Optional[UUID]:
    raw = contract.person_id
    if raw == "":
        return None
    if type(raw) is UUID:
        return raw
    if type(raw) is str:
        return UUID(raw)
    raise TypeError("L'identifiant du salarié doit être un UUID.")


@dataclass(frozen=True, slots=True)
class ContractSalaryEvaluationFailure:
    reason: ContractSalaryEvaluationFailureReason
    message: str
    contract_id: UUID
    employee_id: Optional[UUID]
    reference_date: date
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.reason) is not ContractSalaryEvaluationFailureReason:
            raise TypeError("reason doit être un ContractSalaryEvaluationFailureReason.")
        if type(self.message) is not str or not self.message.strip():
            raise ValueError("message est obligatoire.")
        object.__setattr__(self, "message", self.message.strip())
        _strict_uuid(self.contract_id, "contract_id")
        if self.employee_id is not None:
            _strict_uuid(self.employee_id, "employee_id")
        _strict_date(self.reference_date)
        _strict_uuid(self.id, "id")


@dataclass(frozen=True, slots=True)
class ContractSalaryEvaluationResult:
    contract: Contract
    reference_date: date
    successful: bool
    applicable_salary_minimum_result: Optional[ApplicableSalaryMinimumResult]
    failure: Optional[ContractSalaryEvaluationFailure]
    resolved_territory: Optional[SmicTerritory] = None
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.contract) is not Contract:
            raise TypeError("contract doit être un Contract.")
        _strict_date(self.reference_date)
        if type(self.successful) is not bool:
            raise TypeError("successful doit être un bool strict.")
        if self.applicable_salary_minimum_result is not None and type(self.applicable_salary_minimum_result) is not ApplicableSalaryMinimumResult:
            raise TypeError("applicable_salary_minimum_result doit être un ApplicableSalaryMinimumResult.")
        if self.failure is not None and type(self.failure) is not ContractSalaryEvaluationFailure:
            raise TypeError("failure doit être un ContractSalaryEvaluationFailure.")
        if self.resolved_territory is not None and type(self.resolved_territory) is not SmicTerritory:
            raise TypeError("resolved_territory doit être None ou un SmicTerritory.")
        _strict_uuid(self.id, "id")
        if self.successful:
            if self.applicable_salary_minimum_result is None or self.failure is not None:
                raise ValueError("Un résultat réussi doit contenir uniquement le résultat salarial.")
            if self.resolved_territory is None:
                raise ValueError("Un résultat réussi doit conserver le territoire résolu.")
            result = self.applicable_salary_minimum_result
            if result.reference_date != self.reference_date:
                raise ValueError("Le résultat salarial est incohérent avec la date de référence.")
            if result.classification_group != self.contract.ccns_classification:
                raise ValueError("Le résultat salarial est incohérent avec la classification du contrat.")
            if result.remuneration_amount != self.contract.monthly_gross_salary_amount:
                raise ValueError("Le résultat salarial est incohérent avec la rémunération du contrat.")
            if result.weekly_hours != self.contract.weekly_hours:
                raise ValueError("Le résultat salarial est incohérent avec la durée du contrat.")
            if result.territory is not self.resolved_territory:
                raise ValueError("Le résultat salarial est incohérent avec le territoire résolu.")
            if self.contract.smic_territory is not None and self.resolved_territory is not self.contract.smic_territory:
                raise ValueError("Le territoire résolu est incohérent avec le territoire du contrat.")
        else:
            if self.applicable_salary_minimum_result is not None or self.failure is None:
                raise ValueError("Un résultat refusé doit contenir uniquement un échec métier.")
            if self.failure.contract_id != _contract_identifier(self.contract):
                raise ValueError("L'échec est incohérent avec l'identifiant du contrat.")
            if self.failure.reference_date != self.reference_date:
                raise ValueError("L'échec est incohérent avec la date de référence.")
            if self.failure.reason is ContractSalaryEvaluationFailureReason.MISSING_TERRITORY and self.resolved_territory is not None:
                raise ValueError("Un échec pour territoire absent ne doit pas conserver de territoire résolu.")

    def is_successful(self) -> bool:
        return self.successful

    def has_failure(self) -> bool:
        return self.failure is not None

    def result(self) -> ApplicableSalaryMinimumResult:
        if not self.successful or self.applicable_salary_minimum_result is None:
            raise ValueError("L’évaluation salariale du contrat n’a pas abouti.")
        return self.applicable_salary_minimum_result

    def failure_reason(self) -> Optional[ContractSalaryEvaluationFailureReason]:
        return self.failure.reason if self.failure is not None else None

    def contract_id(self) -> UUID:
        return _contract_identifier(self.contract)

    def employee_id(self) -> Optional[UUID]:
        return _employee_identifier(self.contract)


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
        *,
        territory: Optional[SmicTerritory] = None,
    ) -> ContractSalaryEvaluationResult:
        if type(contract) is not Contract:
            raise TypeError("contract doit être un Contract.")
        _strict_date(reference_date)
        if territory is not None and type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")

        if contract.legacy_salary_control_failure_reason == "CONTRAT_A_DUREE_DETERMINEE_SANS_DATE_FIN":
            return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.HISTORICAL_FIXED_TERM_MISSING_END_DATE, "Le contrat historique à durée déterminée ne possède pas de date de fin et ne peut pas être évalué comme un CDI.")

        if not contract.is_applicable_on(reference_date):
            return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.CONTRACT_NOT_ACTIVE_ON_REFERENCE_DATE, "Le contrat n’est pas applicable à la date de référence.")
        classification = contract.ccns_classification
        if type(classification) is not CCNSClassification:
            return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION, "Le contrat ne possède pas de classification CCNS exploitable.")
        remuneration = contract.monthly_gross_salary_amount
        if remuneration is None:
            return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION, "Le contrat ne possède pas de rémunération exploitable.")
        if type(remuneration) is not Decimal:
            return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION, "Le contrat ne possède pas de rémunération exploitable.")
        if contract.salary_unit != "monthly":
            return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.UNSUPPORTED_REMUNERATION_PERIODICITY, "Seule une rémunération brute mensuelle peut être évaluée dans ce ticket.")
        weekly_hours = contract.weekly_hours
        if type(weekly_hours) is not Decimal or weekly_hours <= Decimal("0.00"):
            return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.MISSING_WEEKLY_HOURS, "Le contrat ne possède pas de durée hebdomadaire exploitable.")
        resolved_territory = contract.smic_territory if contract.smic_territory is not None else territory
        if resolved_territory is None:
            return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.MISSING_TERRITORY, "Le contrat ne possède pas de territoire d’exécution exploitable.")
        try:
            result = self.applicable_salary_minimum_service.evaluate(classification, reference_date, resolved_territory, remuneration, weekly_hours)
        except ValueError as exc:
            if str(exc) == _ANNUAL_MINIMUM_ENGINE_MESSAGE:
                return self._failure(contract, reference_date, ContractSalaryEvaluationFailureReason.ANNUAL_CCNS_MINIMUM_NOT_SUPPORTED, _ANNUAL_MINIMUM_CONTRACT_MESSAGE, resolved_territory)
            raise
        return ContractSalaryEvaluationResult(contract, reference_date, True, result, None, resolved_territory)

    def _failure(
        self,
        contract: Contract,
        reference_date: date,
        reason: ContractSalaryEvaluationFailureReason,
        message: str,
        resolved_territory: Optional[SmicTerritory] = None,
    ) -> ContractSalaryEvaluationResult:
        failure = ContractSalaryEvaluationFailure(reason, message, _contract_identifier(contract), _employee_identifier(contract), reference_date)
        return ContractSalaryEvaluationResult(contract, reference_date, False, None, failure, resolved_territory)
