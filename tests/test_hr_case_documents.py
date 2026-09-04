from datetime import date, datetime, timezone

import pytest

from application.services.hr_connections import HrCaseDocumentTrackingService
from domain.hr_connections import (
    ExpectedDocument,
    HrCase,
    HrCaseDocumentReceipt,
    HrCaseDocumentState,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrEventKind,
    HrEventTargetKind,
)


class FakeRepository:
    def __init__(self, case):
        self.case = case
        self.receipts = {}
        self.persisted_events = []

    def get_case(self, *, structure_ref, case_id):
        assert structure_ref == "structure-a"
        return self.case if self.case.case_id == case_id else None

    def get_receipt(self, *, structure_ref, case_id, document_code):
        assert structure_ref == "structure-a"
        return self.receipts.get((case_id, document_code))

    def list_receipts(self, *, structure_ref, case_id):
        assert structure_ref == "structure-a"
        return tuple(
            receipt
            for (stored_case_id, _), receipt in self.receipts.items()
            if stored_case_id == case_id
        )

    def persist_receipt_change(
        self,
        *,
        structure_ref,
        expected_state,
        receipt,
        event,
    ):
        assert structure_ref == "structure-a"
        current = self.receipts.get((receipt.case_id, receipt.document_code))
        current_state = current.state if current is not None else None
        assert current_state is expected_state
        self.receipts[(receipt.case_id, receipt.document_code)] = receipt
        self.persisted_events.append(event)
        return receipt


def _case(status=HrCaseStatus.TODO):
    return HrCase(
        case_id="case-1",
        case_type=HrCaseType.create(code="administratif", label="Suivi administratif"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="42",
        ),
        organization_code="organisme-a",
        opened_on=date(2026, 9, 1),
        status=status,
        expected_documents=frozenset(
            {
                ExpectedDocument.create(
                    code="justificatif",
                    label="Justificatif",
                    required=True,
                ),
                ExpectedDocument.create(
                    code="annexe",
                    label="Annexe",
                    required=False,
                ),
            }
        ),
    )


def _service(repository):
    return HrCaseDocumentTrackingService(
        repository=repository,
        now_provider=lambda: datetime(2026, 9, 2, 8, 30, tzinfo=timezone.utc),
        event_id_factory=lambda: "evt-doc-1",
    )


def test_receipt_domain_is_administrative_and_withdrawal_keeps_history_dates():
    receipt = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
        artifact_ref="document-17",
        source="teamworks-ui",
    )

    assert receipt.state is HrCaseDocumentState.RECEIVED
    assert receipt.is_received is True
    assert receipt.withdrawn_on is None

    withdrawn = receipt.withdraw(withdrawn_on=date(2026, 9, 3))

    assert withdrawn.state is HrCaseDocumentState.WITHDRAWN
    assert withdrawn.is_received is False
    assert withdrawn.received_on == date(2026, 9, 2)
    assert withdrawn.withdrawn_on == date(2026, 9, 3)
    assert withdrawn.artifact_ref == "document-17"


def test_receipt_domain_refuses_incoherent_dates_and_states():
    with pytest.raises(ValueError):
        HrCaseDocumentReceipt(
            case_id="case-1",
            document_code="justificatif",
            state=HrCaseDocumentState.WITHDRAWN,
            received_on=date(2026, 9, 2),
            withdrawn_on=None,
        )

    receipt = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
    )
    with pytest.raises(ValueError):
        receipt.withdraw(withdrawn_on=date(2026, 9, 1))


def test_checklist_counts_receipts_without_claiming_legal_validity():
    repository = FakeRepository(_case())
    repository.receipts[("case-1", "annexe")] = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="annexe",
        received_on=date(2026, 9, 2),
    )

    checklist = _service(repository).build_checklist(
        structure_ref="structure-a",
        case_id="case-1",
    )

    assert checklist.expected_count == 2
    assert checklist.required_count == 1
    assert checklist.received_count == 1
    assert checklist.required_missing_count == 1
    assert checklist.complete_administratively is False
    assert [row.expected_document.code for row in checklist.rows] == [
        "justificatif",
        "annexe",
    ]


def test_record_received_targets_case_history_and_only_expected_document():
    repository = FakeRepository(_case())
    service = _service(repository)

    result = service.record_received(
        structure_ref="structure-a",
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
        artifact_ref="document-17",
        actor_ref="user-1",
    )

    assert result.receipt.state is HrCaseDocumentState.RECEIVED
    assert result.receipt.artifact_ref == "document-17"
    assert result.event.kind is HrEventKind.DOCUMENT_ADDED
    assert result.event.target_kind is HrEventTargetKind.CASE
    assert result.event.target_ref == "case-1"
    fields = {field.key: field.value for field in result.event.fields}
    assert fields == {
        "document_code": "justificatif",
        "document_label": "Justificatif",
        "required": "true",
        "received_on": "2026-09-02",
    }
    assert "document-17" not in {field.value for field in result.event.fields}

    with pytest.raises(ValueError, match="déjà enregistrée"):
        service.record_received(
            structure_ref="structure-a",
            case_id="case-1",
            document_code="justificatif",
            received_on=date(2026, 9, 2),
        )

    with pytest.raises(ValueError, match="n'est pas déclarée"):
        service.record_received(
            structure_ref="structure-a",
            case_id="case-1",
            document_code="inconnue",
            received_on=date(2026, 9, 2),
        )


def test_withdraw_marks_projection_and_appends_document_removed_event():
    repository = FakeRepository(_case())
    repository.receipts[("case-1", "justificatif")] = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
        artifact_ref="document-17",
    )
    service = _service(repository)

    result = service.withdraw_received(
        structure_ref="structure-a",
        case_id="case-1",
        document_code="justificatif",
        withdrawn_on=date(2026, 9, 3),
    )

    assert result.receipt.state is HrCaseDocumentState.WITHDRAWN
    assert result.receipt.withdrawn_on == date(2026, 9, 3)
    assert result.event.kind is HrEventKind.DOCUMENT_REMOVED
    fields = {field.key: field.value for field in result.event.fields}
    assert fields["from_state"] == "received"
    assert fields["to_state"] == "withdrawn"


def test_closed_case_is_readable_but_document_state_cannot_change():
    repository = FakeRepository(_case(status=HrCaseStatus.ACCEPTED))
    service = _service(repository)

    checklist = service.build_checklist(
        structure_ref="structure-a",
        case_id="case-1",
    )
    assert checklist.expected_count == 2

    with pytest.raises(ValueError, match="ne peuvent plus être modifiées"):
        service.record_received(
            structure_ref="structure-a",
            case_id="case-1",
            document_code="justificatif",
            received_on=date(2026, 9, 2),
        )
