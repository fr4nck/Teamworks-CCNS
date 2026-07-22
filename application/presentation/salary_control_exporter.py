from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from application.presentation.salary_control_csv_exporter import ContractSalaryControlCsvExporter
from application.presentation.salary_control_json_exporter import ContractSalaryControlJsonExporter
from application.presentation.salary_control_presenter import ContractSalaryControlViewModel


class ContractSalaryControlExportFormat(str, Enum):
    """Formats disponibles pour l'export du contrôle salarial."""

    CSV = "csv"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class ContractSalaryControlExport:
    content: str
    suggested_filename: str
    mime_type: str
    format: ContractSalaryControlExportFormat

    def __post_init__(self) -> None:
        if type(self.content) is not str:
            raise TypeError("content doit être une chaîne stricte.")
        if not self.content:
            raise ValueError("content ne peut pas être vide.")
        if type(self.suggested_filename) is not str:
            raise TypeError("suggested_filename doit être une chaîne stricte.")
        if not self.suggested_filename.strip():
            raise ValueError("suggested_filename ne peut pas être vide.")
        if type(self.mime_type) is not str:
            raise TypeError("mime_type doit être une chaîne stricte.")
        if not self.mime_type.strip():
            raise ValueError("mime_type ne peut pas être vide.")
        if type(self.format) is not ContractSalaryControlExportFormat:
            raise TypeError("format doit être un ContractSalaryControlExportFormat strict.")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlExporter:
    """Façade stateless d'export du view model de contrôle salarial."""

    csv_exporter: ContractSalaryControlCsvExporter = field(default_factory=ContractSalaryControlCsvExporter)
    json_exporter: ContractSalaryControlJsonExporter = field(default_factory=ContractSalaryControlJsonExporter)

    def __post_init__(self) -> None:
        if type(self.csv_exporter) is not ContractSalaryControlCsvExporter:
            raise TypeError("csv_exporter doit être un ContractSalaryControlCsvExporter strict.")
        if type(self.json_exporter) is not ContractSalaryControlJsonExporter:
            raise TypeError("json_exporter doit être un ContractSalaryControlJsonExporter strict.")

    def export(
        self,
        view_model: ContractSalaryControlViewModel,
        format: ContractSalaryControlExportFormat,
    ) -> ContractSalaryControlExport:
        if type(view_model) is not ContractSalaryControlViewModel:
            raise TypeError("view_model doit être un ContractSalaryControlViewModel strict.")
        if type(format) is not ContractSalaryControlExportFormat:
            raise TypeError("format doit être un ContractSalaryControlExportFormat strict.")

        if format is ContractSalaryControlExportFormat.CSV:
            export = self.csv_exporter.export(view_model)
        elif format is ContractSalaryControlExportFormat.JSON:
            export = self.json_exporter.export(view_model)
        else:  # pragma: no cover - enum stricte validée ci-dessus.
            raise ValueError(f"format d'export non supporté: {format!r}.")

        return ContractSalaryControlExport(
            content=export.content,
            suggested_filename=export.suggested_filename,
            mime_type=export.mime_type,
            format=format,
        )
