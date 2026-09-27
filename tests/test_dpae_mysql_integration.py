"""Tests d'intégration DPAE sur une vraie base MySQL/MariaDB.

Activer avec DPAE_MYSQL_HOST, DPAE_MYSQL_USER, DPAE_MYSQL_PASSWORD et
DPAE_MYSQL_DATABASE. Sans ces variables, la suite générale reste portable.
"""
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

mysql = pytest.importorskip("mysql.connector")

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)


def connect():
    return mysql.connect(host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")), user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""), database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False)


def statements():
    text = Path("infrastructure/persistence/sql/mysql/dpae_v1.sql").read_text(encoding="utf-8")
    return [part.strip() for part in text.split(";") if part.strip()]


@pytest.fixture(scope="module", autouse=True)
def install_schema():
    conn = connect()
    try:
        cur = conn.cursor()
        for statement in statements(): cur.execute(statement)
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


def seed_case_submission_return():
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("INSERT INTO tw_dpae_case (id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at) VALUES ('c1','case-1','e1','ct1','est1',NOW(),'IN_PROGRESS','TEAMWORKS',NOW())")
        for sid, attempt in (("s1", 1), ("s2", 2)): cur.execute("INSERT INTO tw_dpae_submission (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES (%s,'c1',%s,%s,%s,'SENDING',NOW())", (sid, attempt, "cmd-" + sid, (sid * 64)[:64]))
        cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,correlation_status) VALUES ('r1','URSSAF','RETURN_41',%s,NOW(),'ext-1','UNMATCHED')", ("a" * 64,)); conn.commit()
    finally: conn.close()


def seed_rollback_case():
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("INSERT INTO tw_dpae_case (id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at,version) VALUES ('crb','case-rollback','erb','ctrb','estrb',NOW(),'READY','TEAMWORKS',NOW(),7)"); conn.commit()
    finally: conn.close()


def execute_atomic_transition(failure_point=None):
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("SELECT status,version FROM tw_dpae_case WHERE id='crb' FOR UPDATE"); assert cur.fetchone() == ("READY", 7)
        cur.execute("UPDATE tw_dpae_case SET status='SUBMITTING',version=8 WHERE id='crb' AND version=7"); assert cur.rowcount == 1
        if failure_point == "AFTER_CASE_MUTATION": raise RuntimeError(failure_point)
        cur.execute("INSERT INTO tw_dpae_case_event (id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) VALUES ('ev-rb','crb','SUBMISSION_REQUESTED','READY','SUBMITTING',7,8,'USER','u1','cmd-rb',%s,NOW(),NOW())", ("e" * 64,))
        if failure_point == "AFTER_CASE_EVENT": raise RuntimeError(failure_point)
        cur.execute("INSERT INTO tw_dpae_command_audit (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,requested_at,decided_at,decision,case_version_seen) VALUES ('audit-rb','cmd-rb','RequestDpaeSubmission',%s,'USER','u1','crb',NOW(),NOW(),'APPLIED',7)", ("e" * 64,))
        if failure_point == "AFTER_COMMAND_AUDIT": raise RuntimeError(failure_point)
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def durable_atomic_state():
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("SELECT status,version FROM tw_dpae_case WHERE id='crb'"); case = cur.fetchone(); cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id='crb'"); events = cur.fetchone()[0]; cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id='cmd-rb'"); audits = cur.fetchone()[0]; return case, events, audits
    finally: conn.close()


def request_submission_idempotently(command_id, command_hash, lose_response=False):
    """Simule la frontière applicative : un commit durable peut être suivi d'une réponse perdue."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT command_hash,decision,case_id,submission_id,decision_code FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        previous = cur.fetchone()
        if previous:
            if previous[0] != command_hash:
                raise ValueError("IDEMPOTENCY_PAYLOAD_CONFLICT")
            conn.rollback()
            return {"replayed": True, "decision": previous[1], "case_id": previous[2], "submission_id": previous[3], "decision_code": previous[4]}
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id='crb' FOR UPDATE"); assert cur.fetchone() == ("READY", 7)
        cur.execute("UPDATE tw_dpae_case SET status='SUBMITTING',version=8 WHERE id='crb' AND version=7"); assert cur.rowcount == 1
        cur.execute("INSERT INTO tw_dpae_case_event (id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) VALUES ('ev-lost','crb','SUBMISSION_REQUESTED','READY','SUBMITTING',7,8,'USER','u1',%s,%s,NOW(),NOW())", (command_id, command_hash))
        cur.execute("INSERT INTO tw_dpae_submission (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES ('s-lost','crb',1,%s,%s,'PREPARED',NOW())", (command_id, command_hash))
        cur.execute("INSERT INTO tw_dpae_command_audit (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,submission_id,requested_at,decided_at,decision,case_version_seen) VALUES ('audit-lost',%s,'RequestDpaeSubmission',%s,'USER','u1','crb','s-lost',NOW(),NOW(),'APPLIED',7)", (command_id, command_hash)); conn.commit()
        result = {"replayed": False, "decision": "APPLIED", "case_id": "crb", "submission_id": "s-lost", "decision_code": None}
        if lose_response: raise ConnectionError("simulated response loss after successful COMMIT")
        return result
    except ConnectionError: raise
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def durable_command_counts(command_id):
    """État durable lu depuis une nouvelle connexion, comme après reconnexion client."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id='crb' AND idempotency_key=%s", (command_id,)); events = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,)); audits = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id='crb'"); submissions = cur.fetchone()[0]
        return events, audits, submissions
    finally: conn.close()


def test_unique_case_key_and_idempotency_are_enforced_by_mysql():
    seed_case_submission_return(); conn = connect()
    try:
        cur = conn.cursor()
        with pytest.raises(mysql.IntegrityError): cur.execute("INSERT INTO tw_dpae_case (id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at) VALUES ('cx','case-1','e2','ct2','est1',NOW(),'READY','TEAMWORKS',NOW())")
        conn.rollback()
        with pytest.raises(mysql.IntegrityError): cur.execute("INSERT INTO tw_dpae_submission (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES ('sx','c1',3,'cmd-s1',%s,'PREPARED',NOW())", ("b" * 64,))
    finally: conn.close()


def test_two_workers_cannot_hold_uncertain_submission_lock_for_same_case():
    seed_case_submission_return()
    def acquire(submission_id):
        conn = connect()
        try:
            cur = conn.cursor()
            try: cur.execute("INSERT INTO tw_dpae_case_submission_lock (case_id,submission_id,acquired_at) VALUES ('c1',%s,NOW())", (submission_id,)); conn.commit(); return "ACQUIRED"
            except mysql.IntegrityError: conn.rollback(); return "CONFLICT"
        finally: conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(acquire, ("s1", "s2")))
    assert sorted(results) == ["ACQUIRED", "CONFLICT"]


def test_two_operators_cannot_create_two_current_correlations():
    seed_case_submission_return()
    def confirm(args):
        decision_id, submission_id = args; conn = connect()
        try:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO tw_dpae_correlation_decision (id,return_id,action,actor_id,decided_at,candidate_submission_id) VALUES (%s,'r1','CONFIRM_MATCH',%s,NOW(),%s)", (decision_id, decision_id, submission_id)); cur.execute("INSERT INTO tw_dpae_current_correlation (return_id,submission_id,decision_id,confirmed_at) VALUES ('r1',%s,%s,NOW())", (submission_id, decision_id)); conn.commit(); return "CONFIRMED"
            except mysql.IntegrityError: conn.rollback(); return "CONFLICT"
        finally: conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(confirm, (("d1", "s1"), ("d2", "s2"))))
    assert sorted(results) == ["CONFIRMED", "CONFLICT"]


def test_return_effect_is_exactly_once_under_concurrency():
    seed_case_submission_return()
    def apply(_):
        conn = connect()
        try:
            cur = conn.cursor()
            try: cur.execute("INSERT INTO tw_dpae_return_effect (return_id,effect_type,created_at) VALUES ('r1','MARK_DPAE_REGISTERED',NOW())"); conn.commit(); return "CREATED"
            except mysql.IntegrityError: conn.rollback(); return "REPLAY"
        finally: conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(apply, range(2)))
    assert sorted(results) == ["CREATED", "REPLAY"]


@pytest.mark.parametrize("failure_point", ["AFTER_CASE_MUTATION", "AFTER_CASE_EVENT", "AFTER_COMMAND_AUDIT"])
def test_case_event_and_command_audit_are_all_rolled_back(failure_point):
    seed_rollback_case()
    with pytest.raises(RuntimeError, match=failure_point): execute_atomic_transition(failure_point)
    assert durable_atomic_state() == (("READY", 7), 0, 0)


def test_case_event_and_command_audit_commit_together_on_success():
    seed_rollback_case(); execute_atomic_transition(); assert durable_atomic_state() == (("SUBMITTING", 8), 1, 1)


def test_replay_after_successful_commit_and_lost_response_creates_no_duplicate_transition_or_submission():
    seed_rollback_case(); command_id = "cmd-lost-response"; command_hash = "f" * 64
    with pytest.raises(ConnectionError, match="response loss"): request_submission_idempotently(command_id, command_hash, lose_response=True)
    result = request_submission_idempotently(command_id, command_hash)
    assert result == {"replayed": True, "decision": "APPLIED", "case_id": "crb", "submission_id": "s-lost", "decision_code": None}
    assert durable_command_counts(command_id) == (1, 1, 1)


def test_reconnect_recovers_durable_result_without_recreating_anything():
    seed_rollback_case(); command_id = "cmd-reconnect"; command_hash = "d" * 64
    with pytest.raises(ConnectionError, match="response loss"):
        request_submission_idempotently(command_id, command_hash, lose_response=True)

    # Photographie durable avant reconnexion : le commit a déjà produit exactement 1/1/1.
    before_reconnect = durable_command_counts(command_id)
    assert before_reconnect == (1, 1, 1)

    # Nouvel appel = nouvelle connexion MariaDB. Le même command_id relit l'audit durable.
    recovered = request_submission_idempotently(command_id, command_hash)
    assert recovered == {"replayed": True, "decision": "APPLIED", "case_id": "crb", "submission_id": "s-lost", "decision_code": None}

    # La récupération est strictement en lecture : aucun nouvel événement/audit/submission.
    assert durable_command_counts(command_id) == before_reconnect
    conn = connect()
    try:
        cur = conn.cursor(); cur.execute("SELECT status,version FROM tw_dpae_case WHERE id='crb'"); assert cur.fetchone() == ("SUBMITTING", 8)
        cur.execute("SELECT attempt_no,idempotency_key,state FROM tw_dpae_submission WHERE id='s-lost'"); assert cur.fetchone() == (1, command_id, "PREPARED")
    finally: conn.close()
