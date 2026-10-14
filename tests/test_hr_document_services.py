from application.services.hr_documents import prepare_hr_document_generation
from domain.documents import (
    DocumentIssueCode,
    DocumentTemplate,
    GenerationStatus,
    KeywordContext,
    TemplateTarget,
    render_text_template,
    select_document_templates,
    validate_template_keywords,
)


def test_known_empty_keyword_is_distinct_from_unknown_keyword() -> None:
    validation = validate_template_keywords(
        "Bonjour {SALARIE_PRENOM} {INCONNU}",
        {"SALARIE_PRENOM": ""},
        context=KeywordContext.HR_DOCUMENT,
    )

    assert validation.empty_known_keywords == ("SALARIE_PRENOM",)
    assert validation.unknown_keywords == ("INCONNU",)


def test_text_preview_blanks_known_missing_values_and_keeps_unknown_tokens_visible() -> None:
    rendered = render_text_template(
        "{STRUCTURE_RAISON_SOCIALE} / {STRUCTURE_SITE_WEB} / {FAUTE_MODELE}",
        {"STRUCTURE_RAISON_SOCIALE": "Association Exemple"},
        context=KeywordContext.HR_DOCUMENT,
    )

    assert rendered == "Association Exemple /  / {FAUTE_MODELE}"


def test_dynamic_custom_keyword_can_be_known_even_without_value() -> None:
    validation = validate_template_keywords(
        "{CHAMP_PERSO}",
        {},
        context=KeywordContext.HR_DOCUMENT,
        extra_keywords=("CHAMP_PERSO",),
    )

    assert validation.unknown_keywords == ()
    assert validation.empty_known_keywords == ("CHAMP_PERSO",)


def test_template_selection_preserves_legacy_fallback_and_filters_document_kind() -> None:
    templates = (
        DocumentTemplate("legacy.twd"),
        DocumentTemplate(
            "contrat-g2.twd",
            target=TemplateTarget(
                convention_code="CCNS",
                ccns_group="G2",
                document_kind="contract",
            ),
        ),
        DocumentTemplate(
            "avenant-g2.twd",
            target=TemplateTarget(
                convention_code="CCNS",
                ccns_group="G2",
                document_kind="amendment",
            ),
        ),
        DocumentTemplate(
            "contrat-g3.twd",
            target=TemplateTarget(
                convention_code="CCNS",
                ccns_group="G3",
                document_kind="contract",
            ),
        ),
    )

    selected = select_document_templates(
        templates,
        contract_data={"CONVENTION": "CCNS", "GROUPECCNS": "G2"},
        document_kind="contract",
    )

    assert [item.name for item in selected] == ["legacy.twd", "contrat-g2.twd"]


def test_template_selection_can_exclude_unclassified_legacy_models() -> None:
    templates = (
        DocumentTemplate("legacy.twd"),
        DocumentTemplate(
            "contrat.twd",
            target=TemplateTarget(document_kind="contract"),
        ),
    )

    selected = select_document_templates(
        templates,
        document_kind="contract",
        include_legacy=False,
    )

    assert [item.name for item in selected] == ["contrat.twd"]


def test_generation_plan_blocks_missing_required_business_data() -> None:
    plan = prepare_hr_document_generation(
        "contract",
        structure={"raison_sociale": "Structure"},
        employee={"nom": "Martin", "prenom": "Lou"},
        contract={"date_debut": "2026-09-01"},
    )

    assert plan.status is GenerationStatus.BLOCKED
    assert plan.ready is False
    assert [(issue.code, issue.field) for issue in plan.errors] == [
        (DocumentIssueCode.MISSING_REQUIRED_FIELD, "STRUCTURE_ADRESSE"),
    ]


def test_unknown_template_keyword_is_reported_without_masking_generation() -> None:
    plan = prepare_hr_document_generation(
        "employment_certificate",
        structure={"raison_sociale": "Structure", "adresse": "Adresse"},
        employee={"nom": "Martin", "prenom": "Lou"},
        template_text="Bonjour {SALARIE_PRENOM}. {MOTCLE_FAUX}",
    )

    assert plan.status is GenerationStatus.READY
    assert plan.ready is True
    assert [(issue.code, issue.field) for issue in plan.warnings] == [
        (DocumentIssueCode.UNKNOWN_TEMPLATE_KEYWORD, "MOTCLE_FAUX"),
    ]


def test_external_document_has_explicit_generation_state() -> None:
    plan = prepare_hr_document_generation(
        "france_travail_certificate",
        structure={"raison_sociale": "Structure", "adresse": "Adresse"},
        employee={"nom": "Martin", "prenom": "Lou"},
        contract={"date_debut": "2026-09-01"},
    )

    assert plan.status is GenerationStatus.EXTERNAL_PREPARATION
    assert any(
        issue.code is DocumentIssueCode.EXTERNAL_GENERATION_REQUIRED
        for issue in plan.issues
    )
