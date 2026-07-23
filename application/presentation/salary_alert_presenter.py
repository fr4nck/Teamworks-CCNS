from __future__ import annotations

from dataclasses import dataclass

from application.presentation.salary_control_presenter import format_euro_amount, format_french_date
from domain.contracts.contract_salary_alert import ContractSalaryAlert, ContractSalaryAlertCollection, ContractSalaryAlertSeverity, ContractSalaryAlertType


@dataclass(frozen=True, slots=True)
class ContractSalaryAlertRowViewModel:
    employee_label: str
    contract_label: str
    severity_label: str
    type_label: str
    summary: str
    detail: str
    date_label: str


@dataclass(frozen=True, slots=True)
class ContractSalaryAlertViewModel:
    total_count: int
    critical_count: int
    warning_count: int
    info_count: int
    summary_lines: tuple[str, ...]
    rows: tuple[ContractSalaryAlertRowViewModel, ...]


class ContractSalaryAlertPresenter:
    FILTER_ALL = "all"
    FILTER_CRITICAL = "critical"
    FILTER_WARNING = "warning"
    FILTER_INFO = "info"
    FILTER_NON_COMPLIANCE = "non_compliance"
    FILTER_NEW_ANOMALIES = "new_anomalies"
    FILTER_RESOLVED = "resolved"

    SUMMARY_LABELS = {
        "new_non_compliant_contract": "Nouveau contrat non conforme",
        "new_compliant_contract": "Nouveau contrat conforme",
        "removed_contract": "Contrat supprimé",
        "contract_became_compliant": "Contrat redevenu conforme",
        "contract_became_non_compliant": "Contrat devenu non conforme",
        "contract_not_evaluated": "Contrat non évalué",
        "minimum_increased": "Minimum conventionnel augmenté",
        "salary_decreased": "Baisse de rémunération",
        "shortfall_increased": "Écart salarial aggravé",
        "new_anomaly": "Nouvelle anomalie",
        "persistent_anomaly": "Anomalie persistante",
        "resolved_anomaly": "Anomalie résolue",
    }
    DETAIL_LABELS = {
        "new_contract_requires_action": "Le dernier snapshot signale un nouveau contrat nécessitant une action.",
        "new_contract_no_action": "Le dernier snapshot signale un nouveau contrat conforme.",
        "contract_absent_from_current_snapshot": "Le contrat était présent dans le snapshot précédent et absent du dernier.",
        "non_compliance_resolved": "La comparaison indique un retour à la conformité.",
        "contract_requires_action": "La comparaison indique une non-conformité dans le dernier snapshot.",
        "missing_data_or_rule_prevents_evaluation": "Le dernier snapshot ne permet pas d'évaluer le contrat.",
        "applicable_minimum_above_previous_snapshot": "Le minimum applicable est supérieur à celui du snapshot précédent.",
        "remuneration_below_previous_snapshot": "La rémunération est inférieure à celle du snapshot précédent.",
        "shortfall_above_previous_snapshot": "L'écart salarial est supérieur à celui du snapshot précédent.",
        "anomaly_absent_from_previous_snapshot": "Le suivi des anomalies classe cette anomalie comme nouvelle.",
        "anomaly_still_present": "Le suivi des anomalies classe cette anomalie comme persistante.",
        "anomaly_absent_from_current_snapshot": "Le suivi des anomalies classe cette anomalie comme résolue.",
    }

    def present(self, collection: ContractSalaryAlertCollection, *, filter_key: str = FILTER_ALL) -> ContractSalaryAlertViewModel:
        if type(collection) is not ContractSalaryAlertCollection:
            raise TypeError("collection doit être une ContractSalaryAlertCollection stricte.")
        filtered = tuple(alert for alert in collection.alerts if self.matches_filter(alert, filter_key))
        return ContractSalaryAlertViewModel(
            collection.total_count,
            collection.critical_count,
            collection.warning_count,
            collection.info_count,
            (f"Alertes : {collection.total_count}", f"Critiques : {collection.critical_count}", f"Avertissements : {collection.warning_count}", f"Informations : {collection.info_count}"),
            tuple(self.row(alert) for alert in filtered),
        )

    def matches_filter(self, alert: ContractSalaryAlert, filter_key: str) -> bool:
        if filter_key == self.FILTER_ALL:
            return True
        if filter_key == self.FILTER_CRITICAL:
            return alert.severity is ContractSalaryAlertSeverity.CRITICAL
        if filter_key == self.FILTER_WARNING:
            return alert.severity is ContractSalaryAlertSeverity.WARNING
        if filter_key == self.FILTER_INFO:
            return alert.severity is ContractSalaryAlertSeverity.INFO
        if filter_key == self.FILTER_NON_COMPLIANCE:
            return alert.alert_type is ContractSalaryAlertType.NON_COMPLIANT_CONTRACT
        if filter_key == self.FILTER_NEW_ANOMALIES:
            return alert.alert_type is ContractSalaryAlertType.NEW_ANOMALY
        if filter_key == self.FILTER_RESOLVED:
            return alert.summary_key in ("resolved_anomaly", "contract_became_compliant")
        raise ValueError(f"Filtre d'alertes inconnu : {filter_key}.")

    def row(self, alert: ContractSalaryAlert) -> ContractSalaryAlertRowViewModel:
        detail = self.DETAIL_LABELS.get(alert.detail_key, alert.detail_key)
        if alert.amount is not None:
            detail = f"{detail} Montant : {format_euro_amount(alert.amount)}."
        if alert.issue_code is not None:
            detail = f"{detail} Anomalie : {alert.issue_code}."
        return ContractSalaryAlertRowViewModel(str(alert.employee_id or "Non renseigné"), str(alert.contract_id), self.severity_label(alert.severity), self.type_label(alert.alert_type), self.SUMMARY_LABELS.get(alert.summary_key, alert.summary_key), detail, format_french_date(alert.alert_date))

    def severity_label(self, severity):
        return {ContractSalaryAlertSeverity.CRITICAL: "Critique", ContractSalaryAlertSeverity.WARNING: "Avertissement", ContractSalaryAlertSeverity.INFO: "Information"}[severity]

    def type_label(self, alert_type):
        return {value: value.name.replace("_", " ").title() for value in ContractSalaryAlertType}[alert_type]
