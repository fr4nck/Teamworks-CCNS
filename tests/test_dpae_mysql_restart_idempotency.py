"""Idempotence DPAE après interruption du premier processus et redémarrage."""
import os
from datetime import datetime
from pathlib import Path

import pytest

mysql = pytest.importorskip("mysql.connector")

from application.services.dpae_service import DpaeService, PrepareDpae, SubmitDpae
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


def test_conflicting_payload_after_durable_audit_and_process_restart_is_rejected_without_new_audit():
    command_id = "restart-conflict-submit-001"
    original_hash = "a" * 64
    conflicting_hash = "b" * 64

    # Premier processus Teamworks : la commande est appliquée et son audit est COMMIT.
    first_process = DpaeService(DpaeMariaDbAdapter(connect))
    prepared = first_process.prepare(PrepareDpae(
        command_id="restart-conflict-prepare-001",
        case_key="restart-conflict-case-key",
        employee_id="employee-restart-conflict",
        contract_id="contract-restart-conflict",
        establishment_id="est-restart-conflict",
        expected_hiring_at=datetime(2026, 10, 17, 8, 0),
        actor_id="accounting-user",
    ))
    case_id = prepared["case_id"]
    first = first_process.submit(SubmitDpae(
        command_id=command_id,
        case_id=case_id,
        payload_hash=original_hash,
        actor_id="accounting-user",
    ))
    submission_id = first["submission_id"]

    # Vérifie que l'audit que le processus suivant retrouvera est réellement durable.
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT command_hash,decision,case_id,submission_id "
            "FROM tw_dpae_command_audit WHERE command_id=%s",
            (command_id,),
        )
        durable_audit = cur.fetchone()
        assert durable_audit == (original_hash, "APPLIED", case_id, submission_id)
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        durable_case = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        durable_submission_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        durable_event_count = cur.fetchone()[0]
    finally:
        conn.close()

    # Interruption simulée : aucune référence au premier service/adapter n'est réutilisée.
    del first_process

    # Redémarrage complet : nouvelles instances et nouvelles connexions MariaDB.
    restarted_process = DpaeService(DpaeMariaDbAdapter(connect))
    with pytest.raises(IdempotencyPayloadConflict, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        restarted_process.submit(SubmitDpae(
            command_id=command_id,
            case_id=case_id,
            payload_hash=conflicting_hash,
            actor_id="accounting-user",
        ))

    # Le conflit doit être détecté depuis l'audit durable original et ne laisser
    # absolument aucune nouvelle trace métier ou d'audit.
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        assert cur.fetchone()[0] == 1
        cur.execute(
            "SELECT command_hash,decision,case_id,submission_id "
            "FROM tw_dpae_command_audit WHERE command_id=%s",
            (command_id,),
        )
        assert cur.fetchone() == durable_audit
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        assert cur.fetchone() == durable_case
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == durable_submission_count == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == durable_event_count == 1
        cur.execute("SELECT payload_hash FROM tw_dpae_submission WHERE id=%s", (submission_id,))
        assert cur.fetchone() == (original_hash,)
    finally:
        conn.close()
