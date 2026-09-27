"""Sémantique transactionnelle DPAE sur MySQL/MariaDB réel."""
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

mysql = pytest.importorskip("mysql.connector")

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)


def connect():
    return mysql.connect(
        host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")),
        user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""),
        database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False,
    )


def seed_two_returns():
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,correlation_status,version) VALUES ('r1','URSSAF','RETURN_41',%s,NOW(),'ext-r1','UNMATCHED',0)", ("a" * 64,))
        cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,correlation_status,version) VALUES ('r2','URSSAF','RETURN_41',%s,NOW(),'ext-r2','UNMATCHED',0)", ("b" * 64,))
        conn.commit()
    finally:
        cur.close(); conn.close()


def set_isolation(cur, level):
    cur.execute("SET TRANSACTION ISOLATION LEVEL " + level)


def read_version(cur, return_id):
    cur.execute("SELECT version FROM tw_dpae_return WHERE id=%s", (return_id,))
    return cur.fetchone()[0]


def test_read_committed_observes_commit_between_two_reads(clean_tables):
    seed_two_returns(); reader = connect(); writer = connect()
    try:
        rc = reader.cursor(); wc = writer.cursor(); set_isolation(rc, "READ COMMITTED")
        reader.start_transaction(); assert read_version(rc, "r1") == 0
        wc.execute("UPDATE tw_dpae_return SET version=1 WHERE id='r1'"); writer.commit()
        assert read_version(rc, "r1") == 1; reader.rollback()
    finally:
        reader.close(); writer.close()


def test_repeatable_read_keeps_snapshot_until_transaction_end(clean_tables):
    seed_two_returns(); reader = connect(); writer = connect()
    try:
        rc = reader.cursor(); wc = writer.cursor(); set_isolation(rc, "REPEATABLE READ")
        reader.start_transaction(); assert read_version(rc, "r1") == 0
        wc.execute("UPDATE tw_dpae_return SET version=1 WHERE id='r1'"); writer.commit()
        assert read_version(rc, "r1") == 0; reader.commit(); reader.start_transaction()
        assert read_version(rc, "r1") == 1; reader.rollback()
    finally:
        reader.close(); writer.close()


def test_select_for_update_blocks_competing_writer_until_commit(clean_tables):
    seed_two_returns()
    locked = threading.Event(); attempted = threading.Event(); release = threading.Event()
    waiter_finished = threading.Event()

    def holder():
        conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SELECT version FROM tw_dpae_return WHERE id='r1' FOR UPDATE"); cur.fetchone(); locked.set()
            assert release.wait(10); conn.commit()
        finally:
            cur.close(); conn.close()

    def waiter():
        assert locked.wait(10); conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SET SESSION innodb_lock_wait_timeout=8"); attempted.set()
            cur.execute("UPDATE tw_dpae_return SET version=version+1 WHERE id='r1'"); conn.commit()
        finally:
            waiter_finished.set(); cur.close(); conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(holder); b = pool.submit(waiter)
        assert attempted.wait(10)
        # Synchronisation événementielle : aucune hypothèse sur la vitesse du runner.
        assert not waiter_finished.wait(0.5), "le writer n'a pas été bloqué par SELECT FOR UPDATE"
        release.set(); a.result(timeout=10); b.result(timeout=10)
    assert waiter_finished.is_set()


def test_rollback_releases_lock_and_discards_uncommitted_change(clean_tables):
    seed_two_returns()
    locked = threading.Event(); attempted = threading.Event(); rollback_now = threading.Event(); waiter_finished = threading.Event()

    def holder_then_rollback():
        conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SELECT version FROM tw_dpae_return WHERE id='r1' FOR UPDATE"); cur.fetchone()
            cur.execute("UPDATE tw_dpae_return SET version=7 WHERE id='r1'"); locked.set(); assert rollback_now.wait(10); conn.rollback()
        finally:
            cur.close(); conn.close()

    def waiter():
        assert locked.wait(10); conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SET SESSION innodb_lock_wait_timeout=8"); attempted.set()
            cur.execute("UPDATE tw_dpae_return SET version=version+1 WHERE id='r1'"); conn.commit()
        finally:
            waiter_finished.set(); cur.close(); conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(holder_then_rollback); b = pool.submit(waiter)
        assert attempted.wait(10)
        assert not waiter_finished.wait(0.5), "le writer n'a pas attendu le rollback du détenteur"
        rollback_now.set(); a.result(timeout=10); b.result(timeout=10)
    conn = connect(); cur = conn.cursor()
    try:
        assert read_version(cur, "r1") == 1
    finally:
        conn.rollback(); cur.close(); conn.close()


def test_deadlock_aborts_exactly_one_transaction_and_survivor_commits(clean_tables):
    seed_two_returns(); first_locks = threading.Barrier(2)

    def cross_lock(first, second):
        conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SET SESSION innodb_lock_wait_timeout=8")
            cur.execute("UPDATE tw_dpae_return SET version=version+1 WHERE id=%s", (first,))
            first_locks.wait(timeout=10)
            cur.execute("UPDATE tw_dpae_return SET version=version+1 WHERE id=%s", (second,)); conn.commit()
            return "COMMITTED"
        except mysql.Error as exc:
            conn.rollback()
            if getattr(exc, "errno", None) == 1213 or getattr(exc, "sqlstate", None) == "40001":
                return "DEADLOCK"
            raise
        finally:
            cur.close(); conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(cross_lock, *pair) for pair in (("r1", "r2"), ("r2", "r1"))]
        results = [future.result(timeout=15) for future in futures]
    assert sorted(results) == ["COMMITTED", "DEADLOCK"]
    conn = connect(); cur = conn.cursor()
    try:
        assert read_version(cur, "r1") == 1; assert read_version(cur, "r2") == 1
    finally:
        conn.rollback(); cur.close(); conn.close()


def test_savepoint_rollback_preserves_outer_transaction(clean_tables):
    seed_two_returns(); conn = connect(); cur = conn.cursor()
    try:
        cur.execute("UPDATE tw_dpae_return SET version=1 WHERE id='r1'"); cur.execute("SAVEPOINT dpae_before_effect")
        cur.execute("UPDATE tw_dpae_return SET version=9 WHERE id='r2'"); cur.execute("ROLLBACK TO SAVEPOINT dpae_before_effect"); conn.commit()
    finally:
        cur.close(); conn.close()
    conn = connect(); cur = conn.cursor()
    try:
        assert read_version(cur, "r1") == 1; assert read_version(cur, "r2") == 0
    finally:
        conn.rollback(); cur.close(); conn.close()
