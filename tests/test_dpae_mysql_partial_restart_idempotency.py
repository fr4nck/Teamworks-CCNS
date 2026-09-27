"""Idempotence DPAE après états partiels durables et redémarrage.

Ces états sont injectés volontairement : le chemin normal doit conserver
Case + Submission + CaseEvent + CommandAudit dans une transaction atomique.
Le but est de prouver qu'un état historique/endommagé contenant déjà l'identité
de commande ne peut pas être réinterprété avec un autre payload après restart.
"""
import os
from datetime import datetime
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
        host=os.environ["DPAE_MYSQL_HOST"],
        port=int(os.getenv("DPAE_MYSQL_PORT", "3306")),
        user=os.environ["DPAE_MYSQL_USER"],
        password=os.getenv("DPAE_MYSQL_PASSWORD", ""),
        database=os.environ["DPAE_MYSQL_DATABASE"],
        use_pure=True,
        autocommit=False,
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
        cur = conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for table in (
            "tw_dpae_return_effect", "tw_dpae_current_correlation",
            "tw_dpae_correlation_decision", "tw_dpae_return",
            "tw_dpae_case_submission_lock", "tw_dpae_submission",
            "tw_dpae_command_audit", "tw_dpae_case_event", "tw_dpae_case",
        ):
            cur.execute("DELETE FROM " + table)
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
    finally:
        conn.close()


def seed_partial_state(failure_point, command_id, original_hash):
    case_id = "partial-case-" + failure_point
    submission_id = "partial-submission-" + failure_point
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tw_dpae_case "
            "(id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at,version) "
            "VALUES (%s,%s,'employee-partial','contract-partial','est-partial',%s,'READY','TEAMWORKS',NOW(),0)",
            (case_id, case_id + "-key", datetime(2026, 10, 18, 8, 0)),
        )

        # L'identité durable de la commande existe dès le premier point.
        # submission_id est nullable dans l'audit tant que la Submission n'existe pas.
        audit_submission_id = None if failure_point == "after_audit_commit" else submission_id
        cur.execute(
            "INSERT INTO tw_dpae_command_audit "
            "(id,command_id,command_type,command_hash,actor_type,actor_id,case_id,submission_id,requested_at,decided_at,decision,case_version_seen) "
            "VALUES (%s,%s,'SubmitDpae',%s,'USER','accounting-user',%s,%s,NOW(),NOW(),'APPLIED',0)",
            ("audit-" + failure_point, command_id, original_hash, case_id, audit_submission_id),
        )
        conn.commit()

        if failure_point in ("after_submission_commit", "after_case_event_commit"):
            cur.execute(
                "INSERT INTO tw_dpae_submission "
                "(id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at,version) "
                "VALUES (%s,%s,1,%s,%s,'PREPARED',NOW(),0)",
                (submission_id, case_id, command_id, original_hash),
            )
            conn.commit()

        if failure_point == "after_case_event_commit":
            cur.execute(
                "INSERT INTO tw_dpae_case_event "
                "(id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) "
                "VALUES (%s,%s,'SUBMISSION_REQUESTED','READY','SUBMITTING',0,1,'USER','accounting-user',%s,%s,NOW(),NOW())",
                ("event-" + failure_point, case_id, command_id, original_hash),
            )
            conn.commit()
    finally:
        conn.close()
    return case_id, submission_id


def snapshot(case_id, command_id):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        case = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        audits = cur.fetchone()[0]
        cur.execute("SELECT command_hash,decision,case_id,submission_id FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        audit = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        submissions = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        events = cur.fetchone()[0]
        return case, audits, audit, submissions, events
    finally:
        conn.close()


@pytest.mark.parametrize(
    "failure_point,expected_submissions,expected_events",
    [
        ("after_audit_commit", 0, 0),
        ("after_submission_commit", 1, 0),
        ("after_case_event_commit", 1, 1),
    ],
)
def test_conflicting_replay_after_partial_durable_state_and_restart_keeps_original_audit(
    failure_point, expected_submissions, expected_events
):
    command_id = "partial-restart-command-" + failure_point
    original_hash = "3" * 64
    conflicting_hash = "4" * 64
    case_id, _ = seed_partial_state(failure_point, command_id, original_hash)

    before = snapshot(case_id, command_id)
    assert before[0] == ("READY", 0)
    assert before[1] == 1
    assert before[2][0:3] == (original_hash, "APPLIED", case_id)
    assert before[3] == expected_submissions
    assert before[4] == expected_events

    # Redémarrage complet : aucune connexion ni instance du processus ayant
    # produit l'état partiel n'est réutilisée.
    restarted = DpaeService(DpaeMariaDbAdapter(connect))
    with pytest.raises(IdempotencyPayloadConflict, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        restarted.submit(SubmitDpae(
            command_id=command_id,
            case_id=case_id,
            payload_hash=conflicting_hash,
            actor_id="accounting-user",
        ))

    after = snapshot(case_id, command_id)
    assert after == before

    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s AND command_hash=%s", (command_id, conflicting_hash))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == expected_submissions
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == expected_events
        if expected_submissions:
            cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s AND payload_hash=%s", (case_id, original_hash))
            assert cur.fetchone()[0] == 1
            cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s AND payload_hash=%s", (case_id, conflicting_hash))
            assert cur.fetchone()[0] == 0
    finally:
        conn.close()
