"""Intégration MariaDB : un command_id ne peut jamais désigner deux payloads."""
import os
from pathlib import Path

import pytest

mysql = pytest.importorskip("mysql.connector")

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)


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
    sql = Path("infrastructure/persistence/sql/mysql/dpae_v1.sql").read_text(encoding="utf-8")
    conn = connect()
    try:
        cur = conn.cursor()
        for statement in (part.strip() for part in sql.split(";") if part.strip()):
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


def seed_case():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tw_dpae_case "
            "(id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at,version) "
            "VALUES ('conflict-case','conflict-key','emp','contract','est',NOW(),'READY','TEAMWORKS',NOW(),7)"
        )
        conn.commit()
    finally:
        conn.close()


def request_submission(command_id, command_hash):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT command_hash,decision FROM tw_dpae_command_audit WHERE command_id=%s",
            (command_id,),
        )
        previous = cur.fetchone()
        if previous:
            if previous[0] != command_hash:
                conn.rollback()
                raise ValueError("IDEMPOTENCY_PAYLOAD_CONFLICT")
            conn.rollback()
            return "ALREADY_APPLIED"

        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id='conflict-case' FOR UPDATE")
        assert cur.fetchone() == ("READY", 7)
        cur.execute("UPDATE tw_dpae_case SET status='SUBMITTING',version=8 WHERE id='conflict-case' AND version=7")
        assert cur.rowcount == 1
        cur.execute(
            "INSERT INTO tw_dpae_case_event "
            "(id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) "
            "VALUES ('conflict-event','conflict-case','SUBMISSION_REQUESTED','READY','SUBMITTING',7,8,'USER','u1',%s,%s,NOW(),NOW())",
            (command_id, command_hash),
        )
        cur.execute(
            "INSERT INTO tw_dpae_submission "
            "(id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at) "
            "VALUES ('conflict-submission','conflict-case',1,%s,%s,'PREPARED',NOW())",
            (command_id, command_hash),
        )
        cur.execute(
            "INSERT INTO tw_dpae_command_audit "
            "(id,command_id,command_type,command_hash,actor_type,actor_id,case_id,submission_id,requested_at,decided_at,decision,case_version_seen) "
            "VALUES ('conflict-audit',%s,'RequestDpaeSubmission',%s,'USER','u1','conflict-case','conflict-submission',NOW(),NOW(),'APPLIED',7)",
            (command_id, command_hash),
        )
        conn.commit()
        return "APPLIED"
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def durable_state(command_id):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id='conflict-case'")
        case = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id='conflict-case'")
        events = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id='conflict-case'")
        submissions = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*),MIN(command_hash),MIN(decision) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        audit = cur.fetchone()
        return case, events, submissions, audit
    finally:
        conn.close()


def test_same_command_id_with_different_payload_is_rejected_without_new_mutation():
    seed_case()
    command_id = "cmd-payload-conflict"
    original_hash = "a" * 64
    divergent_hash = "b" * 64

    assert request_submission(command_id, original_hash) == "APPLIED"
    before = durable_state(command_id)
    assert before == (("SUBMITTING", 8), 1, 1, (1, original_hash, "APPLIED"))

    # Nouvelle connexion, même command_id mais contenu différent : refus avant toute mutation.
    with pytest.raises(ValueError, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        request_submission(command_id, divergent_hash)

    # L'état durable initial est strictement inchangé : aucune tentative, transition ou audit bis.
    assert durable_state(command_id) == before
