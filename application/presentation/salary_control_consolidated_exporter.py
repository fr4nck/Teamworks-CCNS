from __future__ import annotations

from dataclasses import dataclass, field

from application.presentation.salary_control_exporter import ContractSalaryControlExport, ContractSalaryControlExportFormat
from application.presentation.salary_control_consolidated_csv_exporter import ContractSalaryControlConsolidatedCsvExporter
from application.presentation.salary_control_consolidated_json_exporter import ContractSalaryControlConsolidatedJsonExporter
from domain.contracts.contract_salary_control_consolidated_report import ContractSalaryControlConsolidatedReport


@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsolidatedExporter:
    csv_exporter: ContractSalaryControlConsolidatedCsvExporter = field(default_factory=ContractSalaryControlConsolidatedCsvExporter)
    json_exporter: ContractSalaryControlConsolidatedJsonExporter = field(default_factory=ContractSalaryControlConsolidatedJsonExporter)

    def export(self, report: ContractSalaryControlConsolidatedReport, format: ContractSalaryControlExportFormat) -> ContractSalaryControlExport:
        if type(format) is not ContractSalaryControlExportFormat:
            raise TypeError("format doit être un ContractSalaryControlExportFormat strict.")
        export = self.csv_exporter.export(report) if format is ContractSalaryControlExportFormat.CSV else self.json_exporter.export(report)
        return ContractSalaryControlExport(export.content, export.suggested_filename, export.mime_type, format)
