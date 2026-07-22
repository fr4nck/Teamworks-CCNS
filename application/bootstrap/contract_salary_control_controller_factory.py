from __future__ import annotations

from dataclasses import dataclass

from application.control import ConsultContractSalaryControlUseCase, ContractSalaryControlController
from application.presentation import ContractSalaryControlPresenter
from domain.contracts import (
    ContractSalaryBatchAuditService,
    ContractSalaryBatchEvaluationService,
    ContractSalaryControlConsultationService,
    ContractSalaryControlProjectionService,
    ContractSalaryControlQueryService,
    ContractSalaryControlService,
    ContractSalaryEvaluationService,
)
from domain.convention import (
    ApplicableSalaryMinimumService,
    SalaryGridCatalog,
    SalaryMinimumAuditService,
    SalaryMinimumBatchAuditService,
    SalaryMinimumComplianceService,
    SmicCatalog,
)
from infrastructure.repositories import ContractRepository, ContractRepositorySalaryControlProvider


@dataclass(frozen=True, slots=True)
class ContractSalaryControlControllerFactory:
    """Point de composition applicatif du contrôleur de contrôle salarial."""

    def create(
        self,
        *,
        contracts_repository: ContractRepository,
        salary_grid_catalog: SalaryGridCatalog,
        smic_catalog: SmicCatalog,
    ) -> ContractSalaryControlController:
        """Construit un contrôleur prêt à exécuter une demande de contrôle salarial."""

        if type(contracts_repository) is not ContractRepository:
            raise TypeError("contracts_repository doit être un ContractRepository strict.")
        if type(salary_grid_catalog) is not SalaryGridCatalog:
            raise TypeError("salary_grid_catalog doit être un SalaryGridCatalog strict.")
        if type(smic_catalog) is not SmicCatalog:
            raise TypeError("smic_catalog doit être un SmicCatalog strict.")

        salary_minimum_compliance_service = SalaryMinimumComplianceService(salary_grid_catalog)
        applicable_salary_minimum_service = ApplicableSalaryMinimumService(
            salary_minimum_compliance_service,
            smic_catalog,
        )
        contract_salary_evaluation_service = ContractSalaryEvaluationService(
            applicable_salary_minimum_service,
        )
        contract_salary_batch_evaluation_service = ContractSalaryBatchEvaluationService(
            contract_salary_evaluation_service,
        )
        salary_minimum_audit_service = SalaryMinimumAuditService()
        salary_minimum_batch_audit_service = SalaryMinimumBatchAuditService(
            salary_minimum_audit_service,
        )
        contract_salary_batch_audit_service = ContractSalaryBatchAuditService(
            contract_salary_batch_evaluation_service,
            salary_minimum_batch_audit_service,
        )
        contract_salary_control_projection_service = ContractSalaryControlProjectionService()
        contract_salary_control_service = ContractSalaryControlService(
            contract_salary_batch_audit_service,
            contract_salary_control_projection_service,
        )
        contract_salary_control_query_service = ContractSalaryControlQueryService()
        consultation_service = ContractSalaryControlConsultationService(
            contract_salary_control_service,
            contract_salary_control_query_service,
        )
        contract_provider = ContractRepositorySalaryControlProvider(contracts_repository)
        use_case = ConsultContractSalaryControlUseCase(contract_provider, consultation_service)
        presenter = ContractSalaryControlPresenter()
        return ContractSalaryControlController(use_case, presenter)
