from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from domain.hr_connections import (
    ExchangeStatus,
    ExpectedDocument,
    HrCase,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
)


def _case(*, due_on: date | None = date(2026, 9, 10)) -> HrCase:
    return HrCase.create(
        case_id=" CASE-001 ",
        case_type=HrCaseType.create(code=" mutuelle_affiliation ", label=" Affiliation mutuelle "),
        subject=HrCaseSubject.create(kind=HrCaseSubjectKind.PERSON, identifier=" 42 "),
        organization_code=" mutuelle-demo ",
        opened_on=date(2026, 9, 1),
        due_on=due_on,
        expected_documents=[
            ExpectedDocument.create(code=" bulletin_adhesion ", label=" Bulletin d'adhésion "),
            ExpectedDocument.create(
                code=" justificatif_optionnel ",
                label=" Justificatif complémentaire ",
                required=False,
            ),
        ],
        source=" embauche ",
        comment=" à préparer ",
    )


def test_case_value_objects_require_stable_identifiers_and_labels():
    with pytest.raises(ValueError):
        HrCaseType.create(code=" ", label="Affiliation")
    with pytest.raises(ValueError):
        HrCaseType.create(code="affiliation", label=" ")
    with pytest.raises(ValueError):
        HrCaseSubject.create(kind=HrCaseSubjectKind.PERSON, identifier=" ")
    with pytest.raises(ValueError):
        ExpectedDocument.create(code=" ", label="Pièce")
    with pytest.raises(ValueError):
        ExpectedDocument.create(code="piece", label=" ")
    with pytest.raises(TypeError):
        ExpectedDocument(code="piece", label="Pièce", required=1)  # type: ignore[arg-type]


def test_subject_kind_is_explicit_and_not_a_free_form_string():
    with pytest.raises(TypeError):
        HrCaseSubject(kind="person", identifier="42")  # type: ignore[arg-type]


def test_case_creation_normalizes_non_sensitive_text_and_freezes_expected_documents():
    case = _case()

    assert case.case_id == "CASE-001"
    assert case.case_type.code == "mutuelle_affiliation"
    assert case.case_type.label == "Affiliation mutuelle"
    assert case.subject.identifier == "42"
    assert case.organization_code == "mutuelle-demo"
    assert case.source == "embauche"
    assert case.comment == "à préparer"
    assert case.status is HrCaseStatus.TODO
    assert case.exchange_status is ExchangeStatus.NOT_APPLICABLE
    assert isinstance(case.expected_documents, frozenset)
    assert {item.code for item in case.expected_documents} == {
        "bulletin_adhesion",
        "justificatif_optionnel",
    }

    with pytest.raises(FrozenInstanceError):
        case.case_id = "OTHER"  # type: ignore[misc]


def test_case_rejects_invalid_identity_dates_and_expected_documents():
    case_type = HrCaseType.create(code="dpae", label="DPAE")
    subject = HrCaseSubject.create(kind=HrCaseSubjectKind.PERSON, identifier="42")

    with pytest.raises(ValueError):
        HrCase.create(
            case_id=" ",
            case_type=case_type,
            subject=subject,
            organization_code="urssaf",
            opened_on=date(2026, 9, 1),
        )
    with pytest.raises(ValueError):
        HrCase.create(
            case_id="CASE",
            case_type=case_type,
            subject=subject,
            organization_code=" ",
            opened_on=date(2026, 9, 1),
        )
    with pytest.raises(ValueError):
        HrCase.create(
            case_id="CASE",
            case_type=case_type,
            subject=subject,
            organization_code="urssaf",
            opened_on=date(2026, 9, 2),
            due_on=date(2026, 9, 1),
        )
    with pytest.raises(TypeError):
        HrCase(
            case_id="CASE",
            case_type=case_type,
            subject=subject,
            organization_code="urssaf",
            opened_on=date(2026, 9, 1),
            expected_documents=frozenset({"piece"}),  # type: ignore[arg-type]
        )


def test_nominal_workflow_reaches_acceptance_without_mutating_previous_versions():
    todo = _case()
    prepared = todo.transition_to(HrCaseStatus.PREPARED, comment="Pièces réunies")
    submitted = prepared.transition_to(HrCaseStatus.SUBMITTED)
    accepted = submitted.transition_to(HrCaseStatus.ACCEPTED, result="Affiliation confirmée")

    assert todo.status is HrCaseStatus.TODO
    assert prepared.status is HrCaseStatus.PREPARED
    assert prepared.comment == "Pièces réunies"
    assert submitted.status is HrCaseStatus.SUBMITTED
    assert accepted.status is HrCaseStatus.ACCEPTED
    assert accepted.result == "Affiliation confirmée"
    assert accepted.is_closed


def test_anomaly_requires_regularization_before_direct_acceptance():
    anomaly = (
        _case()
        .transition_to(HrCaseStatus.PREPARED)
        .transition_to(HrCaseStatus.SUBMITTED)
        .transition_to(HrCaseStatus.ANOMALY, result="Pièce illisible")
    )

    assert not anomaly.can_transition_to(HrCaseStatus.ACCEPTED)
    with pytest.raises(ValueError):
        anomaly.transition_to(HrCaseStatus.ACCEPTED)

    regularized = anomaly.transition_to(
        HrCaseStatus.REGULARIZATION,
        comment="Nouvelle pièce transmise",
    )
    accepted = regularized.transition_to(HrCaseStatus.ACCEPTED, result="Régularisé")

    assert regularized.status is HrCaseStatus.REGULARIZATION
    assert accepted.status is HrCaseStatus.ACCEPTED
    assert accepted.result == "Régularisé"


def test_regularization_can_be_resubmitted_or_return_to_anomaly():
    regularized = (
        _case()
        .transition_to(HrCaseStatus.PREPARED)
        .transition_to(HrCaseStatus.SUBMITTED)
        .transition_to(HrCaseStatus.ANOMALY)
        .transition_to(HrCaseStatus.REGULARIZATION)
    )

    assert regularized.can_transition_to(HrCaseStatus.SUBMITTED)
    assert regularized.can_transition_to(HrCaseStatus.ANOMALY)
    assert regularized.can_transition_to(HrCaseStatus.ACCEPTED)


def test_illegal_transitions_and_invalid_status_types_are_rejected():
    case = _case()

    assert not case.can_transition_to(HrCaseStatus.ACCEPTED)
    assert not case.can_transition_to("prepared")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        case.transition_to(HrCaseStatus.ACCEPTED)
    with pytest.raises(TypeError):
        case.transition_to("prepared")  # type: ignore[arg-type]


def test_terminal_cases_cannot_be_reopened_implicitly():
    accepted = (
        _case()
        .transition_to(HrCaseStatus.PREPARED)
        .transition_to(HrCaseStatus.SUBMITTED)
        .transition_to(HrCaseStatus.ACCEPTED)
    )
    cancelled = _case().transition_to(HrCaseStatus.CANCELLED)

    assert not accepted.can_transition_to(HrCaseStatus.ANOMALY)
    assert not cancelled.can_transition_to(HrCaseStatus.TODO)
    with pytest.raises(ValueError):
        accepted.transition_to(HrCaseStatus.ANOMALY)
    with pytest.raises(ValueError):
        cancelled.transition_to(HrCaseStatus.TODO)


def test_overdue_depends_on_business_status_not_technical_exchange():
    case = _case(due_on=date(2026, 9, 5))

    assert not case.is_overdue(as_of=date(2026, 9, 5))
    assert case.is_overdue(as_of=date(2026, 9, 6))

    technically_successful = case.with_exchange_status(ExchangeStatus.SUCCEEDED)
    assert technically_successful.status is HrCaseStatus.TODO
    assert technically_successful.is_overdue(as_of=date(2026, 9, 6))

    accepted = (
        technically_successful
        .transition_to(HrCaseStatus.PREPARED)
        .transition_to(HrCaseStatus.SUBMITTED)
        .transition_to(HrCaseStatus.ACCEPTED)
    )
    assert not accepted.is_overdue(as_of=date(2026, 9, 20))


def test_case_without_due_date_is_never_overdue():
    assert not _case(due_on=None).is_overdue(as_of=date(2030, 1, 1))


def test_exchange_status_is_separate_and_type_checked():
    case = _case()
    ready = case.with_exchange_status(ExchangeStatus.READY)
    succeeded = ready.with_exchange_status(ExchangeStatus.SUCCEEDED)

    assert case.exchange_status is ExchangeStatus.NOT_APPLICABLE
    assert ready.exchange_status is ExchangeStatus.READY
    assert succeeded.exchange_status is ExchangeStatus.SUCCEEDED
    assert succeeded.status is HrCaseStatus.TODO

    with pytest.raises(TypeError):
        case.with_exchange_status("ready")  # type: ignore[arg-type]
