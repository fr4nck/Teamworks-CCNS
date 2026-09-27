"""Idempotence DPAE V2 après états partiels durables et redémarrage.

Ces états sont injectés volontairement pour prouver qu'une identité de commande
déjà durable ne peut pas être réinterprétée contre un autre Case/snapshot.
"""
import os
from pathlib import Path

import pytest

mysql = pytest.importorskip("mysql.connector")

from application.services.dpae_service import DpaeService, SubmitDpae
from infrastructure.persistence.dpae_mysql import DpaeMariaDbAdapter, IdempotencyPayloadConflict

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)

SCHEMA = Path("infrastructure/persistence/sql/mysql/dpae_v1.sql")


def connect():
    return mysql.connect(
        host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")),
        user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""),
        database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False,
    )


@pytest.fixture(scope="module", autouse=True)
def install_schema():
    conn = connect()
    try:
        cur = conn.cursor()
        for statement in (part.strip() for part in SCHEMA.read_text(encoding="utf-8").split(";")):
            if statement:
                cur.execute(statement)
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def clean_tables():
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for table in (
            "tw_dpae_return_effect", "tw_dpae_current_correlation", "tw_dpae_correlation_decision",
            "tw_dpae_return", "tw_dpae_case_submission_lock", "tw_dpae_submission",
            "tw_dpae_command_audit", "tw_dpae_case_event", "tw_dpae_snapshot", "tw_dpae_case",
        ):
            cur.execute("DELETE FROM " + table)
        cur.execute("SET FOREIGN_KEY_CHECKS=1"); conn.commit()
    finally:
        conn.close()


def seed_case(cur, suffix):
    case_id = "partial-case-" + suffix
    snapshot_id = "partial-snapshot-" + suffix
    payload_hash = "3" * 64
    cur.execute(
        "INSERT INTO tw_dpae_case (id,case_key,contract_id,status,origin,created_at,version) "
        "VALUES (%s,%s,%s,'READY','TEAMWORKS',NOW(),0)",
        (case_id, case_id + "-key", "contract-" + suffix),
    )
    cur.execute(
        "INSERT INTO tw_dpae_snapshot "
        "(id,case_id,contract_id,rules_version,source_fingerprint,canonical_payload,payload_hash,created_at) "
        "VALUES (%s,%s,%s,'test-rules',%s,%s,%s,NOW())",
        (snapshot_id, case_id, "contract-" + suffix, "f" * 64, '{"case":"%s"}' % suffix, payload_hash),
    )
    return case_id, snapshot_id, payload_hash


def seed_partial_state(failure_point, command_id):
    submission_id = "partial-submission-" + failure_point
    conn = connect()
    try:
        cur = conn.cursor()
        case_id, snapshot_id, payload_hash = seed_case(cur, failure_point)
        command_hash = DpaeMariaDbAdapter._hash(case_id, snapshot_id, payload_hash)
        audit_submission_id = None if failure_point == "after_audit_commit" else submission_id
        cur.execute(
            "INSERT INTO tw_dpae_command_audit "
            "(id,command_id,command_type,command_hash,actor_type,actor_id,case_id,submission_id,requested_at,decided_at,decision,case_version_seen) "
            "VALUES (%s,%s,'SubmitDpae',%s,'USER','accounting-user',%s,%s,NOW(),NOW(),'APPLIED',0)",
            ("audit-" + failure_point, command_id, command_hash, case_id, audit_submission_id),
        )
        conn.commit()
        if failure_point in ("after_submission_commit", "after_case_event_commit"):
            cur.execute(
                "INSERT INTO tw_dpae_submission "
                "(id,case_id,snapshot_id,attempt_no,idempotency_key,payload_hash,state,created_at,version) "
                "VALUES (%s,%s,%s,1,%s,%s,'PREPARED',NOW(),0)",
                (submission_id, case_id, snapshot_id, command_id, payload_hash),
            )
            conn.commit()
        if failure_point == "after_case_event_commit":
            cur.execute(
                "INSERT INTO tw_dpae_case_event "
                "(id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) "
                "VALUES (%s,%s,'SUBMISSION_REQUESTED','READY','SUBMITTING',0,1,'USER','accounting-user',%s,%s,NOW(),NOW())",
                ("event-" + failure_point, case_id, command_id, command_hash),
            )
            conn.commit()
    finally:
        conn.close()
    return case_id, snapshot_id, submission_id, command_hash


def seed_conflicting_case(suffix):
    conn = connect()
    try:
        cur = conn.cursor(); case_id, _, _ = seed_case(cur, "conflict-" + suffix); conn.commit(); return case_id
    finally:
        conn.close()


def snapshot(case_id, command_id):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,)); case = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); audits = cur.fetchone()[0]
        cur.execute("SELECT command_hash,decision,case_id,submission_id FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); audit = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,)); submissions = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,)); events = cur.fetchone()[0]
        return case, audits, audit, submissions, events
    finally:
        conn.close()


@pytest.mark.parametrize(
    "failure_point,expected_submissions,expected_events",
    [("after_audit_commit", 0, 0), ("after_submission_commit", 1, 0), ("after_case_event_commit", 1, 1)],
)
def test_conflicting_replay_after_partial_durable_state_and_restart_keeps_original_audit(
    failure_point, expected_submissions, expected_events
):
    command_id = "partial-restart-command-" + failure_point
    case_id, _, _, original_hash = seed_partial_state(failure_point, command_id)
    before = snapshot(case_id, command_id)
    assert before[0] == ("READY", 0)
    assert before[1] == 1
    assert before[2][0:3] == (original_hash, "APPLIED", case_id)
    assert before[3] == expected_submissions
    assert before[4] == expected_events

    conflicting_case_id = seed_conflicting_case(failure_point)
    restarted = DpaeService(DpaeMariaDbAdapter(connect))
    with pytest.raises(IdempotencyPayloadConflict, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        restarted.submit(SubmitDpae(command_id=command_id, case_id=conflicting_case_id, actor_id="accounting-user"))

    assert snapshot(case_id, command_id) == before
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,)); assert cur.fetchone()[0] == expected_submissions
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,)); assert cur.fetchone()[0] == expected_events
    finally:
        conn.close()
