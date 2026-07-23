from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from application.control import BuildContractSalaryControlConsolidatedReportUseCase
from application.presentation import ContractSalaryControlConsolidatedCsvExporter, ContractSalaryControlConsolidatedJsonExporter, ContractSalaryControlConsolidatedExporter, ContractSalaryControlExportFormat
from domain.contracts import ContractSalaryControlConsolidatedReport
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from tests.test_contract_salary_control_snapshot_comparison import SID1, SID2, CID1, CID2, REF, NOW, r, snap

RID = UUID("40000000-0000-0000-0000-000000000001")
GEN = datetime(2026, 7, 23, 12, tzinfo=timezone.utc)


def build(current, previous=None):
    return BuildContractSalaryControlConsolidatedReportUseCase(report_id_factory=lambda: RID, clock=lambda: GEN).execute(current, previous, generated_by="Élodie Comptabilité")


def test_export_vide_snapshots_absents_json_stable_unicode_decimal_sans_float():
    report = build(snap(SID2, []))
    assert type(report) is ContractSalaryControlConsolidatedReport
    assert report.comparison is None and report.issue_history is None and report.alerts is None
    content = ContractSalaryControlConsolidatedJsonExporter().export(report).content
    data = json.loads(content)
    assert data["general"]["generated_by"] == "Élodie Comptabilité"
    assert data["summary"]["total_shortfall_amount"] == "0.00"
    assert data["comparison"] is None and data["issues"] is None and data["alerts"] is None
    assert not any(isinstance(value, float) for value in json.loads(content).values())


def test_export_complet_json_csv_deterministes_anomalies_alertes_et_aucune_duplication():
    before = snap(SID1, [r(CID1), r(CID2, ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00"), issue="MIN")])
    after = snap(SID2, [r(CID1, ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("12.50"), issue="MIN"), r(CID2)])
    report = build(after, before)
    assert report.comparison.became_compliant == 1
    assert report.comparison.became_non_compliant == 1
    assert report.issue_history.new_issues == 1 and report.issue_history.resolved_issues == 1
    assert report.alerts.critical_count >= 1

    json_exporter = ContractSalaryControlConsolidatedJsonExporter()
    first = json_exporter.export(report).content
    second = json_exporter.export(report).content
    assert first == second
    data = json.loads(first)
    assert [row["contract_id"] for row in data["snapshots"]["current"]["rows"]] == [str(CID1), str(CID2)]
    assert data["snapshots"]["current"]["rows"][0]["shortfall_amount"] == "12.50"
    assert data["issues"]["new_issues"] == 1 and data["issues"]["resolved_issues"] == 1

    csv = ContractSalaryControlConsolidatedCsvExporter().export(report).content
    assert csv == ContractSalaryControlConsolidatedCsvExporter().export(report).content
    assert "summary;total_shortfall_amount;12.50" in csv
    assert "current;%s;%s" % (REF.isoformat(), CID1) in csv
    facade = ContractSalaryControlConsolidatedExporter().export(report, ContractSalaryControlExportFormat.JSON)
    assert facade.content == first and facade.suggested_filename.endswith(".json")
