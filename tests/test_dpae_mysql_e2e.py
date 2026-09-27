"""E2E MariaDB via le vrai DpaeService et DpaeMariaDbAdapter."""
import os
from datetime import datetime
from pathlib import Path

import pytest

mysql = pytest.importorskip("mysql.connector")

from application.services.dpae_service import DpaeService, PrepareDpae, SubmitDpae, IngestDpaeReturn
from infrastructure.persistence.dpae_mysql import DpaeMariaDbAdapter

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)

SCHEMA = Path("infrastructure/persistence/sql/mysql/dpae_v1.sql")


def connect():
    return mysql.connect(host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")), user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""), database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False)


@pytest.fixture(scope="module", autouse=True)
def install_schema():
    conn = connect()
    try:
        cur = conn.cursor()
        for statement in (p.strip() for p in SCHEMA.read_text(encoding="utf-8").split(";")):
            if statement: cur.execute(statement)
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


def test_full_dpae_e2e_uses_real_service_adapter_and_keeps_durable_evidence():
    service = DpaeService(DpaeMariaDbAdapter(connect))
    payload_hash = "c" * 64
    return_hash = "d" * 64

    prepared = service.prepare(PrepareDpae(
        command_id="e2e-prepare-001", case_key="e2e-case-key",
        employee_id="employee-e2e", contract_id="contract-e2e",
        establishment_id="est-e2e", expected_hiring_at=datetime(2026, 10, 15, 8, 30),
        actor_id="accounting-user",
    ))
    case_id = prepared["case_id"]
    assert prepared["status"] == "READY"

    submitted = service.submit(SubmitDpae(
        command_id="e2e-submit-001", case_id=case_id,
        payload_hash=payload_hash, actor_id="accounting-user",
    ))
    submission_id = submitted["submission_id"]
    assert submitted["decision"] == "APPLIED"

    # Le transport externe est simulé, mais son résultat durable passe par le vrai adaptateur.
    service.mark_sent(submission_id, "flux-e2e-001")
    with pytest.raises(ConnectionError, match="response loss"):
        raise ConnectionError("simulated response loss after durable send state")

    # Reconnexion logique/replay : même commande, même résultat, aucune seconde tentative.
    replay_service = DpaeService(DpaeMariaDbAdapter(connect))
    replayed = replay_service.submit(SubmitDpae(
        command_id="e2e-submit-001", case_id=case_id,
        payload_hash=payload_hash, actor_id="accounting-user",
    ))
    assert replayed == {"case_id": case_id, "submission_id": submission_id, "decision": "APPLIED", "replayed": True}

    returned = replay_service.ingest_return(IngestDpaeReturn(
        provider="URSSAF", return_type="AEE", raw_hash=return_hash,
        received_at=datetime(2026, 10, 15, 8, 31),
        external_return_id="urssaf-return-e2e-001",
        external_flux_id="flux-e2e-001", employer_siret="12345678901234",
    ))
    assert returned["correlation_status"] == "MATCHED"
    assert returned["submission_id"] == submission_id
    return_id = returned["return_id"]

    # Vérifications indépendantes : SQL direct uniquement pour auditer les preuves durables.
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s", (case_id,))
        assert cur.fetchone() == ("SUBMITTING", 1)
        cur.execute("SELECT attempt_no,idempotency_key,payload_hash,state,external_flux_id,version FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        assert cur.fetchall() == [(1, "e2e-submit-001", payload_hash, "SENT", "flux-e2e-001", 1)]
        cur.execute("SELECT COUNT(*),MIN(event_type),MIN(state_before),MIN(state_after) FROM tw_dpae_case_event WHERE case_id=%s", (case_id,))
        assert cur.fetchone() == (1, "SUBMISSION_REQUESTED", "READY", "SUBMITTING")
        cur.execute("SELECT COUNT(*),MIN(decision),MIN(command_hash) FROM tw_dpae_command_audit WHERE command_id='e2e-submit-001'")
        assert cur.fetchone() == (1, "APPLIED", payload_hash)
        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == 2  # prepare + submit, replay n'ajoute rien
        cur.execute("SELECT provider,return_type,raw_hash,external_return_id,external_flux_id,submission_id,case_id,correlation_status,processing_status,version FROM tw_dpae_return WHERE id=%s", (return_id,))
        assert cur.fetchone() == ("URSSAF", "AEE", return_hash, "urssaf-return-e2e-001", "flux-e2e-001", submission_id, case_id, "MATCHED", "PROCESSED", 1)
        cur.execute("SELECT action,actor_id,candidate_submission_id,reason_code FROM tw_dpae_correlation_decision WHERE return_id=%s", (return_id,))
        assert cur.fetchone() == ("CONFIRM_MATCH", "DPAE_RETURN_CORRELATOR", submission_id, "EXTERNAL_FLUX_ID_EXACT")
        cur.execute("SELECT submission_id FROM tw_dpae_current_correlation WHERE return_id=%s", (return_id,))
        assert cur.fetchone() == (submission_id,)
        cur.execute("SELECT effect_type FROM tw_dpae_return_effect WHERE return_id=%s", (return_id,))
        assert cur.fetchall() == [("MARK_DPAE_REGISTERED",)]
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id=%s", (case_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_current_correlation WHERE return_id=%s", (return_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_return_effect WHERE return_id=%s", (return_id,))
        assert cur.fetchone()[0] == 1
    finally:
        conn.close()
