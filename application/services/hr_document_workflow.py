from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

from domain.documents import (
    DocumentTemplate,
    DocumentType,
    GenerationPlan,
    get_document_type,
    select_document_templates,
)

from .hr_documents import prepare_hr_document_generation


class HRDocumentWorkflowErrorCode(str, Enum):
    UNKNOWN_DOCUMENT_TYPE = "unknown_document_type"
    NO_COMPATIBLE_TEMPLATE = "no_compatible_template"


@dataclass(frozen=True)
class HRDocumentWorkflowError:
    code: HRDocumentWorkflowErrorCode
    message: str
    field: str | None = None


@dataclass(frozen=True)
class HRDocumentWorkflowResult:
    document_type: DocumentType | None
    templates: tuple[DocumentTemplate, ...]
    generation_plan: GenerationPlan | None
    errors: tuple[HRDocumentWorkflowError, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def ready(self) -> bool:
        return (
            self.ok
            and self.generation_plan is not None
            and self.generation_plan.ready
        )


def prepare_hr_document_workflow(
    document_code: str,
    *,
    templates: Iterable[DocumentTemplate] = (),
    include_legacy_templates: bool = True,
    require_template: bool = False,
    structure: Mapping[str, object] | None = None,
    employee: Mapping[str, object] | None = None,
    contract: Mapping[str, object] | None = None,
    extra: Mapping[str, object] | None = None,
    template_text: str | None = None,
    known_template_keywords: Iterable[str] = (),
) -> HRDocumentWorkflowResult:
    """Façade sans UI pour la sélection et la préparation d'un document RH.

    Les erreurs de sélection de haut niveau sont retournées sous forme structurée
    au lieu de remonter des exceptions vers wx ou Qt. Les anomalies de contenu
    du document restent détaillées dans generation_plan.issues.
    """

    try:
        document_type = get_document_type(document_code)
    except KeyError:
        return HRDocumentWorkflowResult(
            document_type=None,
            templates=(),
            generation_plan=None,
            errors=(
                HRDocumentWorkflowError(
                    code=HRDocumentWorkflowErrorCode.UNKNOWN_DOCUMENT_TYPE,
                    field="document_code",
                    message=f"Type de document RH inconnu : {document_code}",
                ),
            ),
        )

    compatible_templates = select_document_templates(
        templates,
        contract_data=contract,
        document_kind=document_type.code,
        include_legacy=include_legacy_templates,
    )

    errors: list[HRDocumentWorkflowError] = []
    if (
        require_template
        and document_type.generated_by_teamworks
        and not compatible_templates
    ):
        errors.append(
            HRDocumentWorkflowError(
                code=HRDocumentWorkflowErrorCode.NO_COMPATIBLE_TEMPLATE,
                field="template",
                message=(
                    f"Aucun modèle compatible n'est disponible pour "
                    f"{document_type.label}."
                ),
            )
        )

    generation_plan = prepare_hr_document_generation(
        document_type.code,
        structure=structure,
        employee=employee,
        contract=contract,
        extra=extra,
        template_text=template_text,
        known_template_keywords=known_template_keywords,
    )

    return HRDocumentWorkflowResult(
        document_type=document_type,
        templates=compatible_templates,
        generation_plan=generation_plan,
        errors=tuple(errors),
    )
