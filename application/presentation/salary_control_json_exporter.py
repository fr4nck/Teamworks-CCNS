from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from application.presentation.salary_control_presenter import (
    ContractSalaryControlEmptyStateViewModel,
    ContractSalaryControlPaginationViewModel,
    ContractSalaryControlRowViewModel,
    ContractSalaryControlViewModel,
)

_MIME_TYPE = "application/json; charset=utf-8"


@dataclass(frozen=True, slots=True)
class ContractSalaryControlJsonExport:
    content: str
    suggested_filename: str
    mime_type: str = _MIME_TYPE

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
        if self.mime_type != _MIME_TYPE:
            raise ValueError(f"mime_type doit être {_MIME_TYPE!r}.")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlJsonExporter:
    """Exporteur JSON pur du view model de contrôle salarial."""

    def export(self, view_model: ContractSalaryControlViewModel) -> ContractSalaryControlJsonExport:
        if type(view_model) is not ContractSalaryControlViewModel:
            raise TypeError("view_model doit être un ContractSalaryControlViewModel strict.")

        document = _document(view_model)
        content = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
        return ContractSalaryControlJsonExport(
            content=content,
            suggested_filename=f"controle-salarial-{_date(view_model.reference_date)}.json",
        )


def _document(view_model: ContractSalaryControlViewModel) -> dict[str, object]:
    return {
        "reference_date": _date(view_model.reference_date),
        "status": _enum(view_model.presentation_status),
        "summary": {
            "title": view_model.summary_title,
            "message": view_model.summary_message,
        },
        "validity": {
            "global": view_model.global_valid,
            "filtered": view_model.filtered_valid,
        },
        "counts": {
            "global_total": view_model.global_total_count,
            "global_compliant": view_model.global_compliant_count,
            "global_non_compliant": view_model.global_non_compliant_count,
            "global_not_evaluated": view_model.global_not_evaluated_count,
            "filtered_total": view_model.filtered_total_count,
            "returned": view_model.returned_count,
        },
        "amounts": {
            "filtered_total_shortfall": _decimal(view_model.filtered_total_shortfall_amount),
        },
        "pagination": _pagination(view_model.pagination),
        "empty_state": _empty_state(view_model.empty_state),
        "rows": [_row(row) for row in view_model.rows],
    }


def _pagination(pagination: ContractSalaryControlPaginationViewModel) -> dict[str, object]:
    if type(pagination) is not ContractSalaryControlPaginationViewModel:
        raise TypeError("pagination doit être un ContractSalaryControlPaginationViewModel strict.")
    return {
        "offset": pagination.offset,
        "limit": pagination.limit,
        "has_previous_page": pagination.has_previous_page,
        "has_next_page": pagination.has_next_page,
        "previous_offset": pagination.previous_offset,
        "next_offset": pagination.next_offset,
        "first_displayed_index": pagination.first_displayed_index,
        "last_displayed_index": pagination.last_displayed_index,
        "total_filtered_count": pagination.total_filtered_count,
    }


def _empty_state(empty_state: Optional[ContractSalaryControlEmptyStateViewModel]) -> Optional[dict[str, str]]:
    if empty_state is None:
        return None
    if type(empty_state) is not ContractSalaryControlEmptyStateViewModel:
        raise TypeError("empty_state doit être None ou un ContractSalaryControlEmptyStateViewModel strict.")
    return {
        "title": empty_state.title,
        "message": empty_state.message,
    }


def _row(row: ContractSalaryControlRowViewModel) -> dict[str, object]:
    if type(row) is not ContractSalaryControlRowViewModel:
        raise TypeError("rows doit contenir des ContractSalaryControlRowViewModel stricts.")
    return {
        "contract_id": _uuid(row.contract_id),
        "employee_id": _optional_uuid(row.employee_id),
        "reference_date": _date(row.reference_date),
        "status": _enum(row.status),
        "classification_code": row.classification_code,
        "remuneration_amount": _optional_decimal(row.remuneration_amount),
        "applicable_minimum_amount": _optional_decimal(row.applicable_minimum_amount),
        "shortfall_amount": _decimal(row.shortfall_amount),
        "minimum_source": _optional_enum(row.minimum_source),
        "territory": _optional_enum(row.territory),
        "failure_reason": _optional_enum(row.failure_reason),
        "failure_message": row.failure_message,
        "issue_code": row.issue_code,
        "issue_message": row.issue_message,
    }


def _date(value: date) -> str:
    if type(value) is not date:
        raise TypeError("date doit être une date stricte.")
    return value.isoformat()


def _uuid(value: UUID) -> str:
    if type(value) is not UUID:
        raise TypeError("UUID attendu.")
    return str(value)


def _optional_uuid(value: Optional[UUID]) -> Optional[str]:
    if value is None:
        return None
    return _uuid(value)


def _enum(value: Enum) -> object:
    if not isinstance(value, Enum):
        raise TypeError("enum attendu.")
    return value.value


def _optional_enum(value: Optional[Enum]) -> Optional[object]:
    if value is None:
        return None
    return _enum(value)


def _decimal(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise TypeError("Decimal strict attendu.")
    return format(value, "f")


def _optional_decimal(value: Optional[Decimal]) -> Optional[str]:
    if value is None:
        return None
    return _decimal(value)
