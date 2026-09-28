from datetime import date, datetime, timedelta, timezone

import pytest

from domain.employment.termination import TerminationDomainError, TerminationWorkflowStatus
from domain.employment.termination_documents import (
    TerminationClosureChecklist, TerminationDocument, TerminationDocumentSource,
    TerminationDocumentType, advance_results_workflow,
)
from tests.test_employee_termination_domain import ready_termination, transmit

UTC = timezone.utc
NOW = datetime(2026, 10, 31, 18, 0, tzinfo=UTC)
HASHES = {
    TerminationDocumentType.FINAL_PAYSLIP: "1" * 64,
    TerminationDocumentType.AER: "2" * 64,
    TerminationDocumentType.WORK_CERTIFICATE: "3" * 64,
    TerminationDocumentType.FINAL_SETTLEMENT_RECEIPT: "4" * 64,
    TerminationDocumentType.OTHER: "5" * 64,
}


def doc(termination, kind, *, archived=False, delivered=False):
    source = TerminationDocumentSource.FRANCE_TRAVAIL if kind is TerminationDocumentType.AER else TerminationDocumentSource.IMPACT_EMPLOI
    value = TerminationDocument(
        termination_id=termination.termination_id, document_type=kind, source=source,
        document_date=date(2026, 10, 31), received_at=NOW, received_by="director-1",
        file_reference="rh/%s.pdf" % kind.value.lower(), sha256=HASHES[kind],
    )
    if archived:
        value = value.mark_archived(at=NOW + timedelta(minutes=1), by="director-1")
    if delivered:
        if kind is TerminationDocumentType.AER and not archived:
            value = value.mark_archived(at=NOW + timedelta(minutes=1), by="director-1")
        value = value.mark_delivered(at=NOW + timedelta(minutes=2), by="director-1")
    return value


def assert_code(code, fn):
    with pytest.raises(TerminationDomainError) as exc:
        fn()
    assert exc.value.code == code


def test_document_is_opaque_and_requires_sha256():
    termination = ready_termination()
    assert_code("INVALID_DOCUMENT_SHA256", lambda: TerminationDocument(
        termination_id=termination.termination_id, document_type="AER", source="FRANCE_TRAVAIL",
        document_date=date(2026, 10, 31), received_at=NOW, received_by="d",
        file_reference="aer.pdf", sha256="not-a-hash",
    ))


def test_archive_and_delivery_are_explicit_immutable_facts():
    termination = ready_termination()
    original = doc(termination, TerminationDocumentType.WORK_CERTIFICATE)
    archived = original.mark_archived(at=NOW + timedelta(minutes=1), by="director-1")
    delivered = archived.mark_delivered(at=NOW + timedelta(minutes=2), by="director-1")
    assert not original.is_archived and not original.is_delivered
    assert archived.is_archived and not archived.is_delivered
    assert delivered.is_archived and delivered.is_delivered


def test_aer_cannot_be_marked_delivered_before_archive():
    termination = ready_termination()
    aer = doc(termination, TerminationDocumentType.AER)
    assert_code("AER_MUST_BE_ARCHIVED_BEFORE_DELIVERY", lambda: aer.mark_delivered(at=NOW + timedelta(minutes=1), by="d"))


def complete_documents(termination):
    return (
        doc(termination, TerminationDocumentType.FINAL_PAYSLIP, archived=True),
        doc(termination, TerminationDocumentType.AER, archived=True, delivered=True),
        doc(termination, TerminationDocumentType.WORK_CERTIFICATE, archived=True, delivered=True),
        doc(termination, TerminationDocumentType.FINAL_SETTLEMENT_RECEIPT, archived=True, delivered=True),
    )


def test_checklist_is_derived_from_documents_not_an_editable_boolean():
    termination = ready_termination()
    checklist = TerminationClosureChecklist.from_documents(complete_documents(termination))
    assert checklist.complete is True


CHECKLIST_FIELDS_BY_TYPE = {
    TerminationDocumentType.FINAL_PAYSLIP: ("final_payslip_received",),
    TerminationDocumentType.AER: ("aer_received", "aer_archived", "aer_delivered"),
    TerminationDocumentType.WORK_CERTIFICATE: ("work_certificate_received", "work_certificate_delivered"),
    TerminationDocumentType.FINAL_SETTLEMENT_RECEIPT: (
        "final_settlement_receipt_received", "final_settlement_receipt_delivered",
    ),
    TerminationDocumentType.OTHER: (),
}
ALL_CHECKLIST_FIELDS = tuple(
    field for fields in CHECKLIST_FIELDS_BY_TYPE.values() for field in fields
)
DOCUMENT_STATES = ("received", "archived", "delivered")


def document_in_state(termination, kind, state):
    return doc(
        termination,
        kind,
        archived=state in ("archived", "delivered"),
        delivered=state == "delivered",
    )


@pytest.mark.parametrize("actual_type", tuple(TerminationDocumentType))
@pytest.mark.parametrize("state", DOCUMENT_STATES)
def test_document_type_only_satisfies_its_own_checklist_conditions(actual_type, state):
    """A document may never satisfy a checklist condition belonging to another type."""
    termination = ready_termination()
    checklist = TerminationClosureChecklist.from_documents((
        document_in_state(termination, actual_type, state),
    ))

    own_fields = set(CHECKLIST_FIELDS_BY_TYPE[actual_type])
    for field in ALL_CHECKLIST_FIELDS:
        if field not in own_fields:
            assert getattr(checklist, field) is False, (
                "%s in state %s incorrectly satisfied %s" % (actual_type.value, state, field)
            )


@pytest.mark.parametrize("missing_type", (
    TerminationDocumentType.FINAL_PAYSLIP,
    TerminationDocumentType.AER,
    TerminationDocumentType.WORK_CERTIFICATE,
    TerminationDocumentType.FINAL_SETTLEMENT_RECEIPT,
))
@pytest.mark.parametrize("replacement_type", tuple(TerminationDocumentType))
@pytest.mark.parametrize("state", DOCUMENT_STATES)
def test_wrong_document_type_cannot_replace_required_type(missing_type, replacement_type, state):
    """Even received/archived/delivered wrong-type documents cannot fill another type's slot."""
    if replacement_type is missing_type:
        pytest.skip("same type is not a substitution")
    termination = ready_termination()
    documents = [
        document_in_state(termination, kind, "delivered")
        for kind in (
            TerminationDocumentType.FINAL_PAYSLIP,
            TerminationDocumentType.AER,
            TerminationDocumentType.WORK_CERTIFICATE,
            TerminationDocumentType.FINAL_SETTLEMENT_RECEIPT,
        )
        if kind is not missing_type
    ]
    documents.append(document_in_state(termination, replacement_type, state))

    checklist = TerminationClosureChecklist.from_documents(documents)

    for field in CHECKLIST_FIELDS_BY_TYPE[missing_type]:
        assert getattr(checklist, field) is False, (
            "%s in state %s incorrectly replaced %s for %s"
            % (replacement_type.value, state, field, missing_type.value)
        )
    assert checklist.complete is False


def test_other_document_never_changes_any_checklist_condition():
    termination = ready_termination()
    baseline = TerminationClosureChecklist.from_documents(())
    for state in DOCUMENT_STATES:
        with_other = TerminationClosureChecklist.from_documents((
            document_in_state(termination, TerminationDocumentType.OTHER, state),
        ))
        assert with_other == baseline
        assert with_other.complete is False


def test_results_received_requires_final_payslip_and_aer():
    termination = ready_termination()
    transmit(termination)
    advance_results_workflow(termination, ())
    assert termination.workflow_status is TerminationWorkflowStatus.EN_ATTENTE_RESULTATS
    assert_code("RESULTS_INCOMPLETE", lambda: advance_results_workflow(
        termination, (doc(termination, TerminationDocumentType.FINAL_PAYSLIP),)
    ))


def test_aer_must_be_delivered_before_documents_remis():
    termination = ready_termination()
    transmit(termination)
    docs = list(complete_documents(termination))
    docs[1] = doc(termination, TerminationDocumentType.AER, archived=True, delivered=False)
    advance_results_workflow(termination, docs)
    advance_results_workflow(termination, docs)
    assert_code("DOCUMENTS_NOT_DELIVERED", lambda: advance_results_workflow(termination, docs))


def test_full_documentary_path_reaches_closure():
    termination = ready_termination()
    transmit(termination)
    documents = complete_documents(termination)
    for _ in range(4):
        advance_results_workflow(termination, documents)
    assert termination.workflow_status is TerminationWorkflowStatus.CLOTURE


def test_document_from_another_termination_is_rejected():
    termination = ready_termination()
    other = ready_termination(contract_id="contract-2")
    transmit(termination)
    foreign = doc(other, TerminationDocumentType.AER, archived=True)
    assert_code("DOCUMENT_TERMINATION_MISMATCH", lambda: advance_results_workflow(termination, (foreign,)))


def test_open_correction_blocks_documentary_closure():
    termination = ready_termination()
    transmit(termination)
    documents = complete_documents(termination)
    for _ in range(3):
        advance_results_workflow(termination, documents)
    termination.request_correction("motif rectifie", requested_by="director-1", requested_at=NOW + timedelta(hours=1))
    assert_code("CORRECTION_OPEN", lambda: advance_results_workflow(termination, documents))
