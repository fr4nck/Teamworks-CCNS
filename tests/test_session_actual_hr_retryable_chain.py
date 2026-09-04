from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3

from application.services.inter_domain_mailbox_client_hr import synchronize_mailbox
from application.services.session_actual_hr import SessionActualHrConsumer
from infrastructure.persistence.session_actual_hr_repository import SessionActualHrRepository

STAFF_UID = "22222222-2222-2222-2222-222222222222"
ACTUAL_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SESSION_UID = "session-canonique-retryable"
IDEMPOTENCE = "session-actual:retryable:r1:hr_employment"
CORRELATION = ACTUAL_UUID
DELIVERY_ID = "33333333-3333-3333-3333-333333333333"
SECRET = b"k" * 32
KEY_ID = "kid-1"


class SqliteDb:
    isNetwork = False

    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()

    def Close(self):
        self.connexion.close()


class FakeTransport:
    def __init__(self, item):
        self.item = item
        self.acks = []

    def claim(self, limit=20):
        return (self.item,)

    def acknowledge(self, delivery_id, receipt):
        self.acks.append((delivery_id, dict(receipt)))
        return {"status": receipt["status"]}


def payload():
    return {
        "contract_version": "session-actual/1",
        "event_type": "session_actual_validated",
        "actual_uuid": ACTUAL_UUID,
        "actual_revision": 1,
        "session_uid": SESSION_UID,
        "session_status": "realisee",
        "assignment_date": "2026-09-04",
        "validated_at": "audit-token-non-temporel",
        "actual_staff_uid": STAFF_UID,
        "actual_place_uid": "place-1",
        "actual_start_time": "09:00",
        "actual_end_time": "10:00",
        "actual_duration_minutes": 60,
        "actual_comment": "",
    }


def signed_delivery():
    envelope = {
        "envelope_version": "inter-domain-delivery/1",
        "source_domain": "operations_portal",
        "target_domain": "hr_employment",
        "contract_version": "session-actual/1",
        "event_type": "session_actual_validated",
        "idempotence_key": IDEMPOTENCE,
        "correlation_id": CORRELATION,
        "occurred_at": "2026-09-04T08:00:00Z",
        "key_id": KEY_ID,
        "payload": payload(),
    }
    message = json.dumps(
        envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    signature = hmac.new(SECRET, message, hashlib.sha256).hexdigest()
    return {"envelope": envelope, "signature": signature}


def mailbox_item():
    return {
        "mailbox_version": "inter-domain-mailbox-pull/1",
        "delivery_id": DELIVERY_ID,
        "target_domain": "hr_employment",
        "idempotence_key": IDEMPOTENCE,
        "correlation_id": CORRELATION,
        "attempts": 1,
        "signed_delivery": signed_delivery(),
    }


def test_repository_transaction_failure_is_acked_retryable_end_to_end():
    db = SqliteDb()
    try:
        db.cursor.execute("CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, nom TEXT)")
        db.cursor.execute("INSERT INTO personnes VALUES (1, 'Test')")
        db.connexion.commit()

        repository = SessionActualHrRepository(lambda: db)
        assert repository.ensure_schema(apply=True) == ()
        assert repository.register_person_uid(STAFF_UID, 1) == 1

        # Le moteur SQLite lui-même refuse l'écriture de l'inbox. L'INSERT du
        # journal courant est autorisé, puis doit être annulé par le rollback.
        def deny_inbox_insert(action, arg1, arg2, database, source):
            if action == sqlite3.SQLITE_INSERT and arg1 == "tw_session_actual_inbox":
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        db.connexion.set_authorizer(deny_inbox_insert)
        consumer = SessionActualHrConsumer(repository)
        transport = FakeTransport(mailbox_item())

        summary = synchronize_mailbox(
            transport,
            {KEY_ID: SECRET},
            consumer=consumer,
        )

        assert summary["retryable"] == 1
        assert summary["rejected"] == 0
        assert summary["acked"] == 1
        assert transport.acks[0][0] == DELIVERY_ID
        receipt = transport.acks[0][1]
        assert receipt["status"] == "retryable"
        assert receipt["idempotence_key"] == IDEMPOTENCE
        assert receipt["correlation_id"] == CORRELATION
        assert "SessionActualHrTechnicalError" in receipt["detail"]
        assert "transactionnel" in receipt["detail"]
        assert db.cursor.execute("SELECT count(*) FROM tw_session_actual_work").fetchone()[0] == 0
        assert db.cursor.execute("SELECT count(*) FROM tw_session_actual_inbox").fetchone()[0] == 0
    finally:
        db.Close()


def test_missing_hr_schema_is_acked_retryable_not_rejected():
    db = SqliteDb()
    try:
        # Le poste n'a pas encore appliqué les migrations RH : ce n'est pas un
        # défaut permanent du message et la mailbox doit pouvoir le rejouer.
        db.cursor.execute("CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, nom TEXT)")
        db.connexion.commit()

        repository = SessionActualHrRepository(lambda: db)
        consumer = SessionActualHrConsumer(repository)
        transport = FakeTransport(mailbox_item())

        summary = synchronize_mailbox(
            transport,
            {KEY_ID: SECRET},
            consumer=consumer,
        )

        assert summary["retryable"] == 1
        assert summary["rejected"] == 0
        assert summary["acked"] == 1
        receipt = transport.acks[0][1]
        assert receipt["status"] == "retryable"
        assert receipt["idempotence_key"] == IDEMPOTENCE
        assert receipt["correlation_id"] == CORRELATION
        assert "SessionActualHrTechnicalError" in receipt["detail"]
        assert "Tables du réalisé RH absentes" in receipt["detail"]
    finally:
        db.Close()
