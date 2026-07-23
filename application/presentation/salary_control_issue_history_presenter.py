from __future__ import annotations

from dataclasses import dataclass

from application.presentation.salary_control_presenter import format_french_date
from domain.contracts.contract_salary_control_issue_history import (
    ContractSalaryControlIssueEvolutionType,
    ContractSalaryControlIssueHistory,
    ContractSalaryControlIssueHistoryRow,
    ContractSalaryControlIssueStatus,
)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlIssueHistoryRowViewModel:
    contract_id_label: str
    employee_id_label: str
    issue_label: str
    status_label: str
    evolution_label: str
    before_reason_label: str
    after_reason_label: str
    before_snapshot_date_label: str
    after_snapshot_date_label: str


@dataclass(frozen=True, slots=True)
class ContractSalaryControlIssueHistoryViewModel:
    summary_lines: tuple[str, ...]
    rows: tuple[ContractSalaryControlIssueHistoryRowViewModel, ...]


class ContractSalaryControlIssueHistoryPresenter:
    FILTER_ALL = "all"
    FILTER_NEW = "new"
    FILTER_ONGOING = "ongoing"
    FILTER_RESOLVED = "resolved"

    def present(self, history: ContractSalaryControlIssueHistory, *, filter_key: str = FILTER_ALL) -> ContractSalaryControlIssueHistoryViewModel:
        if type(history) is not ContractSalaryControlIssueHistory:
            raise TypeError("history doit être un ContractSalaryControlIssueHistory strict.")
        filtered = tuple(row for row in history.rows if self.matches_filter(row, filter_key))
        return ContractSalaryControlIssueHistoryViewModel(
            summary_lines=(
                f"Date snapshot précédent : {format_french_date(history.before_reference_date)}",
                f"Date snapshot courant : {format_french_date(history.after_reference_date)}",
                f"Anomalies : {history.total_issues}",
                f"Nouvelles anomalies : {history.new_issues}",
                f"Anomalies résolues : {history.resolved_issues}",
                f"Anomalies persistantes : {history.ongoing_issues}",
            ),
            rows=tuple(self.row(row, history) for row in filtered),
        )

    def row(self, row: ContractSalaryControlIssueHistoryRow, history: ContractSalaryControlIssueHistory) -> ContractSalaryControlIssueHistoryRowViewModel:
        issue_code = row.issue_code_after or row.issue_code_before or "unknown"
        return ContractSalaryControlIssueHistoryRowViewModel(
            str(row.contract_id),
            str(row.employee_id or "Non renseigné"),
            issue_code,
            self.status_label(row.status),
            self.evolution_label(row.evolution_type),
            self.reason_label(row.failure_reason_before, row.issue_message_before),
            self.reason_label(row.failure_reason_after, row.issue_message_after),
            format_french_date(history.before_reference_date),
            format_french_date(history.after_reference_date),
        )

    def matches_filter(self, row: ContractSalaryControlIssueHistoryRow, filter_key: str) -> bool:
        if filter_key == self.FILTER_ALL:
            return True
        if filter_key == self.FILTER_NEW:
            return row.status is ContractSalaryControlIssueStatus.NEW
        if filter_key == self.FILTER_ONGOING:
            return row.status is ContractSalaryControlIssueStatus.ONGOING
        if filter_key == self.FILTER_RESOLVED:
            return row.status is ContractSalaryControlIssueStatus.RESOLVED
        raise ValueError(f"Filtre de suivi inconnu : {filter_key}.")

    def status_label(self, status):
        return {
            ContractSalaryControlIssueStatus.NEW: "Nouvelle",
            ContractSalaryControlIssueStatus.ONGOING: "Persistante",
            ContractSalaryControlIssueStatus.RESOLVED: "Résolue",
            ContractSalaryControlIssueStatus.UNKNOWN: "Inconnue",
        }[status]

    def evolution_label(self, evolution):
        return {
            ContractSalaryControlIssueEvolutionType.NEW: "Nouvelle anomalie",
            ContractSalaryControlIssueEvolutionType.ONGOING: "Toujours présente",
            ContractSalaryControlIssueEvolutionType.RESOLVED: "Anomalie corrigée",
            ContractSalaryControlIssueEvolutionType.REPLACED: "Remplacée par une autre anomalie",
            ContractSalaryControlIssueEvolutionType.SEVERITY_CHANGED: "Changement de gravité",
            ContractSalaryControlIssueEvolutionType.REASON_CHANGED: "Changement de motif",
            ContractSalaryControlIssueEvolutionType.STATUS_CHANGED: "Changement de statut",
            ContractSalaryControlIssueEvolutionType.UNKNOWN: "Évolution inconnue",
        }[evolution]

    def reason_label(self, failure_reason, issue_message):
        if failure_reason is not None:
            return failure_reason.value
        return issue_message or "Non renseigné"
