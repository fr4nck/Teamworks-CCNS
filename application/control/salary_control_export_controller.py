from __future__ import annotations

from dataclasses import dataclass, field

from application.presentation.salary_control_exporter import (
    ContractSalaryControlExportFormat,
    ContractSalaryControlExporter,
)
from application.presentation.salary_control_presenter import ContractSalaryControlViewModel


@dataclass(frozen=True, slots=True)
class ContractSalaryControlExportRequest:
    view_model: ContractSalaryControlViewModel
    format: ContractSalaryControlExportFormat

    def __post_init__(self) -> None:
        if type(self.view_model) is not ContractSalaryControlViewModel:
            raise TypeError("view_model doit être un ContractSalaryControlViewModel strict.")
        if type(self.format) is not ContractSalaryControlExportFormat:
            raise TypeError("format doit être un ContractSalaryControlExportFormat strict.")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlExportResponse:
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
class ContractSalaryControlExportController:
    """Contrôleur stateless et indépendant des interfaces pour l'export salarial."""

    exporter: ContractSalaryControlExporter = field(default_factory=ContractSalaryControlExporter)

    def __post_init__(self) -> None:
        if type(self.exporter) is not ContractSalaryControlExporter:
            raise TypeError("exporter doit être un ContractSalaryControlExporter strict.")

    def execute(
        self,
        request: ContractSalaryControlExportRequest,
    ) -> ContractSalaryControlExportResponse:
        if type(request) is not ContractSalaryControlExportRequest:
            raise TypeError("request doit être un ContractSalaryControlExportRequest strict.")

        export = self.exporter.export(request.view_model, request.format)
        return ContractSalaryControlExportResponse(
            content=export.content,
            suggested_filename=export.suggested_filename,
            mime_type=export.mime_type,
            format=export.format,
        )
