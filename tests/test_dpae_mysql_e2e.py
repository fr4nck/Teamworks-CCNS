"""Scénario E2E DPAE sur une vraie base MariaDB/MySQL.

Couvre le cycle durable minimal : dossier -> préparation -> émission simulée avec
réponse perdue -> replay idempotent -> retour URSSAF -> corrélation -> preuve.
Le transport URSSAF reste simulé : ce test valide notre frontière transactionnelle,
pas le protocole réseau du fournisseur.
"""
import os
from pathlib import Path

import pytest

mysql = pytest.importorskip("mysql.connector")

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


def create_case():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tw_dpae_case
              (id,case_key,employee_id,contract_id,establishment_id,
               expected_hiring_at,status,origin,created_at,version)
            VALUES
              ('e2e-case','e2e-case-key','employee-e2e','contract-e2e','est-e2e',
               '2026-10-15 08:30:00','READY','TEAMWORKS',NOW(),0)
        """)
        conn.commit()
    finally:
        conn.close()


def prepare_submission(command_id, payload_hash):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id='e2e-case' FOR UPDATE")
        assert cur.fetchone() == ("READY", 0)
        cur.execute("UPDATE tw_dpae_case SET status='SUBMITTING',version=1 WHERE id='e2e-case' AND version=0")
        assert cur.rowcount == 1
        cur.execute("""
            INSERT INTO tw_dpae_submission
              (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at)
            VALUES ('e2e-submission','e2e-case',1,%s,%s,'PREPARED',NOW())
        """, (command_id, payload_hash))
        cur.execute("""
            INSERT INTO tw_dpae_case_event
              (id,case_id,event_type,state_before,state_after,version_before,version_after,
               actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at)
            VALUES
              ('e2e-event-prepare','e2e-case','SUBMISSION_REQUESTED','READY','SUBMITTING',0,1,
               'USER','accounting-user',%s,%s,NOW(),NOW())
        """, (command_id, payload_hash))
        cur.execute("""
            INSERT INTO tw_dpae_command_audit
              (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,
               submission_id,requested_at,decided_at,decision,case_version_seen)
            VALUES
              ('e2e-audit-prepare',%s,'RequestDpaeSubmission',%s,'USER','accounting-user',
               'e2e-case','e2e-submission',NOW(),NOW(),'APPLIED',0)
        """, (command_id, payload_hash))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def simulated_send_then_lose_response():
    """Le fournisseur reçoit le flux ; le client perd seulement la réponse locale."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT state,version FROM tw_dpae_submission WHERE id='e2e-submission' FOR UPDATE")
        assert cur.fetchone() == ("PREPARED", 0)
        cur.execute("""
            UPDATE tw_dpae_submission
               SET state='SENT', external_flux_id='flux-e2e-001', sent_at=NOW(), version=1
             WHERE id='e2e-submission' AND version=0
        """)
        assert cur.rowcount == 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    raise ConnectionError("simulated response loss after durable send state")


def replay_prepare(command_id, payload_hash):
    """Une reconnexion retrouve la commande déjà appliquée sans recréer d'essai."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT command_hash,decision,case_id,submission_id
              FROM tw_dpae_command_audit WHERE command_id=%s
        """, (command_id,))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == payload_hash
        conn.rollback()
        return row[1:]
    finally:
        conn.close()


def receive_urssaf_return(raw_hash):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tw_dpae_return
              (id,provider,return_type,raw_hash,received_at,external_return_id,
               external_flux_id,employer_siret,correlation_status,processing_status,version)
            VALUES
              ('e2e-return','URSSAF','AEE',%s,NOW(),'urssaf-return-e2e-001',
               'flux-e2e-001','12345678901234','UNMATCHED','RECEIVED',0)
        """, (raw_hash,))
        conn.commit()
    finally:
        conn.close()


def correlate_return():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT external_flux_id FROM tw_dpae_return WHERE id='e2e-return' FOR UPDATE")
        flux_id = cur.fetchone()[0]
        cur.execute("SELECT id,case_id FROM tw_dpae_submission WHERE external_flux_id=%s", (flux_id,))
        submission_id, case_id = cur.fetchone()
        assert (submission_id, case_id) == ("e2e-submission", "e2e-case")
        cur.execute("""
            INSERT INTO tw_dpae_correlation_decision
              (id,return_id,action,actor_id,decided_at,candidate_submission_id,reason_code)
            VALUES
              ('e2e-correlation-decision','e2e-return','CONFIRM_MATCH','DPAE_RETURN_CORRELATOR',
               NOW(),'e2e-submission','EXTERNAL_FLUX_ID_EXACT')
        """)
        cur.execute("""
            INSERT INTO tw_dpae_current_correlation
              (return_id,submission_id,decision_id,confirmed_at)
            VALUES
              ('e2e-return','e2e-submission','e2e-correlation-decision',NOW())
        """)
        cur.execute("""
            UPDATE tw_dpae_return
               SET submission_id='e2e-submission',case_id='e2e-case',
                   correlation_status='CONFIRMED',processing_status='PROCESSED',version=1
             WHERE id='e2e-return' AND version=0
        """)
        assert cur.rowcount == 1
        cur.execute("""
            INSERT INTO tw_dpae_return_effect(return_id,effect_type,created_at)
            VALUES ('e2e-return','MARK_DPAE_REGISTERED',NOW())
        """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_full_dpae_e2e_durable_evidence_after_network_loss_and_replay():
    command_id = "e2e-command-001"
    payload_hash = "c" * 64
    return_hash = "d" * 64

    # 1. Création du dossier puis préparation atomique de la première tentative.
    create_case()
    prepare_submission(command_id, payload_hash)

    # 2. Envoi simulé : l'état SENT est durable, puis la réponse locale est perdue.
    with pytest.raises(ConnectionError, match="response loss"):
        simulated_send_then_lose_response()

    # 3. Le client se reconnecte et rejoue exactement la même commande.
    recovered = replay_prepare(command_id, payload_hash)
    assert recovered == ("APPLIED", "e2e-case", "e2e-submission")

    # 4. L'URSSAF renvoie ensuite un AEE portant le même identifiant de flux.
    receive_urssaf_return(return_hash)
    correlate_return()

    # 5. Nouvelle connexion : preuve exclusivement à partir de l'état durable.
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status,version FROM tw_dpae_case WHERE id='e2e-case'")
        assert cur.fetchone() == ("SUBMITTING", 1)

        cur.execute("""
            SELECT attempt_no,idempotency_key,payload_hash,state,external_flux_id,version
              FROM tw_dpae_submission WHERE case_id='e2e-case'
        """)
        assert cur.fetchall() == [(1, command_id, payload_hash, "SENT", "flux-e2e-001", 1)]

        cur.execute("SELECT COUNT(*) FROM tw_dpae_case_event WHERE case_id='e2e-case'")
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT event_type,state_before,state_after,idempotency_key,command_hash FROM tw_dpae_case_event WHERE case_id='e2e-case'")
        assert cur.fetchone() == ("SUBMISSION_REQUESTED", "READY", "SUBMITTING", command_id, payload_hash)

        cur.execute("SELECT COUNT(*) FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT decision,case_id,submission_id,command_hash FROM tw_dpae_command_audit WHERE command_id=%s", (command_id,))
        assert cur.fetchone() == ("APPLIED", "e2e-case", "e2e-submission", payload_hash)

        cur.execute("""
            SELECT provider,return_type,raw_hash,external_return_id,external_flux_id,
                   submission_id,case_id,correlation_status,processing_status,version
              FROM tw_dpae_return WHERE id='e2e-return'
        """)
        assert cur.fetchone() == (
            "URSSAF", "AEE", return_hash, "urssaf-return-e2e-001", "flux-e2e-001",
            "e2e-submission", "e2e-case", "CONFIRMED", "PROCESSED", 1,
        )

        cur.execute("SELECT action,actor_id,candidate_submission_id,reason_code FROM tw_dpae_correlation_decision WHERE id='e2e-correlation-decision'")
        assert cur.fetchone() == ("CONFIRM_MATCH", "DPAE_RETURN_CORRELATOR", "e2e-submission", "EXTERNAL_FLUX_ID_EXACT")
        cur.execute("SELECT submission_id,decision_id FROM tw_dpae_current_correlation WHERE return_id='e2e-return'")
        assert cur.fetchone() == ("e2e-submission", "e2e-correlation-decision")
        cur.execute("SELECT effect_type FROM tw_dpae_return_effect WHERE return_id='e2e-return'")
        assert cur.fetchall() == [("MARK_DPAE_REGISTERED",)]

        # Invariants E2E : le replay n'a créé aucune seconde preuve ni tentative.
        cur.execute("SELECT COUNT(*) FROM tw_dpae_submission WHERE case_id='e2e-case'")
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_current_correlation WHERE return_id='e2e-return'")
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM tw_dpae_return_effect WHERE return_id='e2e-return' AND effect_type='MARK_DPAE_REGISTERED'")
        assert cur.fetchone()[0] == 1
    finally:
        conn.close()
