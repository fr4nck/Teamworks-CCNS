"""Atomicité du vrai DpaeMariaDbAdapter sur MariaDB."""
import os

import pytest

mysql = pytest.importorskip("mysql.connector")

from application.services.dpae_service import DpaeBusinessData, PrepareDpae, SubmitDpae
from infrastructure.persistence.dpae_mysql import DpaeMariaDbAdapter

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)


def connect():
    return mysql.connect(
        host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")),
        user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""),
        database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False,
    )


def business_data(contract_id):
    return DpaeBusinessData(contract_id, "{}", "f" * 64, "test-rules", "a" * 64)


def prepare_case(suffix):
    adapter = DpaeMariaDbAdapter(connect)
    command = PrepareDpae("atomicity-prepare-" + suffix, "atomicity-case-key-" + suffix, "contract-atomicity", "accounting-user")
    return adapter.prepare(command, business_data(command.contract_id))["case_id"]


def assert_submit_rolled_back(case_id, command_id, prepare_command_id):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        assert cur.fetchone() == ("READY", 0)
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (prepare_command_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_snapshot WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == 1
    finally:
        conn.close()


def test_submit_exception_after_submission_write_rolls_back_everything(clean_tables):
    case_id = prepare_case("001")

    def failure(point):
        if point == "after_submission_write":
            raise RuntimeError("injected failure after submission write")

    adapter = DpaeMariaDbAdapter(connect, failure_injector=failure)
    command_id = "atomicity-submit-001"
    with pytest.raises(RuntimeError, match="injected failure after submission write"):
        adapter.submit(SubmitDpae(command_id, case_id, "accounting-user"))
    assert_submit_rolled_back(case_id, command_id, "atomicity-prepare-001")


def test_submit_exception_after_case_event_write_rolls_back_everything(clean_tables):
    case_id = prepare_case("002")

    def failure(point):
        if point == "after_case_event_write":
            raise RuntimeError("injected failure after case event write")

    adapter = DpaeMariaDbAdapter(connect, failure_injector=failure)
    command_id = "atomicity-submit-002"
    with pytest.raises(RuntimeError, match="injected failure after case event write"):
        adapter.submit(SubmitDpae(command_id, case_id, "accounting-user"))
    assert_submit_rolled_back(case_id, command_id, "atomicity-prepare-002")


def test_prepare_exception_after_snapshot_write_leaves_no_orphan(clean_tables):
    def failure(point):
        if point == "after_snapshot_write":
            raise RuntimeError("injected failure after snapshot write")

    adapter = DpaeMariaDbAdapter(connect, failure_injector=failure)
    command = PrepareDpae("atomicity-prepare-fail", "atomicity-case-key-fail", "contract-atomicity", "accounting-user")
    with pytest.raises(RuntimeError, match="injected failure after snapshot write"):
        adapter.prepare(command, business_data(command.contract_id))
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case WHERE case_key=%s", (command.case_key,))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM tw_dpae_snapshot WHERE contract_id=%s", (command.contract_id,))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command.command_id,))
        assert cur.fetchone()[0] == 0
    finally:
        conn.close()
