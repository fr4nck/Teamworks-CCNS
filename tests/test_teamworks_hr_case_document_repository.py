import sqlite3
from datetime import date, datetime, timezone

import pytest

from domain.hr_connections import (
    ExpectedDocument,
    HrAuditEvent,
    HrAuditField,
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
from infrastructure.persistence import (
    StaleTeamworksHrCaseDocumentStateError,
    TeamworksHrCaseDocumentRepository,
    TeamworksHrCasesRepository,
)


class LocalGestionDb:
    def __init__(self, path):
        self.isNetwork = False
        self.connexion = sqlite3.connect(path)
        self.cursor = self.connexion.cursor()

    def Commit(self):
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


def _factory(path):
    return lambda: LocalGestionDb(path)


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
                )
            }
        ),
    )


def _event(event_id, kind):
    return HrAuditEvent.create(
        event_id=event_id,
        kind=kind,
        target_kind=HrEventTargetKind.CASE,
        target_ref="case-1",
        occurred_at=datetime(2026, 9, 2, 8, 30, tzinfo=timezone.utc),
        actor_ref="user-1",
        source="teamworks-ui",
        fields=(
            HrAuditField.create(key="document_code", value="justificatif"),
        ),
    )


def _prepare(path, status=HrCaseStatus.TODO):
    factory = _factory(path)
    cases = TeamworksHrCasesRepository(db_factory=factory)
    cases.save_case(structure_ref="structure-a", case=_case(status=status))
    repository = TeamworksHrCaseDocumentRepository(db_factory=factory)
    return factory, cases, repository


def test_schema_is_additive_versioned_and_idempotent(tmp_path):
    path = tmp_path / "documents.sqlite"
    factory, _cases, repository = _prepare(path)

    assert repository.schema_version() == 1
    repository.ensure_schema()
    assert repository.schema_version() == 1

    db = factory()
    try:
        tables = {
            row[0]
            for row in db.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        indexes = {
            row[0]
            for row in db.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }
    finally:
        db.Close()

    assert "tw_hr_case_document_receipts" in tables
    assert "idx_tw_hr_case_document_state" in indexes


def test_received_projection_and_case_history_are_persisted_atomically(tmp_path):
    path = tmp_path / "documents.sqlite"
    _factory_, cases, repository = _prepare(path)
    receipt = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
        artifact_ref="document-17",
        source="teamworks-ui",
    )
    event = _event("evt-add", HrEventKind.DOCUMENT_ADDED)

    persisted = repository.persist_receipt_change(
        structure_ref="structure-a",
        expected_state=None,
        receipt=receipt,
        event=event,
    )

    assert persisted == receipt
    assert repository.get_receipt(
        structure_ref="structure-a",
        case_id="case-1",
        document_code="justificatif",
    ) == receipt
    assert repository.list_receipts(
        structure_ref="structure-a",
        case_id="case-1",
    ) == (receipt,)
    events = cases.list_events(
        structure_ref="structure-a",
        target_kind=HrEventTargetKind.CASE,
        target_ref="case-1",
    )
    assert event in events


def test_withdraw_updates_projection_without_deleting_receipt(tmp_path):
    path = tmp_path / "documents.sqlite"
    factory, cases, repository = _prepare(path)
    received = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
        artifact_ref="document-17",
    )
    repository.persist_receipt_change(
        structure_ref="structure-a",
        expected_state=None,
        receipt=received,
        event=_event("evt-add", HrEventKind.DOCUMENT_ADDED),
    )
    withdrawn = received.withdraw(withdrawn_on=date(2026, 9, 3))

    repository.persist_receipt_change(
        structure_ref="structure-a",
        expected_state=HrCaseDocumentState.RECEIVED,
        receipt=withdrawn,
        event=_event("evt-remove", HrEventKind.DOCUMENT_REMOVED),
    )

    assert repository.get_receipt(
        structure_ref="structure-a",
        case_id="case-1",
        document_code="justificatif",
    ) == withdrawn
    db = factory()
    try:
        count = db.cursor.execute(
            "SELECT COUNT(*) FROM tw_hr_case_document_receipts "
            "WHERE structure_ref = ? AND case_id = ? AND document_code = ?",
            ("structure-a", "case-1", "justificatif"),
        ).fetchone()[0]
    finally:
        db.Close()
    assert count == 1
    assert len(
        cases.list_events(
            structure_ref="structure-a",
            target_kind=HrEventTargetKind.CASE,
            target_ref="case-1",
        )
    ) == 2


def test_stale_state_rolls_back_projection_and_event(tmp_path):
    path = tmp_path / "documents.sqlite"
    _factory_, cases, repository = _prepare(path)
    received = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
    )
    repository.persist_receipt_change(
        structure_ref="structure-a",
        expected_state=None,
        receipt=received,
        event=_event("evt-add", HrEventKind.DOCUMENT_ADDED),
    )
    attempted = received.withdraw(withdrawn_on=date(2026, 9, 3))

    with pytest.raises(StaleTeamworksHrCaseDocumentStateError):
        repository.persist_receipt_change(
            structure_ref="structure-a",
            expected_state=HrCaseDocumentState.WITHDRAWN,
            receipt=attempted,
            event=_event("evt-stale", HrEventKind.DOCUMENT_REMOVED),
        )

    assert repository.get_receipt(
        structure_ref="structure-a",
        case_id="case-1",
        document_code="justificatif",
    ) == received
    assert cases.get_event(structure_ref="structure-a", event_id="evt-stale") is None


def test_closed_case_and_unknown_expected_document_are_rejected_without_audit(tmp_path):
    closed_path = tmp_path / "closed.sqlite"
    _factory_, closed_cases, closed_repository = _prepare(
        closed_path,
        status=HrCaseStatus.ACCEPTED,
    )
    receipt = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
    )

    with pytest.raises(StaleTeamworksHrCaseDocumentStateError):
        closed_repository.persist_receipt_change(
            structure_ref="structure-a",
            expected_state=None,
            receipt=receipt,
            event=_event("evt-closed", HrEventKind.DOCUMENT_ADDED),
        )
    assert closed_cases.get_event(
        structure_ref="structure-a",
        event_id="evt-closed",
    ) is None

    unknown_path = tmp_path / "unknown.sqlite"
    _factory_, cases, repository = _prepare(unknown_path)
    unknown = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="inconnue",
        received_on=date(2026, 9, 2),
    )
    unknown_event = HrAuditEvent.create(
        event_id="evt-unknown",
        kind=HrEventKind.DOCUMENT_ADDED,
        target_kind=HrEventTargetKind.CASE,
        target_ref="case-1",
        occurred_at=datetime(2026, 9, 2, 8, 30, tzinfo=timezone.utc),
        fields=(HrAuditField.create(key="document_code", value="inconnue"),),
    )
    with pytest.raises(ValueError, match="n'est pas déclarée"):
        repository.persist_receipt_change(
            structure_ref="structure-a",
            expected_state=None,
            receipt=unknown,
            event=unknown_event,
        )
    assert cases.get_event(
        structure_ref="structure-a",
        event_id="evt-unknown",
    ) is None


def test_event_must_describe_same_document_and_matching_action(tmp_path):
    path = tmp_path / "validation.sqlite"
    _factory_, _cases, repository = _prepare(path)
    receipt = HrCaseDocumentReceipt.received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
    )

    with pytest.raises(ValueError, match="ne correspond pas"):
        repository.persist_receipt_change(
            structure_ref="structure-a",
            expected_state=None,
            receipt=receipt,
            event=_event("evt-wrong-kind", HrEventKind.DOCUMENT_REMOVED),
        )
