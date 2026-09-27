"""E2E MariaDB via le vrai DpaeService et DpaeMariaDbAdapter."""
import os
from datetime import datetime
from pathlib import Path

import pytest

mysql = pytest.importorskip("mysql.connector")

from application.services.dpae_service import DpaeService, PrepareDpae, SubmitDpae, IngestDpaeReturn
from infrastructure.persistence.dpae_mysql import DpaeMariaDbAdapter, IdempotencyPayloadConflict

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)

SCHEMA = Path("infrastructure/persistence/sql/mysql/dpae_v1.sql")


def connect():
    return mysql.connect(host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")), user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""), database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False)


@pytest.fixture(scope="module", autouse=True)
def install_schema():
    conn = connect()
    try:
        cur = conn.cursor()
        for statement in (p.strip() for p in SCHEMA.read_text(encoding="utf-8").split(";")):
            if statement: cur.execute(statement)
        conn.commit()
    finally: conn.close()


@pytest.fixture(autouse=True)
def clean_tables():
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for table in ("tw_dpae_return_effect", "tw_dpae_current_correlation", "tw_dpae_correlation_decision", "tw_dpae_return", "tw_dpae_case_submission_lock", "tw_dpae_submission", "tw_dpae_command_audit", "tw_dpae_case_event", "tw_dpae_case"):
            cur.execute("DELETE FROM " + table)
        cur.execute("SET FOREIGN_KEY_CHECKS=1"); conn.commit()
    finally: conn.close()


def test_full_dpae_e2e_uses_real_service_adapter_and_keeps_durable_evidence():
    service = DpaeService(DpaeMariaDbAdapter(connect))
    payload_hash = "c" * 64
    return_hash = "d" * 64

    prepared = service.prepare(PrepareDpae(
        command_id="e2e-prepare-001", case_key="e2e-case-key",
        employee_id="employee-e2e", contract_id="contract-e2e",
        establishment_id="est-e2e", expected_hiring_at=datetime(2026, 10, 15, 8, 30),
        actor_id="accounting-user",
    ))
    case_id = prepared["case_id"]
    assert prepared["status"] == "READY"

    submitted = service.submit(SubmitDpae(
        command_id="e2e-submit-001", case_id=case_id,
        payload_hash=payload_hash, actor_id="accounting-user",
    ))
    submission_id = submitted["submission_id"]
    assert submitted["decision"] == "APPLIED"

    # Reconnexion logique/replay : même commande, même résultat, aucune seconde tentative.
    replay_service = DpaeService(DpaeMariaDbAdapter(connect))
    replayed = replay_service.submit(SubmitDpae(
        command_id="e2e-submit-001", case_id=case_id,
        payload_hash=payload_hash, actor_id="accounting-user",
    ))
    assert replayed == {"case_id": case_id, "submission_id": submission_id, "decision": "APPLIED", "replayed": True}


def test_same_command_id_with_different_payload_is_rejected_without_new_audit_or_mutation():
    service = DpaeService(DpaeMariaDbAdapter(connect))
    original_hash = "1" * 64
    conflicting_hash = "2" * 64
    command_id = "e2e-idempotency-conflict-001"

    prepared = service.prepare(PrepareDpae(
        command_id="e2e-prepare-conflict-001", case_key="e2e-conflict-case-key",
        employee_id="employee-conflict", contract_id="contract-conflict",
        establishment_id="est-conflict", expected_hiring_at=datetime(2026, 10, 16, 9, 0),
        actor_id="accounting-user",
    ))
    case_id = prepared["case_id"]

    first = service.submit(SubmitDpae(
        command_id=command_id, case_id=case_id,
        payload_hash=original_hash, actor_id="accounting-user",
    ))
    submission_id = first["submission_id"]

    # Snapshot durable avant le rejeu conflictuel.
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        case_before = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        submissions_before = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        events_before = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        audits_before = cur.fetchone()[0]
        cur.execute("SELECT command_hash,decision,submission_id FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        audit_before = cur.fetchone()
    finally:
        conn.close()

    assert audits_before == 1
    assert audit_before == (original_hash, "APPLIED", submission_id)

    replay_service = DpaeService(DpaeMariaDbAdapter(connect))
    with pytest.raises(IdempotencyPayloadConflict, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        replay_service.submit(SubmitDpae(
            command_id=command_id, case_id=case_id,
            payload_hash=conflicting_hash, actor_id="accounting-user",
        ))

    # Le conflit est une collision avec la commande existante : il ne crée
    # ni nouvel audit, ni nouvelle tentative, ni nouvel événement, ni transition.
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        assert cur.fetchone() == case_before
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == submissions_before == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == events_before == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        assert cur.fetchone()[0] == audits_before == 1
        cur.execute("SELECT command_hash,decision,submission_id FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        assert cur.fetchone() == audit_before
        cur.execute("SELECT payload_hash FROM tw_dpae_submission WHERE id=%s", (submission_id,))
        assert cur.fetchone() == (original_hash,)
    finally:
        conn.close()
