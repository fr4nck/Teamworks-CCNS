from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from domain.documents import (
    DocumentType,
    MergeContext,
    MissingMergeField,
    build_merge_context,
    get_document_type,
    validate_required_fields,
)


@dataclass(frozen=True)
class PreparedHRDocument:
    document_type: DocumentType
    merge_context: MergeContext
    missing_fields: tuple[MissingMergeField, ...]

    @property
    def ready(self) -> bool:
        return not self.missing_fields

    @property
    def generated_by_teamworks(self) -> bool:
        return self.document_type.generated_by_teamworks


def prepare_hr_document(
    document_code: str,
    *,
    structure: Mapping[str, object] | None = None,
    employee: Mapping[str, object] | None = None,
    contract: Mapping[str, object] | None = None,
    extra: Mapping[str, object] | None = None,
) -> PreparedHRDocument:
    document_type = get_document_type(document_code)
    merge_context = build_merge_context(
        structure=structure,
        employee=employee,
        contract=contract,
        extra=extra,
    )
    missing_fields = validate_required_fields(
        merge_context,
        document_type.required_fields,
    )
    return PreparedHRDocument(
        document_type=document_type,
        merge_context=merge_context,
        missing_fields=missing_fields,
    )
