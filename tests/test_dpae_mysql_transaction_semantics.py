"""Sémantique transactionnelle DPAE sur MySQL/MariaDB réel.

Ces tests ne simulent pas InnoDB : ils exigent la base configurée par les
variables DPAE_MYSQL_* et vérifient isolation, attente de verrou, deadlock et
rollback. Ils complètent les tests fonctionnels de MysqlDpaeRepository.
"""
import os
import threading
import time
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


def seed_two_returns():
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,correlation_status,version) VALUES ('r1','URSSAF','RETURN_41',%s,NOW(),'ext-r1','UNMATCHED',0)", ("a" * 64,))
        cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,correlation_status,version) VALUES ('r2','URSSAF','RETURN_41',%s,NOW(),'ext-r2','UNMATCHED',0)", ("b" * 64,))
        conn.commit()
    finally:
        cur.close(); conn.close()


def set_isolation(cur, level):
    # SET TRANSACTION est compris par les versions MySQL/MariaDB visées et ne
    # modifie que la prochaine transaction de cette connexion.
    cur.execute("SET TRANSACTION ISOLATION LEVEL " + level)


def read_version(cur, return_id):
    cur.execute("SELECT version FROM tw_dpae_return WHERE id=%s", (return_id,))
    return cur.fetchone()[0]


def test_read_committed_observes_commit_between_two_reads(clean_tables):
    seed_two_returns()
    reader = connect(); writer = connect()
    try:
        rc = reader.cursor(); wc = writer.cursor()
        set_isolation(rc, "READ COMMITTED")
        reader.start_transaction()
        assert read_version(rc, "r1") == 0
        wc.execute("UPDATE tw_dpae_return SET version=1 WHERE id='r1'")
        writer.commit()
        assert read_version(rc, "r1") == 1
        reader.rollback()
    finally:
        reader.close(); writer.close()


def test_repeatable_read_keeps_snapshot_until_transaction_end(clean_tables):
    seed_two_returns()
    reader = connect(); writer = connect()
    try:
        rc = reader.cursor(); wc = writer.cursor()
        set_isolation(rc, "REPEATABLE READ")
        reader.start_transaction()
        assert read_version(rc, "r1") == 0
        wc.execute("UPDATE tw_dpae_return SET version=1 WHERE id='r1'")
        writer.commit()
        assert read_version(rc, "r1") == 0
        reader.commit()
        reader.start_transaction()
        assert read_version(rc, "r1") == 1
        reader.rollback()
    finally:
        reader.close(); writer.close()


def test_select_for_update_blocks_competing_writer_until_commit(clean_tables):
    seed_two_returns()
    locked = threading.Event(); attempted = threading.Event(); release = threading.Event()
    elapsed = {}

    def holder():
        conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SELECT version FROM tw_dpae_return WHERE id='r1' FOR UPDATE")
            cur.fetchone(); locked.set()
            assert release.wait(5)
            conn.commit()
        finally:
            cur.close(); conn.close()

    def waiter():
        assert locked.wait(5)
        conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SET SESSION innodb_lock_wait_timeout=5")
            attempted.set(); start = time.monotonic()
            cur.execute("UPDATE tw_dpae_return SET version=version+1 WHERE id='r1'")
            conn.commit(); elapsed["seconds"] = time.monotonic() - start
        finally:
            cur.close(); conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(holder); b = pool.submit(waiter)
        assert attempted.wait(5)
        # Le writer doit encore attendre tant que le verrou n'est pas libéré.
        time.sleep(0.35)
        assert not b.done()
        release.set(); a.result(timeout=5); b.result(timeout=5)
    assert elapsed["seconds"] >= 0.30


def test_rollback_releases_lock_and_discards_uncommitted_change(clean_tables):
    seed_two_returns()
    locked = threading.Event(); attempted = threading.Event(); rollback_now = threading.Event()

    def holder_then_rollback():
        conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SELECT version FROM tw_dpae_return WHERE id='r1' FOR UPDATE")
            cur.fetchone()
            cur.execute("UPDATE tw_dpae_return SET version=7 WHERE id='r1'")
            locked.set(); assert rollback_now.wait(5)
            conn.rollback()
        finally:
            cur.close(); conn.close()

    def waiter():
        assert locked.wait(5)
        conn = connect(); cur = conn.cursor()
        try:
            attempted.set()
            cur.execute("UPDATE tw_dpae_return SET version=version+1 WHERE id='r1'")
            conn.commit()
        finally:
            cur.close(); conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(holder_then_rollback); b = pool.submit(waiter)
        assert attempted.wait(5); time.sleep(0.25); assert not b.done()
        rollback_now.set(); a.result(timeout=5); b.result(timeout=5)

    conn = connect(); cur = conn.cursor()
    try:
        # 7 n'a jamais été visible/committé ; le waiter repart de 0 puis +1.
        assert read_version(cur, "r1") == 1
    finally:
        conn.rollback(); cur.close(); conn.close()


def test_deadlock_aborts_exactly_one_transaction_and_survivor_commits(clean_tables):
    seed_two_returns()
    first_locks = threading.Barrier(2)

    def cross_lock(first, second):
        conn = connect(); cur = conn.cursor()
        try:
            cur.execute("SET SESSION innodb_lock_wait_timeout=5")
            cur.execute("UPDATE tw_dpae_return SET version=version+1 WHERE id=%s", (first,))
            first_locks.wait(timeout=5)
            cur.execute("UPDATE tw_dpae_return SET version=version+1 WHERE id=%s", (second,))
            conn.commit()
            return "COMMITTED"
        except mysql.Error as exc:
            conn.rollback()
            # MySQL/MariaDB signalent classiquement le deadlock par 1213 /
            # SQLSTATE 40001. Accepter les deux formes évite un test lié au driver.
            if getattr(exc, "errno", None) == 1213 or getattr(exc, "sqlstate", None) == "40001":
                return "DEADLOCK"
            raise
        finally:
            cur.close(); conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda pair: cross_lock(*pair), (("r1", "r2"), ("r2", "r1"))))
    assert sorted(results) == ["COMMITTED", "DEADLOCK"]

    conn = connect(); cur = conn.cursor()
    try:
        # La transaction victime est entièrement rollbackée ; seule la
        # transaction survivante a incrémenté les deux lignes.
        assert read_version(cur, "r1") == 1
        assert read_version(cur, "r2") == 1
    finally:
        conn.rollback(); cur.close(); conn.close()


def test_savepoint_rollback_preserves_outer_transaction(clean_tables):
    seed_two_returns()
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute("UPDATE tw_dpae_return SET version=1 WHERE id='r1'")
        cur.execute("SAVEPOINT dpae_before_effect")
        cur.execute("UPDATE tw_dpae_return SET version=9 WHERE id='r2'")
        cur.execute("ROLLBACK TO SAVEPOINT dpae_before_effect")
        conn.commit()
    finally:
        cur.close(); conn.close()

    conn = connect(); cur = conn.cursor()
    try:
        assert read_version(cur, "r1") == 1
        assert read_version(cur, "r2") == 0
    finally:
        conn.rollback(); cur.close(); conn.close()
