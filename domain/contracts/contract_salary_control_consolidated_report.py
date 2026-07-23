from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.contracts.contract_salary_alert import ContractSalaryAlertCollection
from domain.contracts.contract_salary_control_issue_history import ContractSalaryControlIssueHistory
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot
from domain.contracts.contract_salary_control_snapshot_comparison import ContractSalaryControlSnapshotComparison


@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsolidatedReport:
    """Assemblage immuable des résultats déjà produits par le contrôle salarial."""

    report_id: UUID
    generated_at: datetime
    reference: str
    version: int
    current_snapshot: ContractSalaryControlSnapshot
    previous_snapshot: Optional[ContractSalaryControlSnapshot]
    comparison: Optional[ContractSalaryControlSnapshotComparison]
    issue_history: Optional[ContractSalaryControlIssueHistory]
    alerts: Optional[ContractSalaryAlertCollection]
    generated_by: Optional[str] = None

    def __post_init__(self) -> None:
        if type(self.report_id) is not UUID:
            raise TypeError("report_id doit être un UUID strict.")
        if type(self.generated_at) is not datetime:
            raise TypeError("generated_at doit être un datetime strict.")
        if type(self.reference) is not str or not self.reference.strip():
            raise ValueError("reference doit être une chaîne non vide.")
        if type(self.version) is not int or self.version < 1:
            raise ValueError("version doit être un entier strict positif.")
        if type(self.current_snapshot) is not ContractSalaryControlSnapshot:
            raise TypeError("current_snapshot doit être un ContractSalaryControlSnapshot strict.")
        if self.previous_snapshot is not None and type(self.previous_snapshot) is not ContractSalaryControlSnapshot:
            raise TypeError("previous_snapshot doit être None ou un ContractSalaryControlSnapshot strict.")
        if self.comparison is not None and type(self.comparison) is not ContractSalaryControlSnapshotComparison:
            raise TypeError("comparison doit être None ou un ContractSalaryControlSnapshotComparison strict.")
        if self.issue_history is not None and type(self.issue_history) is not ContractSalaryControlIssueHistory:
            raise TypeError("issue_history doit être None ou un ContractSalaryControlIssueHistory strict.")
        if self.alerts is not None and type(self.alerts) is not ContractSalaryAlertCollection:
            raise TypeError("alerts doit être None ou un ContractSalaryAlertCollection strict.")
        if self.generated_by is not None and type(self.generated_by) is not str:
            raise TypeError("generated_by doit être None ou une chaîne stricte.")

    @property
    def has_previous_snapshot(self) -> bool:
        return self.previous_snapshot is not None
