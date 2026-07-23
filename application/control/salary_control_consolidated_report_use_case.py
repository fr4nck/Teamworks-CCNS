from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional
from uuid import UUID, uuid4

from domain.contracts.contract_salary_alert import GenerateContractSalaryAlertsService
from domain.contracts.contract_salary_control_consolidated_report import ContractSalaryControlConsolidatedReport
from domain.contracts.contract_salary_control_issue_history import TrackContractSalaryControlIssuesService
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot
from domain.contracts.contract_salary_control_snapshot_comparison import CompareContractSalaryControlSnapshotsService


@dataclass(frozen=True, slots=True)
class BuildContractSalaryControlConsolidatedReportUseCase:
    report_id_factory: Callable[[], UUID] = uuid4
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)
    comparison_service: CompareContractSalaryControlSnapshotsService = field(default_factory=CompareContractSalaryControlSnapshotsService)
    issue_service: TrackContractSalaryControlIssuesService = field(default_factory=TrackContractSalaryControlIssuesService)
    alert_service: GenerateContractSalaryAlertsService = field(default_factory=GenerateContractSalaryAlertsService)

    def execute(
        self,
        current_snapshot: ContractSalaryControlSnapshot,
        previous_snapshot: Optional[ContractSalaryControlSnapshot] = None,
        *,
        generated_by: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> ContractSalaryControlConsolidatedReport:
        if type(current_snapshot) is not ContractSalaryControlSnapshot:
            raise TypeError("current_snapshot doit être un ContractSalaryControlSnapshot strict.")
        if previous_snapshot is not None and type(previous_snapshot) is not ContractSalaryControlSnapshot:
            raise TypeError("previous_snapshot doit être None ou un ContractSalaryControlSnapshot strict.")
        comparison = None
        issue_history = None
        alerts = None
        if previous_snapshot is not None:
            comparison = self.comparison_service.compare(previous_snapshot, current_snapshot)
            issue_history = self.issue_service.track(previous_snapshot, current_snapshot)
            alerts = self.alert_service.generate(current_snapshot, comparison, issue_history)
        return ContractSalaryControlConsolidatedReport(
            report_id=self.report_id_factory(),
            generated_at=self.clock(),
            reference=reference or f"controle-salarial-{current_snapshot.reference_date.isoformat()}",
            version=1,
            current_snapshot=current_snapshot,
            previous_snapshot=previous_snapshot,
            comparison=comparison,
            issue_history=issue_history,
            alerts=alerts,
            generated_by=generated_by,
        )
