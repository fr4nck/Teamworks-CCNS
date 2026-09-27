"""Atomicité du vrai DpaeMariaDbAdapter sur MariaDB."""
import os
from datetime import datetime
from pathlib import Path

import pytest

mysql = pytest.importorskip("mysql.connector")

from application.services.dpae_service import PrepareDpae, SubmitDpae
from infrastructure.persistence.dpae_mysql import DpaeMariaDbAdapter

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


def test_submit_exception_after_submission_write_rolls_back_everything():
    base_adapter = DpaeMariaDbAdapter(connect)
    prepared = base_adapter.prepare(PrepareDpae(
        command_id="atomicity-prepare-001",
        case_key="atomicity-case-key-001",
        employee_id="employee-atomicity",
        contract_id="contract-atomicity",
        establishment_id="est-atomicity",
        expected_hiring_at=datetime(2026, 10, 20, 8, 30),
        actor_id="accounting-user",
    ))
    case_id = prepared["case_id"]

    def fail_after_submission_write(point):
        if point == "after_submission_write":
            raise RuntimeError("injected failure after submission write")

    adapter = DpaeMariaDbAdapter(connect, failure_injector=fail_after_submission_write)
    command_id = "atomicity-submit-001"
    payload_hash = "a" * 64

    with pytest.raises(RuntimeError, match="injected failure after submission write"):
        adapter.submit(SubmitDpae(
            command_id=command_id,
            case_id=case_id,
            payload_hash=payload_hash,
            actor_id="accounting-user",
        ))

    # Nouvelle connexion : seules les données réellement commitées sont observées.
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

        # L'audit de préparation est antérieur et commité : le rollback de submit
        # ne doit évidemment pas l'effacer.
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id='atomicity-prepare-001'")
        assert cur.fetchone()[0] == 1
    finally:
        conn.close()
