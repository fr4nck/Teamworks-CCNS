from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO

from domain.contracts.contract_salary_control_consolidated_report import ContractSalaryControlConsolidatedReport

_MIME_TYPE = "text/csv; charset=utf-8"
_HEADERS = ("section", "reference_date", "contract_id", "employee_id", "status", "classification_code", "remuneration_amount", "applicable_minimum_amount", "minimum_source", "shortfall_amount", "territory", "failure_reason", "issue_code", "issue_message")
_ABSENT = "__ABSENT__"

@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsolidatedCsvExport:
    content: str
    suggested_filename: str
    mime_type: str = _MIME_TYPE

@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsolidatedCsvExporter:
    def export(self, report: ContractSalaryControlConsolidatedReport) -> ContractSalaryControlConsolidatedCsvExport:
        if type(report) is not ContractSalaryControlConsolidatedReport:
            raise TypeError("report doit être un ContractSalaryControlConsolidatedReport strict.")
        s = StringIO(newline="")
        w = csv.writer(s, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
        w.writerow(("section", "key", "value"))
        w.writerow(("general", "report_id", report.report_id))
        w.writerow(("general", "generated_at", report.generated_at.isoformat()))
        w.writerow(("general", "reference", report.reference))
        w.writerow(("general", "version", report.version))
        w.writerow(("general", "generated_by", report.generated_by or _ABSENT))
        for key in ("total_contracts", "compliant_contracts", "non_compliant_contracts", "not_evaluated_contracts", "total_shortfall_amount"):
            w.writerow(("summary", key, _fmt(getattr(report.current_snapshot, key))))
        if report.comparison is not None:
            for key in ("new_contracts", "removed_contracts", "became_compliant", "became_non_compliant", "became_not_evaluated", "total_shortfall_delta"):
                w.writerow(("comparison", key, _fmt(getattr(report.comparison, key))))
        if report.issue_history is not None:
            w.writerow(("issues", "new", report.issue_history.new_issues)); w.writerow(("issues", "persistent", report.issue_history.ongoing_issues)); w.writerow(("issues", "resolved", report.issue_history.resolved_issues))
        if report.alerts is not None:
            w.writerow(("alerts", "critical", report.alerts.critical_count)); w.writerow(("alerts", "warnings", report.alerts.warning_count)); w.writerow(("alerts", "information", report.alerts.info_count))
        w.writerow(())
        w.writerow(_HEADERS)
        for section, snapshot in (("previous", report.previous_snapshot), ("current", report.current_snapshot)):
            if snapshot is None: continue
            for row in snapshot.rows:
                w.writerow((section, snapshot.reference_date.isoformat(), row.contract_id, row.employee_id or _ABSENT, row.status.value, row.classification_code or _ABSENT, _fmt(row.remuneration_amount), _fmt(row.applicable_minimum_amount), _enum(row.minimum_source), _fmt(row.shortfall_amount), _enum(row.territory), _enum(row.failure_reason), row.issue_code or _ABSENT, row.issue_message or _ABSENT))
        return ContractSalaryControlConsolidatedCsvExport(s.getvalue(), f"rapport-consolide-controle-salarial-{report.current_snapshot.reference_date.isoformat()}.csv")

def _fmt(v): return _ABSENT if v is None else format(v, "f") if hasattr(v, "as_tuple") else str(v)
def _enum(v): return _ABSENT if v is None else v.value
