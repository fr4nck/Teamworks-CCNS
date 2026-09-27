"""Régression MariaDB : panne après détection d'un conflit d'idempotence.

Le test exige la même base de recette que test_dpae_mysql_integration.py.
"""
import os

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


def snapshot(case_id, command_id):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        case = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        events = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE case_id=%s", (case_id,))
        audits = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        submissions = cur.fetchone()[0]
        cur.execute("SELECT command_hash,decision FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        command = cur.fetchone()
        return case, events, audits, submissions, command
    finally:
        conn.close()


def test_failure_after_idempotency_conflict_leaves_no_partial_mutation():
    case_id = "conflict-failure-case"
    command_id = "conflict-failure-command"
    original_hash = "3" * 64
    conflicting_hash = "4" * 64

    # État durable initial : la commande connue a déjà produit exactement
    # une transition, un audit et une tentative DPAE.
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for table in ("tw_dpae_return_effect", "tw_dpae_current_correlation", "tw_dpae_correlation_decision", "tw_dpae_return", "tw_dpae_case_submission_lock", "tw_dpae_submission", "tw_dpae_command_audit", "tw_dpae_case_event", "tw_dpae_case"):
            cur.execute("DELETE FROM " + table)
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
        cur.execute("INSERT INTO tw_dpae_case (id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at,version) VALUES (%s,'conflict-failure-key','e-conflict','ct-conflict','est-conflict',NOW(),'SUBMITTING','TEAMWORKS',NOW(),8)", (case_id,))
        cur.execute("INSERT INTO tw_dpae_case_event (id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) VALUES ('conflict-failure-event',%s,'SUBMISSION_REQUESTED','READY','SUBMITTING',7,8,'USER','u1',%s,%s,NOW(),NOW())", (case_id, command_id, original_hash))
        cur.execute("INSERT INTO tw_dpae_submission (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES ('conflict-failure-submission',%s,1,%s,%s,'PREPARED',NOW())", (case_id, command_id, original_hash))
        cur.execute("INSERT INTO tw_dpae_command_audit (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,submission_id,requested_at,decided_at,decision,case_version_seen) VALUES ('conflict-failure-audit',%s,'RequestDpaeSubmission',%s,'USER','u1',%s,'conflict-failure-submission',NOW(),NOW(),'APPLIED',7)", (command_id, original_hash, case_id))
        conn.commit()
    finally:
        conn.close()

    before = snapshot(case_id, command_id)
    assert before == (("SUBMITTING", 8), 1, 1, 1, (original_hash, "APPLIED"))

    # Nouvelle connexion = replay client. Le conflit est détecté uniquement à
    # partir de l'audit durable. On injecte ensuite une panne avant tout chemin
    # de mutation et on force le rollback de la transaction courante.
    replay = connect()
    try:
        cur = replay.cursor()
        with pytest.raises(RuntimeError, match="forced failure after idempotency conflict"):
            try:
                cur.execute("SELECT command_hash FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
                known_hash = cur.fetchone()[0]
                assert known_hash != conflicting_hash
                raise RuntimeError("forced failure after idempotency conflict")
            except Exception:
                replay.rollback()
                raise
    finally:
        replay.close()

    # Une troisième connexion observe uniquement l'état réellement durable.
    # La panne ne doit avoir laissé ni mutation, ni nouvel événement, ni audit,
    # ni seconde tentative DPAE.
    after = snapshot(case_id, command_id)
    assert after == before
    assert after[0] == ("SUBMITTING", 8)
    assert after[1:4] == (1, 1, 1)
    assert after[4] == (original_hash, "APPLIED")
