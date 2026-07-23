from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from application.presentation.salary_control_presenter import format_euro_amount, format_french_date
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_snapshot_comparison import ContractSalaryControlSnapshotChangeType, ContractSalaryControlSnapshotComparison, ContractSalaryControlSnapshotComparisonRow


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshotComparisonRowViewModel:
    contract_id_label: str
    employee_id_label: str
    status_before_label: str
    status_after_label: str
    change_type_label: str
    remuneration_before_label: str
    remuneration_after_label: str
    remuneration_delta_label: str
    minimum_before_label: str
    minimum_after_label: str
    minimum_delta_label: str
    shortfall_before_label: str
    shortfall_after_label: str
    shortfall_delta_label: str


@dataclass(frozen=True, slots=True)
class ContractSalaryControlSnapshotComparisonViewModel:
    summary_lines: tuple[str, ...]
    rows: tuple[ContractSalaryControlSnapshotComparisonRowViewModel, ...]
    conclusion_label: str


class ContractSalaryControlSnapshotComparisonPresenter:
    FILTER_ALL = "all"
    FILTER_IMPROVEMENTS = "improvements"
    FILTER_DEGRADATIONS = "degradations"
    FILTER_NEW_CONTRACTS = "new_contracts"
    FILTER_REMOVED_CONTRACTS = "removed_contracts"
    FILTER_STATUS_CHANGES = "status_changes"
    FILTER_SHORTFALL_CHANGED = "shortfall_changed"
    FILTER_UNCHANGED = "unchanged"

    def present(self, comparison: ContractSalaryControlSnapshotComparison, *, filter_key: str = FILTER_ALL) -> ContractSalaryControlSnapshotComparisonViewModel:
        if type(comparison) is not ContractSalaryControlSnapshotComparison:
            raise TypeError("comparison doit être un ContractSalaryControlSnapshotComparison strict.")
        filtered = tuple(row for row in comparison.rows if self.matches_filter(row, filter_key))
        conclusion = self.conclusion_label(comparison)
        return ContractSalaryControlSnapshotComparisonViewModel(
            summary_lines=(
                f"Date de référence avant : {format_french_date(comparison.before_reference_date)}",
                f"Date de référence après : {format_french_date(comparison.after_reference_date)}",
                f"Date d'exécution avant : {comparison.before_executed_at.isoformat(timespec='seconds')}",
                f"Date d'exécution après : {comparison.after_executed_at.isoformat(timespec='seconds')}",
                f"Contrats avant : {comparison.total_before}",
                f"Contrats après : {comparison.total_after}",
                f"Nouveaux contrats : {comparison.new_contracts}",
                f"Contrats absents : {comparison.removed_contracts}",
                f"Devenus conformes : {comparison.became_compliant}",
                f"Devenus non conformes : {comparison.became_non_compliant}",
                f"Devenus non évaluables : {comparison.became_not_evaluated}",
                f"Écart total avant : {format_euro_amount(comparison.total_shortfall_before)}",
                f"Écart total après : {format_euro_amount(comparison.total_shortfall_after)}",
                f"Évolution de l'écart total : {self._delta(comparison.total_shortfall_delta)}",
                f"Conclusion : {conclusion}",
            ),
            rows=tuple(self.row(row) for row in filtered),
            conclusion_label=conclusion,
        )

    def row(self, row: ContractSalaryControlSnapshotComparisonRow) -> ContractSalaryControlSnapshotComparisonRowViewModel:
        return ContractSalaryControlSnapshotComparisonRowViewModel(
            str(row.contract_id), str(row.employee_id_after or row.employee_id_before or "Non renseigné"),
            self.status_label(row.status_before), self.status_label(row.status_after), self.change_type_label(row.change_type),
            self._amount(row.remuneration_amount_before), self._amount(row.remuneration_amount_after), self._delta(row.remuneration_delta),
            self._amount(row.applicable_minimum_amount_before), self._amount(row.applicable_minimum_amount_after), self._delta(row.minimum_delta),
            self._amount(row.shortfall_amount_before), self._amount(row.shortfall_amount_after), self._delta(row.shortfall_delta),
        )

    def matches_filter(self, row: ContractSalaryControlSnapshotComparisonRow, filter_key: str) -> bool:
        if filter_key == self.FILTER_ALL:
            return True
        if filter_key == self.FILTER_IMPROVEMENTS:
            return row.change_type is ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT or row.shortfall_delta < Decimal("0.00")
        if filter_key == self.FILTER_DEGRADATIONS:
            return row.change_type in (ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT, ContractSalaryControlSnapshotChangeType.BECAME_NOT_EVALUATED) or row.shortfall_delta > Decimal("0.00")
        if filter_key == self.FILTER_NEW_CONTRACTS:
            return row.change_type is ContractSalaryControlSnapshotChangeType.NEW_CONTRACT
        if filter_key == self.FILTER_REMOVED_CONTRACTS:
            return row.change_type is ContractSalaryControlSnapshotChangeType.REMOVED_CONTRACT
        if filter_key == self.FILTER_STATUS_CHANGES:
            return row.status_before != row.status_after
        if filter_key == self.FILTER_SHORTFALL_CHANGED:
            return row.shortfall_delta != Decimal("0.00")
        if filter_key == self.FILTER_UNCHANGED:
            return row.change_type is ContractSalaryControlSnapshotChangeType.UNCHANGED
        raise ValueError(f"Filtre de comparaison inconnu : {filter_key}.")

    def conclusion_label(self, comparison):
        if comparison.unchanged:
            return "Aucun changement"
        if comparison.improved and comparison.degraded:
            return "Améliorations et dégradations simultanées"
        if comparison.improved:
            return "Amélioration globale"
        if comparison.degraded:
            return "Dégradation globale"
        return "Changements sans conclusion automatique"

    def change_type_label(self, change_type):
        return {
            ContractSalaryControlSnapshotChangeType.NEW_CONTRACT: "Nouveau contrat",
            ContractSalaryControlSnapshotChangeType.REMOVED_CONTRACT: "Contrat absent du second contrôle",
            ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT: "Devenu conforme",
            ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT: "Devenu non conforme",
            ContractSalaryControlSnapshotChangeType.BECAME_NOT_EVALUATED: "Devenu non évaluable",
            ContractSalaryControlSnapshotChangeType.REMAINS_COMPLIANT: "Toujours conforme",
            ContractSalaryControlSnapshotChangeType.REMAINS_NON_COMPLIANT: "Toujours non conforme",
            ContractSalaryControlSnapshotChangeType.REMAINS_NOT_EVALUATED: "Toujours non évaluable",
            ContractSalaryControlSnapshotChangeType.STATUS_CHANGED_OTHER: "Statut modifié",
            ContractSalaryControlSnapshotChangeType.UNCHANGED: "Inchangé",
        }[change_type]

    def status_label(self, status):
        if status is None:
            return "Absent"
        return {ContractSalaryControlStatus.COMPLIANT: "Conforme", ContractSalaryControlStatus.NON_COMPLIANT: "Non conforme", ContractSalaryControlStatus.NOT_EVALUATED: "Non évaluable"}[status]

    def _amount(self, amount):
        return "Non disponible" if amount is None else format_euro_amount(amount)

    def _delta(self, amount):
        prefix = "+" if amount > Decimal("0.00") else ""
        return prefix + format_euro_amount(amount)
