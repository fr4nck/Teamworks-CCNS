"""Adaptateur d'entrée ``inter-domain-delivery/1`` pour le domaine RH/emploi.

Ce module ne choisit aucun transport physique. Il vérifie l'enveloppe signée
selon ADR-012 puis délègue le payload ``session-actual/1`` au consommateur RH.
Les secrets sont injectés via ``keyring`` et ne sont jamais stockés ici.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import datetime
from typing import Any, Mapping, Optional

from application.services.session_actual_hr import SessionActualHrConsumer
from infrastructure.persistence.session_actual_hr_repository import (
    SessionActualHrPersistenceError,
)


ENVELOPE_VERSION = "inter-domain-delivery/1"
SOURCE_DOMAIN = "operations_portal"
TARGET_DOMAIN = "hr_employment"
CONTRACT_VERSION = "session-actual/1"
EVENT_TYPE = "session_actual_validated"
ACK_STATUSES = frozenset(("accepted", "replayed", "rejected", "retryable"))


class DeliveryEnvelopeError(ValueError):
    """Enveloppe absente, invalide, non authentifiée ou mal adressée."""


def _required_text(value: Any, field_name: str, maximum: int) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise DeliveryEnvelopeError(f"{field_name} obligatoire")
    if len(normalized) > maximum or any(ord(character) < 32 for character in normalized):
        raise DeliveryEnvelopeError(f"{field_name} invalide")
    return normalized


def _secret(value: Any) -> bytes:
    if not isinstance(value, bytes):
        raise DeliveryEnvelopeError("secret HMAC binaire obligatoire")
    if len(value) < 32:
        raise DeliveryEnvelopeError("secret HMAC trop court")
    return value


def _occurred_at(value: Any) -> str:
    value = _required_text(value, "occurred_at", 40)
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$", value):
        raise DeliveryEnvelopeError("occurred_at invalide")
    return value


def _mapping_copy(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise DeliveryEnvelopeError(f"{field_name} invalide")
    try:
        return json.loads(json.dumps(dict(value), ensure_ascii=True))
    except (TypeError, ValueError) as error:
        raise DeliveryEnvelopeError(f"{field_name} non sérialisable") from error


def _canonical_json(envelope: Mapping[str, Any]) -> str:
    try:
        return json.dumps(
            envelope,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
    except (TypeError, ValueError) as error:
        raise DeliveryEnvelopeError("enveloppe non sérialisable") from error


def _signature(envelope: Mapping[str, Any], secret: bytes) -> str:
    message = _canonical_json(envelope).encode("utf-8")
    return hmac.new(_secret(secret), message, hashlib.sha256).hexdigest()


def verify_envelope(
    delivery: Mapping[str, Any],
    keyring: Mapping[str, bytes],
    *,
    target_domain: str = TARGET_DOMAIN,
    source_domain: str = SOURCE_DOMAIN,
) -> dict[str, Any]:
    """Vérifie l'enveloppe authentifiée et retourne une copie détachée."""
    if not isinstance(delivery, Mapping) or set(delivery.keys()) != {"envelope", "signature"}:
        raise DeliveryEnvelopeError("livraison signée invalide")

    envelope = _mapping_copy(delivery.get("envelope"), "enveloppe")
    signature = _required_text(delivery.get("signature"), "signature", 64).lower()
    if not re.match(r"^[0-9a-f]{64}$", signature):
        raise DeliveryEnvelopeError("signature HMAC invalide")

    if envelope.get("envelope_version") != ENVELOPE_VERSION:
        raise DeliveryEnvelopeError("version d'enveloppe non supportée")
    if _required_text(envelope.get("source_domain"), "source_domain", 64) != source_domain:
        raise DeliveryEnvelopeError("domaine source inattendu")
    if _required_text(envelope.get("target_domain"), "target_domain", 64) != target_domain:
        raise DeliveryEnvelopeError("domaine cible inattendu")

    contract_version = _required_text(envelope.get("contract_version"), "contract_version", 64)
    event_type = _required_text(envelope.get("event_type"), "event_type", 64)
    idempotence_key = _required_text(envelope.get("idempotence_key"), "idempotence_key", 255)
    correlation_id = _required_text(envelope.get("correlation_id"), "correlation_id", 128)
    _occurred_at(envelope.get("occurred_at"))
    key_id = _required_text(envelope.get("key_id"), "key_id", 64)

    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise DeliveryEnvelopeError("payload invalide")
    if payload.get("contract_version") != contract_version:
        raise DeliveryEnvelopeError("contract_version incohérente avec le payload")
    if payload.get("event_type") != event_type:
        raise DeliveryEnvelopeError("event_type incohérent avec le payload")
    if contract_version != CONTRACT_VERSION:
        raise DeliveryEnvelopeError("contrat métier non supporté")
    if event_type != EVENT_TYPE:
        raise DeliveryEnvelopeError("type d'événement non supporté")

    if not isinstance(keyring, Mapping) or key_id not in keyring:
        raise DeliveryEnvelopeError("key_id inconnu")
    expected = _signature(envelope, keyring[key_id])
    if not hmac.compare_digest(expected, signature):
        raise DeliveryEnvelopeError("signature HMAC invalide")

    envelope["idempotence_key"] = idempotence_key
    envelope["correlation_id"] = correlation_id
    return envelope


def build_ack(status: str, idempotence_key: str, correlation_id: str, detail: str = "") -> dict[str, str]:
    status = _required_text(status, "status", 32)
    if status not in ACK_STATUSES:
        raise DeliveryEnvelopeError("statut d'accusé invalide")
    idempotence_key = _required_text(idempotence_key, "idempotence_key", 255)
    correlation_id = _required_text(correlation_id, "correlation_id", 128)
    if not isinstance(detail, str) or len(detail) > 500:
        raise DeliveryEnvelopeError("detail invalide")
    return {
        "status": status,
        "idempotence_key": idempotence_key,
        "correlation_id": correlation_id,
        "detail": detail,
    }


def receive_signed_delivery(
    delivery: Mapping[str, Any],
    keyring: Mapping[str, bytes],
    *,
    consumer: Optional[SessionActualHrConsumer] = None,
    received_at: Optional[datetime] = None,
) -> dict[str, str]:
    """Vérifie l'enveloppe puis délègue le réalisé au consommateur RH.

    Les erreurs déterministes d'enveloppe ou de persistance métier deviennent
    ``rejected``. Les pannes techniques inattendues restent propagées afin que
    l'adaptateur de transport physique puisse les classer ``retryable``.
    """
    try:
        envelope = verify_envelope(delivery, keyring)
    except DeliveryEnvelopeError as error:
        idempotence_key = "invalid"
        correlation_id = "invalid"
        if isinstance(delivery, Mapping) and isinstance(delivery.get("envelope"), Mapping):
            candidate = delivery["envelope"]
            try:
                idempotence_key = _required_text(candidate.get("idempotence_key"), "idempotence_key", 255)
            except DeliveryEnvelopeError:
                pass
            try:
                correlation_id = _required_text(candidate.get("correlation_id"), "correlation_id", 128)
            except DeliveryEnvelopeError:
                pass
        return build_ack("rejected", idempotence_key, correlation_id, str(error))

    owned_consumer = consumer is None
    consumer = consumer or SessionActualHrConsumer()
    try:
        result = consumer.receive(
            envelope["payload"],
            idempotence_key=envelope["idempotence_key"],
            source_domain=envelope["source_domain"],
            received_at=received_at,
        )
    except SessionActualHrPersistenceError as error:
        return build_ack(
            "rejected",
            envelope["idempotence_key"],
            envelope["correlation_id"],
            str(error),
        )
    finally:
        if owned_consumer:
            consumer.close()

    if result.status == "applied":
        status = "accepted"
    elif result.status == "replayed":
        status = "replayed"
    else:
        raise RuntimeError("résultat du consommateur RH indéterminé")
    return build_ack(status, envelope["idempotence_key"], envelope["correlation_id"])
