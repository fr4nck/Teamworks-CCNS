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
    return mysql.connect(
        host=os.environ["DPAE_MYSQL_HOST"],
        port=int(os.getenv("DPAE_MYSQL_PORT", "3306")),
        user=os.environ["DPAE_MYSQL_USER"],
        password=os.getenv("DPAE_MYSQL_PASSWORD", ""),
        database=os.environ["DPAE_MYSQL_DATABASE"],
        use_pure=True,
        autocommit=False,
    )


def statements():
    text = Path("infrastructure/persistence/sql/mysql/dpae_v1.sql").read_text(encoding="utf-8")
    return [part.strip() for part in text.split(";") if part.strip()]


@pytest.fixture(scope="module", autouse=True)
def install_schema():
    conn = connect()
    try:
        cur = conn.cursor()
        for statement in statements():
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
            "tw_dpae_case_submission_lock", "tw_dpae_submission", "tw_dpae_case",
        ):
            cur.execute("DELETE FROM " + table)
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
    finally:
        conn.close()


def seed_case_submission_return():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO tw_dpae_case (id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at) VALUES ('c1','case-1','e1','ct1','est1',NOW(),'IN_PROGRESS','TEAMWORKS',NOW())")
        for sid, attempt in (("s1", 1), ("s2", 2)):
            cur.execute("INSERT INTO tw_dpae_submission (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES (%s,'c1',%s,%s,%s,'SENDING',NOW())", (sid, attempt, "cmd-" + sid, (sid * 64)[:64]))
        cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,correlation_status) VALUES ('r1','URSSAF','RETURN_41',%s,NOW(),'ext-1','UNMATCHED')", ("a" * 64,))
        conn.commit()
    finally:
        conn.close()


def test_unique_case_key_and_idempotency_are_enforced_by_mysql():
    seed_case_submission_return()
    conn = connect()
    try:
        cur = conn.cursor()
        with pytest.raises(mysql.IntegrityError):
            cur.execute("INSERT INTO tw_dpae_case (id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at) VALUES ('cx','case-1','e2','ct2','est1',NOW(),'READY','TEAMWORKS',NOW())")
        conn.rollback()
        with pytest.raises(mysql.IntegrityError):
            cur.execute("INSERT INTO tw_dpae_submission (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES ('sx','c1',3,'cmd-s1',%s,'PREPARED',NOW())", ("b" * 64,))
    finally:
        conn.close()


def test_two_workers_cannot_hold_uncertain_submission_lock_for_same_case():
    seed_case_submission_return()

    def acquire(submission_id):
        conn = connect()
        try:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO tw_dpae_case_submission_lock (case_id,submission_id,acquired_at) VALUES ('c1',%s,NOW())", (submission_id,))
                conn.commit()
                return "ACQUIRED"
            except mysql.IntegrityError:
                conn.rollback()
                return "CONFLICT"
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(acquire, ("s1", "s2")))
    assert sorted(results) == ["ACQUIRED", "CONFLICT"]


def test_two_operators_cannot_create_two_current_correlations():
    seed_case_submission_return()

    def confirm(args):
        decision_id, submission_id = args
        conn = connect()
        try:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO tw_dpae_correlation_decision (id,return_id,action,actor_id,decided_at,candidate_submission_id) VALUES (%s,'r1','CONFIRM_MATCH',%s,NOW(),%s)", (decision_id, decision_id, submission_id))
                cur.execute("INSERT INTO tw_dpae_current_correlation (return_id,submission_id,decision_id,confirmed_at) VALUES ('r1',%s,%s,NOW())", (submission_id, decision_id))
                conn.commit()
                return "CONFIRMED"
            except mysql.IntegrityError:
                conn.rollback()
                return "CONFLICT"
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(confirm, (("d1", "s1"), ("d2", "s2"))))
    assert sorted(results) == ["CONFIRMED", "CONFLICT"]


def test_return_effect_is_exactly_once_under_concurrency():
    seed_case_submission_return()

    def apply(_):
        conn = connect()
        try:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO tw_dpae_return_effect (return_id,effect_type,created_at) VALUES ('r1','MARK_DPAE_REGISTERED',NOW())")
                conn.commit()
                return "CREATED"
            except mysql.IntegrityError:
                conn.rollback()
                return "REPLAY"
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(apply, range(2)))
    assert sorted(results) == ["CREATED", "REPLAY"]
