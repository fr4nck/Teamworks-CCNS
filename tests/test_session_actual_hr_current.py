from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import hmac
import json
import sqlite3

import pytest

from application.services import inter_domain_delivery_hr
from application.services.session_actual_hr import SessionActualHrConsumer
from domain.employment import SessionActual, SessionActualContractError
from infrastructure.persistence.session_actual_hr_repository import (
    SessionActualHrPersistenceError,
    SessionActualHrRepository,
)

STAFF_UID = "22222222-2222-2222-2222-222222222222"
ACTUAL_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SESSION_UID = "session-canonique-1"


class SqliteDb:
    isNetwork = False

    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()

    def Close(self):
        self.connexion.close()


@pytest.fixture
def db():
    value = SqliteDb()
    value.cursor.executescript(
        """
        CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, nom TEXT);
        CREATE TABLE contrats (id INTEGER PRIMARY KEY, marker TEXT);
        CREATE TABLE assignments (id INTEGER PRIMARY KEY, marker TEXT);
        CREATE TABLE payroll (id INTEGER PRIMARY KEY, marker TEXT);
        INSERT INTO personnes VALUES (1, 'Test');
        INSERT INTO contrats VALUES (1, 'contract-safe');
        INSERT INTO assignments VALUES (1, 'planning-safe');
        INSERT INTO payroll VALUES (1, 'payroll-safe');
        """
    )
    value.connexion.commit()
    yield value
    value.Close()


def payload(revision=1, status="realisee"):
    data = {
        "contract_version": "session-actual/1",
        "event_type": "session_actual_validated",
        "actual_uuid": ACTUAL_UUID,
        "actual_revision": revision,
        "session_uid": SESSION_UID,
        "session_status": status,
        "assignment_date": "2026-09-04",
        "validated_at": "2026-09-04T08:00:00Z",
        "actual_staff_uid": STAFF_UID,
        "actual_place_uid": "place-1",
        "actual_start_time": "09:00",
        "actual_end_time": "10:00",
        "actual_duration_minutes": 60,
        "actual_comment": "",
    }
    if status == "annulee":
        data.update(
            actual_staff_uid=None,
            actual_place_uid=None,
            actual_start_time=None,
            actual_end_time=None,
            actual_duration_minutes=None,
            actual_comment="Annulation validée",
        )
    return data


def repo_for(db):
    repo = SessionActualHrRepository(lambda: db)
    assert repo.ensure_schema(apply=True) == ()
    return repo


def test_contract_requires_strict_integer_revision_and_coherent_duration():
    for bad in (True, 1.9, "1", 0):
        data = payload()
        data["actual_revision"] = bad
        with pytest.raises(SessionActualContractError):
            SessionActual.from_payload(data)
    bad_duration = payload()
    bad_duration["actual_duration_minutes"] = 59
    with pytest.raises(SessionActualContractError):
        SessionActual.from_payload(bad_duration)


def test_cancelled_session_carries_no_actual_staff_or_times():
    data = payload(status="annulee")
    assert SessionActual.from_payload(data).actual_duration_minutes is None
    data["actual_staff_uid"] = STAFF_UID
    with pytest.raises(SessionActualContractError):
        SessionActual.from_payload(data)


def test_schema_is_explicit_idempotent_and_mysql55_compatible(db):
    repo = SessionActualHrRepository(lambda: db)
    assert set(repo.ensure_schema(False)) == {
        "tw_hr_person_uid_mapping", "tw_session_actual_inbox", "tw_session_actual_work"
    }
    assert repo.ensure_schema(True) == ()
    assert repo.ensure_schema(True) == ()
    sqlite_ddl = "\n".join(repo._schema_statements(False))
    network_ddl = "\n".join(repo._schema_statements(True))
    assert "AUTOINCREMENT" in sqlite_ddl
    assert "AUTO_INCREMENT" in network_ddl
    assert "DEFAULT CURRENT_TIMESTAMP" not in network_ddl


def test_mapping_requires_existing_person_and_never_creates_employee(db):
    repo = repo_for(db)
    with pytest.raises(SessionActualHrPersistenceError):
        repo.register_person_uid(STAFF_UID, 99)
    assert db.cursor.execute("SELECT count(*) FROM personnes").fetchone()[0] == 1
    assert repo.register_person_uid(STAFF_UID, 1) == 1
    assert repo.register_person_uid(STAFF_UID, 1) == 1
    assert repo.resolve_person_uid(STAFF_UID) == 1


def test_apply_exact_replay_and_no_effect_on_planning_contracts_or_payroll(db):
    repo = repo_for(db)
    repo.register_person_uid(STAFF_UID, 1)
    first = repo.receive(payload(), "idem-1")
    replay = repo.receive(payload(), "idem-1")
    assert first.status == "applied"
    assert replay.status == "replayed"
    assert db.cursor.execute("SELECT count(*) FROM tw_session_actual_work").fetchone()[0] == 1
    assert db.cursor.execute("SELECT count(*) FROM tw_session_actual_inbox").fetchone()[0] == 1
    assert db.cursor.execute("SELECT marker FROM contrats").fetchone()[0] == "contract-safe"
    assert db.cursor.execute("SELECT marker FROM assignments").fetchone()[0] == "planning-safe"
    assert db.cursor.execute("SELECT marker FROM payroll").fetchone()[0] == "payroll-safe"


def test_unknown_staff_uid_is_rejected_without_business_write(db):
    repo = repo_for(db)
    with pytest.raises(SessionActualHrPersistenceError, match="UID RH inconnu"):
        repo.receive(payload(), "idem-unknown")
    assert db.cursor.execute("SELECT count(*) FROM tw_session_actual_work").fetchone()[0] == 0
    assert db.cursor.execute("SELECT count(*) FROM tw_session_actual_inbox").fetchone()[0] == 0


def test_newer_revision_updates_and_older_new_key_is_rejected(db):
    repo = repo_for(db)
    repo.register_person_uid(STAFF_UID, 1)
    repo.receive(payload(1), "idem-r1")
    revised = payload(2)
    revised["actual_end_time"] = "10:15"
    revised["actual_duration_minutes"] = 75
    assert repo.receive(revised, "idem-r2").status == "applied"
    row = db.cursor.execute(
        "SELECT actual_revision,actual_end_time,actual_duration_minutes FROM tw_session_actual_work"
    ).fetchone()
    assert row == (2, "10:15", 75)
    with pytest.raises(SessionActualHrPersistenceError, match="obsolète"):
        repo.receive(payload(1), "idem-r1-new-key")


def test_same_revision_divergent_payload_is_rejected(db):
    repo = repo_for(db)
    repo.register_person_uid(STAFF_UID, 1)
    repo.receive(payload(1), "idem-a")
    divergent = payload(1)
    divergent["actual_comment"] = "diverge"
    with pytest.raises(SessionActualHrPersistenceError, match="révision déjà reçue"):
        repo.receive(divergent, "idem-b")


def test_cancellation_revision_clears_actual_fields_but_preserves_person_trace(db):
    repo = repo_for(db)
    repo.register_person_uid(STAFF_UID, 1)
    repo.receive(payload(1), "idem-r1")
    repo.receive(payload(2, status="annulee"), "idem-r2")
    row = db.cursor.execute(
        "SELECT IDpersonne,actual_staff_uid,actual_place_uid,actual_start_time,actual_end_time,actual_duration_minutes,session_status FROM tw_session_actual_work"
    ).fetchone()
    assert row == (1, None, None, None, None, None, "annulee")


def test_wrong_source_domain_is_rejected(db):
    repo = repo_for(db)
    with pytest.raises(SessionActualHrPersistenceError, match="domaine source"):
        repo.receive(payload(), "idem", source_domain="wrong")


def test_failure_between_work_and_inbox_rolls_back_atomically(db):
    repo = repo_for(db)
    repo.register_person_uid(STAFF_UID, 1)
    original = repo._execute

    def fail_inbox(sql, params=()):
        if sql.lstrip().startswith("INSERT INTO tw_session_actual_inbox"):
            raise RuntimeError("simulated inbox failure")
        return original(sql, params)

    repo._execute = fail_inbox
    with pytest.raises(SessionActualHrPersistenceError, match="transactionnel"):
        repo.receive(payload(), "idem-fail")
    assert db.cursor.execute("SELECT count(*) FROM tw_session_actual_work").fetchone()[0] == 0
    assert db.cursor.execute("SELECT count(*) FROM tw_session_actual_inbox").fetchone()[0] == 0


def test_concurrent_newer_revision_wins(db):
    repo = repo_for(db)
    repo.register_person_uid(STAFF_UID, 1)
    repo.receive(payload(1), "idem-r1")
    original = repo._execute
    fired = {"value": False}

    def race(sql, params=()):
        if not fired["value"] and sql.lstrip().startswith("UPDATE tw_session_actual_work SET"):
            fired["value"] = True
            db.cursor.execute(
                "UPDATE tw_session_actual_work SET actual_revision=3,payload_sha256='newer' WHERE session_uid=?",
                (SESSION_UID,),
            )
            db.connexion.commit()
        return original(sql, params)

    repo._execute = race
    with pytest.raises(SessionActualHrPersistenceError, match="concurremment"):
        repo.receive(payload(2), "idem-r2")
    assert db.cursor.execute("SELECT actual_revision FROM tw_session_actual_work").fetchone()[0] == 3


def signed_delivery(data, secret=b"k" * 32, key_id="kid-1"):
    envelope = {
        "envelope_version": "inter-domain-delivery/1",
        "source_domain": "operations_portal",
        "target_domain": "hr_employment",
        "contract_version": "session-actual/1",
        "event_type": "session_actual_validated",
        "idempotence_key": "idem-signed",
        "correlation_id": ACTUAL_UUID,
        "occurred_at": "2026-09-04T08:00:00Z",
        "key_id": key_id,
        "payload": data,
    }
    message = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return {"envelope": envelope, "signature": signature}


def test_signed_delivery_vector_tamper_rotation_and_full_chain(db):
    repo = repo_for(db)
    repo.register_person_uid(STAFF_UID, 1)
    consumer = SessionActualHrConsumer(repo)
    secret = b"k" * 32
    delivery = signed_delivery(payload(), secret)
    assert inter_domain_delivery_hr.receive_signed_delivery(
        delivery, {"kid-1": secret}, consumer=consumer
    )["status"] == "accepted"
    assert inter_domain_delivery_hr.receive_signed_delivery(
        delivery, {"kid-1": secret}, consumer=consumer
    )["status"] == "replayed"

    tampered = deepcopy(delivery)
    tampered["envelope"]["payload"]["actual_comment"] = "tampered"
    assert inter_domain_delivery_hr.receive_signed_delivery(
        tampered, {"kid-1": secret}, consumer=consumer
    )["status"] == "rejected"
    assert inter_domain_delivery_hr.receive_signed_delivery(
        delivery, {"other": b"z" * 32}, consumer=consumer
    )["status"] == "rejected"
