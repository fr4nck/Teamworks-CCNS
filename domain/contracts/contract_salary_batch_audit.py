from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, Optional
from uuid import UUID, uuid4

from domain.contracts.contract import Contract
from domain.contracts.contract_salary_batch_evaluation import (
    ContractSalaryBatchEvaluationResult,
    ContractSalaryBatchEvaluationService,
)
from domain.contracts.contract_salary_evaluation import (
    ContractSalaryEvaluationFailure,
    ContractSalaryEvaluationResult,
    _strict_date,
    _strict_uuid,
)
from domain.convention import (
    SalaryMinimumAuditIssue,
    SalaryMinimumAuditResult,
    SalaryMinimumBatchAuditResult,
    SalaryMinimumBatchAuditService,
)
from domain.convention.smic import SmicTerritory


@dataclass(frozen=True, slots=True)
class ContractSalaryBatchAuditResult:
    """Synthèse immutable d'un audit salarial en lot à partir de contrats.

    ``valid`` est volontairement plus strict que celui de
    ``SalaryMinimumBatchAuditResult`` : le lot contrat est valide uniquement si
    aucun contrat n'est refusé fonctionnellement et si aucun audit salarial ne
    produit d'anomalie.
    """

    batch_evaluation_result: ContractSalaryBatchEvaluationResult
    batch_audit_result: SalaryMinimumBatchAuditResult
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.batch_evaluation_result) is not ContractSalaryBatchEvaluationResult:
            raise TypeError("batch_evaluation_result doit être un ContractSalaryBatchEvaluationResult.")
        if type(self.batch_audit_result) is not SalaryMinimumBatchAuditResult:
            raise TypeError("batch_audit_result doit être un SalaryMinimumBatchAuditResult.")
        _strict_uuid(self.id, "id")
        self._validate_consistency()

    def _validate_consistency(self) -> None:
        successful = self.batch_evaluation_result.successful_evaluations()
        items = self.batch_audit_result.items
        audit_results = self.batch_audit_result.audit_results
        if len(successful) != len(items):
            raise ValueError("Le nombre d'évaluations réussies doit correspondre au nombre d'items audités.")
        if len(successful) != len(audit_results):
            raise ValueError("Le nombre d'évaluations réussies doit correspondre au nombre de résultats d'audit.")
        failed_ids = {evaluation.contract_id() for evaluation in self.batch_evaluation_result.failed_evaluations()}
        audited_ids: set[UUID] = set()
        for evaluation, item, audit_result in zip(successful, items, audit_results):
            contract_id = evaluation.contract_id()
            employee_id = evaluation.employee_id()
            if item.compliance_result is not evaluation.result():
                raise ValueError("Chaque item audité doit reprendre l'instance de résultat salarial de l'évaluation correspondante.")
            if item.contract_id != contract_id or item.employee_id != employee_id:
                raise ValueError("Les UUID contrat et salarié de l'item sont incohérents avec l'évaluation.")
            if audit_result.compliance_result is not evaluation.result():
                raise ValueError("Chaque résultat d'audit doit reprendre l'instance de résultat salarial de l'évaluation correspondante.")
            if audit_result.contract_id != contract_id or audit_result.employee_id != employee_id:
                raise ValueError("Les UUID contrat et salarié du résultat d'audit sont incohérents avec l'évaluation.")
            if contract_id in failed_ids:
                raise ValueError("Une évaluation échouée ne doit pas produire de résultat d'audit.")
            if contract_id in audited_ids:
                raise ValueError("Un contrat ne doit pas produire plusieurs résultats d'audit.")
            audited_ids.add(contract_id)
        expected_ids = {evaluation.contract_id() for evaluation in successful}
        if audited_ids != expected_ids:
            raise ValueError("Un résultat d'audit existe sans évaluation réussie correspondante.")
        if self.total_contract_count != self.evaluated_contract_count + self.failed_contract_count:
            raise ValueError("Les compteurs d'évaluation du lot sont incohérents.")
        if self.evaluated_contract_count != self.compliant_contract_count + self.non_compliant_contract_count:
            raise ValueError("Les compteurs d'audit du lot sont incohérents.")
        if self.total_shortfall_amount is not self.batch_audit_result.total_shortfall_amount:
            raise ValueError("total_shortfall_amount doit provenir du résultat d'audit en lot.")

    @property
    def reference_date(self):
        return self.batch_evaluation_result.reference_date

    @property
    def total_contract_count(self) -> int:
        return self.batch_evaluation_result.total_count

    @property
    def evaluated_contract_count(self) -> int:
        return self.batch_evaluation_result.successful_count

    @property
    def failed_contract_count(self) -> int:
        return self.batch_evaluation_result.failed_count

    @property
    def compliant_contract_count(self) -> int:
        return self.batch_audit_result.compliant_count

    @property
    def non_compliant_contract_count(self) -> int:
        return self.batch_audit_result.non_compliant_count

    @property
    def issue_count(self) -> int:
        return self.batch_audit_result.issue_count()

    @property
    def total_shortfall_amount(self) -> Decimal:
        return self.batch_audit_result.total_shortfall_amount

    @property
    def valid(self) -> bool:
        return self.batch_audit_result.is_valid() and self.failed_contract_count == 0

    @property
    def evaluations(self) -> tuple[ContractSalaryEvaluationResult, ...]:
        return self.batch_evaluation_result.evaluations

    @property
    def failures(self) -> tuple[ContractSalaryEvaluationFailure, ...]:
        return self.batch_evaluation_result.failures()

    @property
    def audit_results(self) -> tuple[SalaryMinimumAuditResult, ...]:
        return self.batch_audit_result.audit_results

    @property
    def issues(self) -> tuple[SalaryMinimumAuditIssue, ...]:
        return self.batch_audit_result.issues

    def successful_evaluations(self) -> tuple[ContractSalaryEvaluationResult, ...]:
        return self.batch_evaluation_result.successful_evaluations()

    def failed_evaluations(self) -> tuple[ContractSalaryEvaluationResult, ...]:
        return self.batch_evaluation_result.failed_evaluations()

    def evaluation_for_contract(self, contract_id: UUID) -> Optional[ContractSalaryEvaluationResult]:
        return self.batch_evaluation_result.evaluation_for_contract(_strict_uuid(contract_id, "contract_id"))

    def evaluations_for_employee(self, employee_id: UUID) -> tuple[ContractSalaryEvaluationResult, ...]:
        return self.batch_evaluation_result.evaluations_for_employee(_strict_uuid(employee_id, "employee_id"))

    def audit_result_for_contract(self, contract_id: UUID) -> Optional[SalaryMinimumAuditResult]:
        contract = _strict_uuid(contract_id, "contract_id")
        matches = self.batch_audit_result.results_for_contract(contract)
        if len(matches) > 1:
            raise ValueError("Plusieurs résultats d'audit correspondent au même contract_id.")
        return matches[0] if matches else None

    def issues_for_contract(self, contract_id: UUID) -> tuple[SalaryMinimumAuditIssue, ...]:
        return self.batch_audit_result.issues_for_contract(_strict_uuid(contract_id, "contract_id"))

    def issues_for_employee(self, employee_id: UUID) -> tuple[SalaryMinimumAuditIssue, ...]:
        return self.batch_audit_result.issues_for_employee(_strict_uuid(employee_id, "employee_id"))


@dataclass(frozen=True, slots=True)
class ContractSalaryBatchAuditService:
    contract_salary_batch_evaluation_service: ContractSalaryBatchEvaluationService
    salary_minimum_batch_audit_service: SalaryMinimumBatchAuditService

    def __post_init__(self) -> None:
        if type(self.contract_salary_batch_evaluation_service) is not ContractSalaryBatchEvaluationService:
            raise TypeError("contract_salary_batch_evaluation_service doit être un ContractSalaryBatchEvaluationService.")
        if type(self.salary_minimum_batch_audit_service) is not SalaryMinimumBatchAuditService:
            raise TypeError("salary_minimum_batch_audit_service doit être un SalaryMinimumBatchAuditService.")

    def audit(
        self,
        contracts: Iterable[Contract],
        reference_date,
        *,
        territory: Optional[SmicTerritory] = None,
    ) -> ContractSalaryBatchAuditResult:
        _strict_date(reference_date)
        if territory is not None and type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        batch_evaluation_result = self.contract_salary_batch_evaluation_service.evaluate(
            contracts,
            reference_date,
            territory=territory,
        )
        items = batch_evaluation_result.to_salary_minimum_audit_items()
        batch_audit_result = self.salary_minimum_batch_audit_service.audit(items)
        return ContractSalaryBatchAuditResult(batch_evaluation_result, batch_audit_result)
