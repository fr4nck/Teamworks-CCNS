from application.services.hr_document_workflow import (
    HRDocumentWorkflowErrorCode,
    prepare_hr_document_workflow,
)
from domain.documents import (
    DocumentTemplate,
    GenerationStatus,
    TemplateTarget,
)


def _complete_structure():
    return {"raison_sociale": "Structure", "adresse": "Adresse"}


def _complete_employee():
    return {"nom": "Martin", "prenom": "Lou"}


def test_unknown_document_type_returns_a_structured_error() -> None:
    result = prepare_hr_document_workflow("document-magique")

    assert result.ok is False
    assert result.ready is False
    assert result.document_type is None
    assert result.generation_plan is None
    assert [(error.code, error.field) for error in result.errors] == [
        (HRDocumentWorkflowErrorCode.UNKNOWN_DOCUMENT_TYPE, "document_code"),
    ]


def test_workflow_filters_templates_with_canonical_contract_values() -> None:
    templates = (
        DocumentTemplate("legacy.twd"),
        DocumentTemplate(
            "g2.twd",
            target=TemplateTarget(
                convention_code="CCNS",
                ccns_group="G2",
                document_kind="contract",
            ),
        ),
        DocumentTemplate(
            "g3.twd",
            target=TemplateTarget(
                convention_code="CCNS",
                ccns_group="G3",
                document_kind="contract",
            ),
        ),
    )

    result = prepare_hr_document_workflow(
        "contract",
        templates=templates,
        structure=_complete_structure(),
        employee=_complete_employee(),
        contract={
            "date_debut": "2026-09-01",
            "convention": "CCNS",
            "groupe_ccns": "G2",
        },
    )

    assert result.ok is True
    assert [template.name for template in result.templates] == ["legacy.twd", "g2.twd"]
    assert result.generation_plan is not None
    assert result.generation_plan.status is GenerationStatus.READY
    assert result.ready is True


def test_workflow_can_require_a_compatible_internal_template() -> None:
    result = prepare_hr_document_workflow(
        "contract",
        templates=(
            DocumentTemplate(
                "g3.twd",
                target=TemplateTarget(
                    convention_code="CCNS",
                    ccns_group="G3",
                    document_kind="contract",
                ),
            ),
        ),
        require_template=True,
        structure=_complete_structure(),
        employee=_complete_employee(),
        contract={
            "date_debut": "2026-09-01",
            "convention": "CCNS",
            "groupe_ccns": "G2",
        },
    )

    assert result.ready is False
    assert [(error.code, error.field) for error in result.errors] == [
        (HRDocumentWorkflowErrorCode.NO_COMPATIBLE_TEMPLATE, "template"),
    ]


def test_generation_issues_stay_in_the_generation_plan() -> None:
    result = prepare_hr_document_workflow(
        "contract",
        structure={"raison_sociale": "Structure"},
        employee=_complete_employee(),
        contract={"date_debut": "2026-09-01"},
    )

    assert result.errors == ()
    assert result.generation_plan is not None
    assert result.generation_plan.status is GenerationStatus.BLOCKED
    assert result.ready is False


def test_external_document_does_not_require_an_internal_template() -> None:
    result = prepare_hr_document_workflow(
        "france_travail_certificate",
        require_template=True,
        structure=_complete_structure(),
        employee=_complete_employee(),
        contract={"date_debut": "2026-09-01"},
    )

    assert result.errors == ()
    assert result.generation_plan is not None
    assert result.generation_plan.status is GenerationStatus.EXTERNAL_PREPARATION
