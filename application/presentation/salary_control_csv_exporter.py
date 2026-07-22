from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from typing import Optional

from application.presentation.salary_control_presenter import (
    ContractSalaryControlRowViewModel,
    ContractSalaryControlViewModel,
)

_ABSENT = "__ABSENT__"
_MIME_TYPE = "text/csv; charset=utf-8"
_HEADERS = (
    "reference_date",
    "contract_id",
    "employee_id",
    "status",
    "classification_code",
    "remuneration_amount",
    "applicable_minimum_amount",
    "minimum_source",
    "shortfall_amount",
    "territory",
    "failure_reason",
    "failure_message",
    "issue_code",
    "issue_message",
)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlCsvExport:
    content: str
    suggested_filename: str
    mime_type: str = _MIME_TYPE

    def __post_init__(self) -> None:
        if type(self.content) is not str:
            raise TypeError("content doit être une chaîne stricte.")
        if type(self.suggested_filename) is not str:
            raise TypeError("suggested_filename doit être une chaîne stricte.")
        if not self.suggested_filename.strip():
            raise ValueError("suggested_filename ne peut pas être vide.")
        if type(self.mime_type) is not str:
            raise TypeError("mime_type doit être une chaîne stricte.")
        if self.mime_type != _MIME_TYPE:
            raise ValueError(f"mime_type doit être {_MIME_TYPE!r}.")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlCsvExporter:
    """Exporteur CSV pur du view model de contrôle salarial."""

    def export(self, view_model: ContractSalaryControlViewModel) -> ContractSalaryControlCsvExport:
        if type(view_model) is not ContractSalaryControlViewModel:
            raise TypeError("view_model doit être un ContractSalaryControlViewModel strict.")

        stream = StringIO(newline="")
        writer = csv.writer(
            stream,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\r\n",
        )
        writer.writerow(_HEADERS)
        for row in view_model.rows:
            writer.writerow(_row_values(row))

        return ContractSalaryControlCsvExport(
            content=stream.getvalue(),
            suggested_filename=f"controle-salarial-{view_model.reference_date.isoformat()}.csv",
        )


def _row_values(row: ContractSalaryControlRowViewModel) -> tuple[str, ...]:
    if type(row) is not ContractSalaryControlRowViewModel:
        raise TypeError("rows doit contenir des ContractSalaryControlRowViewModel stricts.")
    return (
        row.reference_date.isoformat(),
        str(row.contract_id),
        _optional(row.employee_id),
        row.status.name,
        _optional(row.classification_code),
        _optional(row.remuneration_amount),
        _optional(row.applicable_minimum_amount),
        _optional_enum(row.minimum_source),
        _decimal(row.shortfall_amount),
        _optional_enum(row.territory),
        _optional_enum(row.failure_reason),
        _optional(row.failure_message),
        _optional(row.issue_code),
        _optional(row.issue_message),
    )


def _decimal(value: object) -> str:
    return format(value, "f")


def _optional(value: Optional[object]) -> str:
    if value is None:
        return _ABSENT
    return str(value)


def _optional_enum(value: Optional[object]) -> str:
    if value is None:
        return _ABSENT
    return str(value.value)
