"""Régressions MariaDB autour des conflits d'idempotence.

Les tests exigent la même base de recette que test_dpae_mysql_integration.py.
"""
import os
import threading

import pytest

mysql = pytest.importorskip("mysql.connector")

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)


def connect():
    return mysql.connect(host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")), user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""), database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False)


def clean_tables():
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for table in ("tw_dpae_return_effect", "tw_dpae_current_correlation", "tw_dpae_correlation_decision", "tw_dpae_return", "tw_dpae_case_submission_lock", "tw_dpae_submission", "tw_dpae_command_audit", "tw_dpae_case_event", "tw_dpae_case"):
            cur.execute("DELETE FROM " + table)
        cur.execute("SET FOREIGN_KEY_CHECKS=1"); conn.commit()
    finally: conn.close()


def seed_applied_command(case_id, command_id, original_hash):
    clean_tables(); conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO tw_dpae_case (id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at,version) VALUES (%s,%s,'e-conflict','ct-conflict','est-conflict',NOW(),'SUBMITTING','TEAMWORKS',NOW(),8)", (case_id, case_id + "-key"))
        cur.execute("INSERT INTO tw_dpae_case_event (id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) VALUES (%s,%s,'SUBMISSION_REQUESTED','READY','SUBMITTING',7,8,'USER','u1',%s,%s,NOW(),NOW())", (case_id + "-event", case_id, command_id, original_hash))
        cur.execute("INSERT INTO tw_dpae_submission (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES (%s,%s,1,%s,%s,'PREPARED',NOW())", (case_id + "-submission", case_id, command_id, original_hash))
        cur.execute("INSERT INTO tw_dpae_command_audit (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,submission_id,requested_at,decided_at,decision,case_version_seen) VALUES (%s,%s,'RequestDpaeSubmission',%s,'USER','u1',%s,%s,NOW(),NOW(),'APPLIED',7)", (case_id + "-audit", command_id, original_hash, case_id, case_id + "-submission")); conn.commit()
    finally: conn.close()


def snapshot(case_id, command_id):
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,)); case = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,)); events = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE case_id=%s", (case_id,)); audits = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,)); submissions = cur.fetchone()[0]
        cur.execute("SELECT command_hash,decision FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); command = cur.fetchone()
        return case, events, audits, submissions, command
    finally: conn.close()


def test_failure_after_idempotency_conflict_leaves_no_partial_mutation():
    case_id = "conflict-failure-case"; command_id = "conflict-failure-command"; original_hash = "3" * 64; conflicting_hash = "4" * 64
    seed_applied_command(case_id, command_id, original_hash); before = snapshot(case_id, command_id)
    assert before == (("SUBMITTING", 8), 1, 1, 1, (original_hash, "APPLIED"))
    replay = connect()
    try:
        cur = replay.cursor()
        with pytest.raises(RuntimeError, match="forced failure after idempotency conflict"):
            try:
                cur.execute("SELECT command_hash FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); known_hash = cur.fetchone()[0]; assert known_hash != conflicting_hash
                raise RuntimeError("forced failure after idempotency conflict")
            except Exception: replay.rollback(); raise
    finally: replay.close()
    assert snapshot(case_id, command_id) == before


def test_close_after_idempotency_conflict_then_reconnect_keeps_durable_state_unchanged():
    case_id = "conflict-reconnect-case"; command_id = "conflict-reconnect-command"; original_hash = "5" * 64; conflicting_hash = "6" * 64
    seed_applied_command(case_id, command_id, original_hash); before = snapshot(case_id, command_id)
    replay = connect()
    try:
        cur = replay.cursor(); cur.execute("SELECT command_hash,decision FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); known_hash, decision = cur.fetchone(); assert decision == "APPLIED"; assert known_hash == original_hash; assert known_hash != conflicting_hash
    finally: replay.close()
    after_reconnect = snapshot(case_id, command_id); assert after_reconnect == before
    verify = connect()
    try:
        cur = verify.cursor(); cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s AND idempotency_key=%s", (case_id, command_id)); assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*),MIN(attempt_no),MIN(payload_hash) FROM tw_dpae_submission WHERE case_id=%s", (case_id,)); assert cur.fetchone() == (1, 1, original_hash)
    finally: verify.close()


def test_idempotency_conflict_is_detected_before_case_lock_or_mutation_access():
    """Un verrou exclusif concurrent sur Case ne doit jamais bloquer le conflit."""
    case_id = "conflict-lock-order-case"; command_id = "conflict-lock-order-command"; original_hash = "7" * 64; conflicting_hash = "8" * 64
    seed_applied_command(case_id, command_id, original_hash); before = snapshot(case_id, command_id)
    lock_ready = threading.Event(); release_lock = threading.Event(); holder_errors = []
    def hold_case_write_lock():
        conn = connect()
        try:
            cur = conn.cursor(); cur.execute("UPDATE tw_dpae_case SET version=version WHERE id=%s", (case_id,)); lock_ready.set(); assert release_lock.wait(timeout=10); conn.rollback()
        except Exception as exc: holder_errors.append(exc); lock_ready.set()
        finally: conn.close()
    holder = threading.Thread(target=hold_case_write_lock, daemon=True); holder.start(); assert lock_ready.wait(timeout=5); assert not holder_errors
    replay = connect()
    try:
        cur = replay.cursor(); cur.execute("SET SESSION innodb_lock_wait_timeout=1")
        cur.execute("SELECT command_hash,decision FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); known_hash, decision = cur.fetchone()
        assert decision == "APPLIED"; assert known_hash == original_hash; assert known_hash != conflicting_hash
        replay.rollback()
    finally:
        replay.close(); release_lock.set(); holder.join(timeout=5)
    assert not holder.is_alive(); assert not holder_errors; assert snapshot(case_id, command_id) == before


def test_idempotency_conflict_reads_committed_audit_under_audit_row_lock_without_touching_case():
    case_id = "conflict-audit-lock-case"; command_id = "conflict-audit-lock-command"; original_hash = "9" * 64; conflicting_hash = "a" * 64
    seed_applied_command(case_id, command_id, original_hash); before = snapshot(case_id, command_id)
    lock_ready = threading.Event(); release_lock = threading.Event(); holder_errors = []
    def hold_audit_row_lock():
        conn = connect()
        try:
            cur = conn.cursor(); cur.execute("UPDATE tw_dpae_command_audit SET decision_code='LOCKED-BUT-UNCOMMITTED' WHERE command_id=%s", (command_id,)); lock_ready.set(); assert release_lock.wait(timeout=10); conn.rollback()
        except Exception as exc: holder_errors.append(exc); lock_ready.set()
        finally: conn.close()
    holder = threading.Thread(target=hold_audit_row_lock, daemon=True); holder.start(); assert lock_ready.wait(timeout=5); assert not holder_errors
    replay = connect()
    try:
        cur = replay.cursor(); cur.execute("SET SESSION innodb_lock_wait_timeout=1")
        cur.execute("SELECT command_hash,decision,decision_code FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); known_hash, decision, decision_code = cur.fetchone()
        assert known_hash == original_hash; assert decision == "APPLIED"; assert decision_code is None; assert known_hash != conflicting_hash; replay.rollback()
    finally:
        replay.close(); release_lock.set(); holder.join(timeout=5)
    assert not holder.is_alive(); assert not holder_errors; assert snapshot(case_id, command_id) == before
    verify = connect()
    try:
        cur = verify.cursor(); cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,)); assert cur.fetchone() == ("SUBMITTING", 8)
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,)); assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,)); assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*),MIN(decision_code) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); assert cur.fetchone() == (1, None)
    finally: verify.close()


def test_original_payload_replay_after_audit_lock_rollback_recovers_durable_result_without_mutation():
    """Après rollback du verrou audit, le replay identique relit le résultat durable."""
    case_id = "audit-rollback-replay-case"
    command_id = "audit-rollback-replay-command"
    original_hash = "b" * 64
    seed_applied_command(case_id, command_id, original_hash)
    before = snapshot(case_id, command_id)
    assert before == (("SUBMITTING", 8), 1, 1, 1, (original_hash, "APPLIED"))

    # Une session prend le verrou X sur l'audit et modifie temporairement son
    # decision_code. Le rollback doit rendre cette modification inexistante.
    holder = connect()
    try:
        cur = holder.cursor()
        cur.execute("UPDATE tw_dpae_command_audit SET decision_code='TEMPORARY-LOCK' WHERE command_id=%s", (command_id,))
        holder.rollback()
    finally:
        holder.close()

    # Reconnexion réelle après libération du verrou : même command_id + même
    # payload. Le résultat doit être récupéré depuis l'audit durable, sans
    # repasser par la mutation du Case ni recréer les artefacts de la commande.
    replay = connect()
    try:
        cur = replay.cursor()
        cur.execute("SELECT command_hash,decision,case_id,submission_id,decision_code FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        command_hash, decision, recovered_case_id, submission_id, decision_code = cur.fetchone()
        assert command_hash == original_hash
        assert decision == "APPLIED"
        assert recovered_case_id == case_id
        assert submission_id == case_id + "-submission"
        assert decision_code is None
        replay.rollback()
    finally:
        replay.close()

    # Le replay est une récupération pure : aucun événement, audit ou essai
    # supplémentaire, et aucune transition supplémentaire du dossier.
    after = snapshot(case_id, command_id)
    assert after == before
    verify = connect()
    try:
        cur = verify.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        assert cur.fetchone() == ("SUBMITTING", 8)
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s AND idempotency_key=%s", (case_id, command_id))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*),MIN(attempt_no),MIN(payload_hash) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        assert cur.fetchone() == (1, 1, original_hash)
    finally:
        verify.close()
