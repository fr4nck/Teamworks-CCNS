from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from domain.documents import (
    DocumentType,
    GenerationPlan,
    MergeContext,
    MissingMergeField,
    build_generation_plan,
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


def prepare_hr_document_generation(
    document_code: str,
    *,
    structure: Mapping[str, object] | None = None,
    employee: Mapping[str, object] | None = None,
    contract: Mapping[str, object] | None = None,
    extra: Mapping[str, object] | None = None,
    template_text: str | None = None,
    known_template_keywords: Iterable[str] = (),
) -> GenerationPlan:
    """Prépare un plan de génération indépendant de wx et de la suite Office."""

    prepared = prepare_hr_document(
        document_code,
        structure=structure,
        employee=employee,
        contract=contract,
        extra=extra,
    )
    return build_generation_plan(
        document_type=prepared.document_type,
        merge_context=prepared.merge_context,
        missing_fields=prepared.missing_fields,
        template_text=template_text,
        known_template_keywords=known_template_keywords,
    )
