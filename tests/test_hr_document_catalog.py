from application.services.hr_documents import prepare_hr_document
from domain.documents import (
    DEFAULT_HR_DOCUMENT_CATALOG,
    DocumentGenerationMode,
    DocumentKind,
    DocumentScope,
    build_merge_context,
    get_document_type,
    list_document_types,
    validate_required_fields,
)


def test_default_catalog_has_unique_codes() -> None:
    codes = [item.code for item in DEFAULT_HR_DOCUMENT_CATALOG]
    assert len(codes) == len(set(codes))


def test_default_catalog_contains_expected_hr_documents() -> None:
    kinds = {item.kind for item in DEFAULT_HR_DOCUMENT_CATALOG}
    assert kinds == {
        DocumentKind.CONTRACT,
        DocumentKind.AMENDMENT,
        DocumentKind.MUTUAL_INSURANCE_WAIVER,
        DocumentKind.EMPLOYMENT_CERTIFICATE,
        DocumentKind.EXPERIENCE_CERTIFICATE,
        DocumentKind.MINOR_AUTHORIZATION,
        DocumentKind.WORK_CERTIFICATE,
        DocumentKind.TRAINING_DOCUMENT,
        DocumentKind.END_OF_CONTRACT_DOCUMENT,
        DocumentKind.FRANCE_TRAVAIL_CERTIFICATE,
    }


def test_france_travail_document_is_prepared_but_not_generated_internally() -> None:
    document_type = get_document_type(DocumentKind.FRANCE_TRAVAIL_CERTIFICATE)
    assert document_type.generation_mode is DocumentGenerationMode.EXTERNAL_PREPARATION
    assert document_type.generated_by_teamworks is False


def test_internal_catalog_can_be_filtered_by_scope() -> None:
    contract_documents = list_document_types(
        scope=DocumentScope.CONTRACT,
        generated_by_teamworks=True,
    )
    assert contract_documents
    assert all(item.scope is DocumentScope.CONTRACT for item in contract_documents)
    assert all(item.generated_by_teamworks for item in contract_documents)
    assert DocumentKind.FRANCE_TRAVAIL_CERTIFICATE not in {item.kind for item in contract_documents}


def test_merge_context_prefixes_structure_employee_and_contract_without_defaults() -> None:
    context = build_merge_context(
        structure={
            "raison_sociale": "Association Exemple",
            "adresse": "1 rue du Test",
            "telephone": "01 02 03 04 05",
            "email_rh": "rh@example.test",
            "logo": "logo.png",
        },
        employee={"nom": "Martin", "prenom": "Lou"},
        contract={"date_debut": "2026-09-01"},
    )
    values = context.as_dict()

    assert values["STRUCTURE_RAISON_SOCIALE"] == "Association Exemple"
    assert values["STRUCTURE_ADRESSE"] == "1 rue du Test"
    assert values["STRUCTURE_TELEPHONE"] == "01 02 03 04 05"
    assert values["STRUCTURE_EMAIL_RH"] == "rh@example.test"
    assert values["STRUCTURE_LOGO"] == "logo.png"
    assert values["SALARIE_NOM"] == "Martin"
    assert values["SALARIE_PRENOM"] == "Lou"
    assert values["CONTRAT_DATE_DEBUT"] == "2026-09-01"
    assert "PELE_MELE" not in values
    assert "PMSL" not in values


def test_legacy_extra_values_cannot_override_canonical_namespaces() -> None:
    context = build_merge_context(
        structure={"raison_sociale": "Structure canonique"},
        employee={"nom": "Martin"},
        contract={"date_debut": "2026-09-01"},
        extra={
            "STRUCTURE_RAISON_SOCIALE": "Ancienne structure",
            "SALARIE_NOM": "Ancien nom",
            "CONTRAT_DATE_DEBUT": "01/01/1900",
            "NOM": "Mot-clé historique conservé",
        },
    )
    values = context.as_dict()

    assert values["STRUCTURE_RAISON_SOCIALE"] == "Structure canonique"
    assert values["SALARIE_NOM"] == "Martin"
    assert values["CONTRAT_DATE_DEBUT"] == "2026-09-01"
    assert values["NOM"] == "Mot-clé historique conservé"


def test_required_fields_report_their_source() -> None:
    context = build_merge_context(
        structure={"raison_sociale": "Structure", "adresse": "Adresse"},
        employee={"nom": "Martin"},
    )
    missing = validate_required_fields(
        context,
        ("STRUCTURE_RAISON_SOCIALE", "SALARIE_NOM", "SALARIE_PRENOM", "CONTRAT_DATE_DEBUT"),
    )
    assert [(item.field, item.source) for item in missing] == [
        ("SALARIE_PRENOM", "salarie"),
        ("CONTRAT_DATE_DEBUT", "contrat"),
    ]


def test_prepare_contract_is_ready_with_structure_employee_and_contract_data() -> None:
    prepared = prepare_hr_document(
        "contract",
        structure={"raison_sociale": "Structure", "adresse": "Adresse"},
        employee={"nom": "Martin", "prenom": "Lou"},
        contract={"date_debut": "2026-09-01"},
    )
    assert prepared.ready is True
    assert prepared.generated_by_teamworks is True
    assert prepared.missing_fields == ()


def test_prepare_document_does_not_invent_missing_structure_data() -> None:
    prepared = prepare_hr_document(
        "employment_certificate",
        structure={},
        employee={"nom": "Martin", "prenom": "Lou"},
    )
    assert prepared.ready is False
    assert {item.field for item in prepared.missing_fields} == {
        "STRUCTURE_RAISON_SOCIALE",
        "STRUCTURE_ADRESSE",
    }


def test_unknown_document_code_is_rejected() -> None:
    try:
        get_document_type("document-magique")
    except KeyError as exc:
        assert "document-magique" in str(exc)
    else:
        raise AssertionError("un code documentaire inconnu doit être refusé")
