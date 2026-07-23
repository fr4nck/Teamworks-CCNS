from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from domain.contracts.contract_salary_alert import ContractSalaryAlert, ContractSalaryAlertCollection
from domain.contracts.contract_salary_control_consolidated_report import ContractSalaryControlConsolidatedReport
from domain.contracts.contract_salary_control_issue_history import ContractSalaryControlIssueHistory, ContractSalaryControlIssueHistoryRow
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot, ContractSalaryControlSnapshotRow
from domain.contracts.contract_salary_control_snapshot_comparison import ContractSalaryControlSnapshotComparison, ContractSalaryControlSnapshotComparisonRow

_MIME_TYPE = "application/json; charset=utf-8"


@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsolidatedJsonExport:
    content: str
    suggested_filename: str
    mime_type: str = _MIME_TYPE


@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsolidatedJsonExporter:
    def export(self, report: ContractSalaryControlConsolidatedReport) -> ContractSalaryControlConsolidatedJsonExport:
        if type(report) is not ContractSalaryControlConsolidatedReport:
            raise TypeError("report doit être un ContractSalaryControlConsolidatedReport strict.")
        return ContractSalaryControlConsolidatedJsonExport(
            json.dumps(_report(report), ensure_ascii=False, indent=2) + "\n",
            f"rapport-consolide-controle-salarial-{report.current_snapshot.reference_date.isoformat()}.json",
        )


def _report(r):
    return {
        "general": {"report_id": _uuid(r.report_id), "generated_at": _dt(r.generated_at), "reference": r.reference, "version": r.version, "generated_by": r.generated_by},
        "summary": {"total_contracts": r.current_snapshot.total_contracts, "compliant_contracts": r.current_snapshot.compliant_contracts, "non_compliant_contracts": r.current_snapshot.non_compliant_contracts, "not_evaluated_contracts": r.current_snapshot.not_evaluated_contracts, "total_shortfall_amount": _dec(r.current_snapshot.total_shortfall_amount)},
        "statistics": {"has_previous_snapshot": r.has_previous_snapshot, "comparison_available": r.comparison is not None, "issue_history_available": r.issue_history is not None, "alerts_available": r.alerts is not None},
        "snapshots": {"current": _snapshot(r.current_snapshot), "previous": _opt(_snapshot, r.previous_snapshot)},
        "comparison": _opt(_comparison, r.comparison),
        "issues": _opt(_issues, r.issue_history),
        "alerts": _opt(_alerts, r.alerts),
    }


def _snapshot(s: ContractSalaryControlSnapshot):
    return {"snapshot_id": _uuid(s.snapshot_id), "reference_date": _date(s.reference_date), "executed_at": _dt(s.executed_at), "created_by": s.created_by, "schema_version": s.schema_version, "total_contracts": s.total_contracts, "compliant_contracts": s.compliant_contracts, "non_compliant_contracts": s.non_compliant_contracts, "not_evaluated_contracts": s.not_evaluated_contracts, "total_shortfall_amount": _dec(s.total_shortfall_amount), "rows": [_snapshot_row(row) for row in s.rows]}


def _snapshot_row(row: ContractSalaryControlSnapshotRow):
    return {"contract_id": _uuid(row.contract_id), "employee_id": _opt(_uuid, row.employee_id), "status": _enum(row.status), "remuneration_amount": _opt(_dec, row.remuneration_amount), "applicable_minimum_amount": _opt(_dec, row.applicable_minimum_amount), "shortfall_amount": _dec(row.shortfall_amount), "classification_code": row.classification_code, "minimum_source": _opt(_enum, row.minimum_source), "territory": _opt(_enum, row.territory), "failure_reason": _opt(_enum, row.failure_reason), "failure_message": row.failure_message, "issue_code": row.issue_code, "issue_message": row.issue_message}


def _comparison(c: ContractSalaryControlSnapshotComparison):
    return {"before_snapshot_id": _uuid(c.before_snapshot_id), "after_snapshot_id": _uuid(c.after_snapshot_id), "new_contracts": c.new_contracts, "removed_contracts": c.removed_contracts, "became_compliant": c.became_compliant, "became_non_compliant": c.became_non_compliant, "became_not_evaluated": c.became_not_evaluated, "total_shortfall_delta": _dec(c.total_shortfall_delta), "rows": [_comparison_row(row) for row in c.rows]}


def _comparison_row(row: ContractSalaryControlSnapshotComparisonRow):
    return {name: _value(getattr(row, name)) for name in row.__dataclass_fields__}


def _issues(h: ContractSalaryControlIssueHistory):
    return {"total_issues": h.total_issues, "new_issues": h.new_issues, "persistent_issues": h.ongoing_issues, "resolved_issues": h.resolved_issues, "unknown_issues": h.unknown_issues, "rows": [_issue_row(row) for row in h.rows]}


def _issue_row(row: ContractSalaryControlIssueHistoryRow):
    return {name: _value(getattr(row, name)) for name in row.__dataclass_fields__}


def _alerts(a: ContractSalaryAlertCollection):
    return {"total": a.total_count, "critical": a.critical_count, "warnings": a.warning_count, "information": a.info_count, "rows": [_alert(row) for row in a.alerts]}


def _alert(row: ContractSalaryAlert):
    return {name: _value(getattr(row, name)) for name in row.__dataclass_fields__}


def _value(v):
    if v is None: return None
    if type(v) is UUID: return str(v)
    if type(v) is Decimal: return format(v, "f")
    if type(v) in (date, datetime): return v.isoformat()
    if isinstance(v, Enum): return v.value
    if type(v) is tuple: return [_value(x) for x in v]
    return v

def _opt(fn, v): return None if v is None else fn(v)
def _uuid(v): return str(v)
def _date(v): return v.isoformat()
def _dt(v): return v.isoformat()
def _dec(v): return format(v, "f")
def _enum(v): return v.value
