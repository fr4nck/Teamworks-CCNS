from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
import json

import pytest

from application.services.inter_domain_delivery_hr import (
    DeliveryEnvelopeError,
    receive_signed_delivery,
    verify_envelope,
)
from application.services.session_actual_hr import SessionActualHrConsumer
from infrastructure.persistence.session_actual_hr_repository import INBOX_TABLE, WORK_TABLE
from tests.test_session_actual_hr_consumer import payload, ready_repository


SECRET_A = b"a" * 32
SECRET_B = b"b" * 32
KEY_ID = "hr-2026-01"
EXPECTED_VECTOR_SIGNATURE = "fd175bd24e30fd9006cb60b3b70e850544ccfbde6d6d7476edab4f20a479fbef"


def _sign(envelope, secret):
    serialized = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hmac.new(secret, serialized.encode("utf-8"), hashlib.sha256).hexdigest()


def delivery(actual_payload=None, secret=SECRET_A, key_id=KEY_ID, **overrides):
    actual_payload = actual_payload or payload()
    envelope = {
        "envelope_version": "inter-domain-delivery/1",
        "source_domain": "operations_portal",
        "target_domain": "hr_employment",
        "contract_version": "session-actual/1",
        "event_type": "session_actual_validated",
        "idempotence_key": (
            f"session-actual:{actual_payload['actual_uuid']}:"
            f"r{actual_payload['actual_revision']}:hr_employment"
        ),
        "correlation_id": actual_payload["actual_uuid"],
        "occurred_at": "2026-09-04T10:46:00Z",
        "key_id": key_id,
        "payload": actual_payload,
    }
    envelope.update(overrides)
    return {"envelope": envelope, "signature": _sign(envelope, secret)}


def test_vecteur_hmac_hr_est_deterministe_et_aligne_adr_012():
    signed = delivery()
    assert signed["signature"] == EXPECTED_VECTOR_SIGNATURE
    verified = verify_envelope(signed, {KEY_ID: SECRET_A})
    assert verified["target_domain"] == "hr_employment"
    assert verified["correlation_id"] == "ACT-001"
    assert verified["payload"] == payload()


def test_payload_altere_apres_signature_est_refuse():
    signed = delivery()
    signed["envelope"]["payload"]["actual_revision"] = 5
    with pytest.raises(DeliveryEnvelopeError, match="signature HMAC invalide"):
        verify_envelope(signed, {KEY_ID: SECRET_A})


def test_mauvaise_cible_et_key_id_inconnu_sont_refuses():
    wrong_target = delivery(target_domain="activity_users")
    with pytest.raises(DeliveryEnvelopeError, match="domaine cible inattendu"):
        verify_envelope(wrong_target, {KEY_ID: SECRET_A})

    with pytest.raises(DeliveryEnvelopeError, match="key_id inconnu"):
        verify_envelope(delivery(), {"hr-old": SECRET_A})


def test_rotation_de_cle_accepte_chaque_secret_associe_a_son_key_id():
    old = delivery(secret=SECRET_A, key_id="hr-old")
    new = delivery(secret=SECRET_B, key_id="hr-new")
    keyring = {"hr-old": SECRET_A, "hr-new": SECRET_B}
    assert verify_envelope(old, keyring)["key_id"] == "hr-old"
    assert verify_envelope(new, keyring)["key_id"] == "hr-new"


def test_livraison_signee_est_appliquee_puis_rejouee_sans_doublon():
    db, repository = ready_repository()
    consumer = SessionActualHrConsumer(repository)
    signed = delivery()

    first = receive_signed_delivery(
        signed,
        {KEY_ID: SECRET_A},
        consumer=consumer,
        received_at=datetime(2026, 9, 4, 10, 46, 0),
    )
    second = receive_signed_delivery(
        signed,
        {KEY_ID: SECRET_A},
        consumer=consumer,
        received_at=datetime(2026, 9, 4, 10, 47, 0),
    )

    assert first["status"] == "accepted"
    assert second["status"] == "replayed"
    assert first["idempotence_key"] == second["idempotence_key"]
    assert first["correlation_id"] == "ACT-001"
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {WORK_TABLE}").fetchone()[0] == 1
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {INBOX_TABLE}").fetchone()[0] == 1


def test_erreur_metier_deterministe_est_rejected_sans_ecriture():
    db, repository = ready_repository()
    consumer = SessionActualHrConsumer(repository)
    invalid = delivery(payload(actual_duration_minutes=91))

    receipt = receive_signed_delivery(invalid, {KEY_ID: SECRET_A}, consumer=consumer)

    assert receipt["status"] == "rejected"
    assert "durée réelle incohérente" in receipt["detail"]
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {WORK_TABLE}").fetchone()[0] == 0
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {INBOX_TABLE}").fetchone()[0] == 0


def test_signature_invalide_est_rejected_avant_toute_ecriture():
    db, repository = ready_repository()
    consumer = SessionActualHrConsumer(repository)
    signed = delivery()
    signed["signature"] = "0" * 64

    receipt = receive_signed_delivery(signed, {KEY_ID: SECRET_A}, consumer=consumer)

    assert receipt["status"] == "rejected"
    assert "signature HMAC invalide" in receipt["detail"]
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {WORK_TABLE}").fetchone()[0] == 0
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {INBOX_TABLE}").fetchone()[0] == 0


def test_panne_technique_inattendue_n_est_pas_masquee_en_rejected():
    class BrokenConsumer:
        def receive(self, *args, **kwargs):
            raise RuntimeError("panne technique simulée")

    with pytest.raises(RuntimeError, match="panne technique simulée"):
        receive_signed_delivery(delivery(), {KEY_ID: SECRET_A}, consumer=BrokenConsumer())
