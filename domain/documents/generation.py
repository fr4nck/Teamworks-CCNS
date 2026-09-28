from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .catalog import DocumentType
from .keywords import (
    KeywordContext,
    TemplateKeywordValidation,
    validate_template_keywords,
)
from .merge_context import MergeContext, MissingMergeField


class DocumentIssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DocumentIssueCode(str, Enum):
    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNKNOWN_TEMPLATE_KEYWORD = "unknown_template_keyword"
    EXTERNAL_GENERATION_REQUIRED = "external_generation_required"


class GenerationStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"
    EXTERNAL_PREPARATION = "external_preparation"


@dataclass(frozen=True)
class DocumentIssue:
    code: DocumentIssueCode
    severity: DocumentIssueSeverity
    message: str
    field: str | None = None


@dataclass(frozen=True)
class GenerationPlan:
    document_type: DocumentType
    merge_context: MergeContext
    status: GenerationStatus
    issues: tuple[DocumentIssue, ...]
    template_validation: TemplateKeywordValidation | None = None

    @property
    def ready(self) -> bool:
        return self.status is GenerationStatus.READY

    @property
    def errors(self) -> tuple[DocumentIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is DocumentIssueSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[DocumentIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity is DocumentIssueSeverity.WARNING
        )


def build_generation_plan(
    *,
    document_type: DocumentType,
    merge_context: MergeContext,
    missing_fields: Iterable[MissingMergeField] = (),
    template_text: str | None = None,
    known_template_keywords: Iterable[str] = (),
) -> GenerationPlan:
    issues: list[DocumentIssue] = []

    for missing in missing_fields:
        issues.append(
            DocumentIssue(
                code=DocumentIssueCode.MISSING_REQUIRED_FIELD,
                severity=DocumentIssueSeverity.ERROR,
                field=missing.field,
                message=f"Champ requis absent : {missing.field}",
            )
        )

    validation = None
    if template_text is not None:
        validation = validate_template_keywords(
            template_text,
            merge_context.values,
            context=KeywordContext.HR_DOCUMENT,
            extra_keywords=known_template_keywords,
        )
        for keyword in validation.unknown_keywords:
            issues.append(
                DocumentIssue(
                    code=DocumentIssueCode.UNKNOWN_TEMPLATE_KEYWORD,
                    severity=DocumentIssueSeverity.WARNING,
                    field=keyword,
                    message=f"Mot-clé de modèle inconnu : {keyword}",
                )
            )

    if not document_type.generated_by_teamworks:
        issues.append(
            DocumentIssue(
                code=DocumentIssueCode.EXTERNAL_GENERATION_REQUIRED,
                severity=DocumentIssueSeverity.INFO,
                message=(
                    f"{document_type.label} est préparé par Teamworks mais doit "
                    "être produit par le service externe prévu."
                ),
            )
        )
        status = GenerationStatus.EXTERNAL_PREPARATION
    elif any(
        issue.severity is DocumentIssueSeverity.ERROR
        for issue in issues
    ):
        status = GenerationStatus.BLOCKED
    else:
        status = GenerationStatus.READY

    return GenerationPlan(
        document_type=document_type,
        merge_context=merge_context,
        status=status,
        issues=tuple(issues),
        template_validation=validation,
    )
