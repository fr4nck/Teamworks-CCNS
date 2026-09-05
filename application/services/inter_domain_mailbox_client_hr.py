"""Client pull sortant ``inter-domain-mailbox-pull/1`` du domaine RH/emploi."""
from __future__ import annotations

import json
import socket
from typing import Any, Mapping, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlparse

from application.services.inter_domain_delivery_hr import (
    ACK_STATUSES,
    SessionActualHrConsumer,
    build_ack,
    receive_signed_delivery,
)

MAILBOX_VERSION = "inter-domain-mailbox-pull/1"
TARGET_DOMAIN = "hr_employment"
CLAIM_PATH = "/api/inter-domain/mailbox/v1/claim"
ACK_PATH_PREFIX = "/api/inter-domain/mailbox/v1/ack/"


class MailboxPullError(RuntimeError):
    pass


class MailboxTransportError(MailboxPullError):
    pass


class _NoRedirectHandler(urllib_request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _text(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise MailboxPullError(f"{field} obligatoire")
    if len(normalized) > maximum or any(ord(c) < 32 for c in normalized):
        raise MailboxPullError(f"{field} invalide")
    return normalized


def _limit(value: Any) -> int:
    if type(value) is not int or value < 1 or value > 200:
        raise MailboxPullError("limit invalide")
    return value


def _delivery(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise MailboxPullError("livraison mailbox invalide")
    if value.get("mailbox_version") != MAILBOX_VERSION:
        raise MailboxPullError("version mailbox non supportée")
    if value.get("target_domain") != TARGET_DOMAIN:
        raise MailboxPullError("domaine cible mailbox inattendu")
    delivery_id = _text(value.get("delivery_id"), "delivery_id", 64)
    idempotence_key = _text(value.get("idempotence_key"), "idempotence_key", 255)
    correlation_id = _text(value.get("correlation_id"), "correlation_id", 128)
    signed = value.get("signed_delivery")
    if not isinstance(signed, Mapping):
        raise MailboxPullError("livraison signée absente")
    attempts = value.get("attempts")
    if type(attempts) is not int or attempts < 1:
        raise MailboxPullError("attempts invalide")
    return {
        "delivery_id": delivery_id,
        "idempotence_key": idempotence_key,
        "correlation_id": correlation_id,
        "signed_delivery": dict(signed),
        "attempts": attempts,
    }


def _safe_detail(error: Exception) -> str:
    text = " ".join((f"{error.__class__.__name__}: {error}").split()).strip()
    return (text or "échec technique local")[:500]


class MailboxHttpTransport:
    """Transport HTTPS sortant, sans dépendance externe ni redirection."""

    def __init__(self, base_url: str, bearer_token: str, timeout: int = 20, opener=None):
        base_url = _text(base_url, "base_url", 512).rstrip("/")
        parsed = urlparse(base_url)
        if parsed.scheme.lower() != "https" or not parsed.netloc or parsed.query or parsed.fragment:
            raise MailboxTransportError("base_url HTTPS invalide")
        self.base_url = base_url
        self.bearer_token = _text(bearer_token, "bearer_token", 512)
        if type(timeout) is not int or timeout < 1 or timeout > 300:
            raise MailboxTransportError("timeout invalide")
        self.timeout = timeout
        self.opener = opener or urllib_request.build_opener(_NoRedirectHandler()).open

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise MailboxTransportError("payload HTTP invalide")
        data = json.dumps(dict(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
        request = urllib_request.Request(
            self.base_url + path,
            data=data,
            headers={
                "Authorization": "Bearer " + self.bearer_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "hr-employment-mailbox/1",
            },
            method="POST",
        )
        try:
            response = self.opener(request, timeout=self.timeout)
            raw = response.read()
            status = getattr(response, "status", getattr(response, "code", 200))
        except urllib_error.HTTPError as error:
            raise MailboxTransportError("mailbox HTTP refusée (%s)" % error.code) from error
        except (urllib_error.URLError, socket.timeout, OSError) as error:
            raise MailboxTransportError("mailbox HTTPS indisponible: %s" % error.__class__.__name__) from error
        if status < 200 or status >= 300:
            raise MailboxTransportError("mailbox HTTP inattendue (%s)" % status)
        try:
            decoded = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            result = json.loads(decoded)
        except (UnicodeDecodeError, ValueError, TypeError) as error:
            raise MailboxTransportError("réponse mailbox JSON invalide") from error
        if not isinstance(result, dict):
            raise MailboxTransportError("réponse mailbox invalide")
        return result

    def claim(self, limit: int = 20) -> tuple[dict[str, Any], ...]:
        result = self._post_json(CLAIM_PATH, {"limit": _limit(limit)})
        deliveries = result.get("deliveries")
        if not isinstance(deliveries, list):
            raise MailboxTransportError("lot mailbox invalide")
        return tuple(deliveries)

    def acknowledge(self, delivery_id: str, receipt: Mapping[str, Any]) -> dict[str, Any]:
        delivery_id = _text(delivery_id, "delivery_id", 64)
        if not isinstance(receipt, Mapping):
            raise MailboxTransportError("accusé invalide")
        result = self._post_json(ACK_PATH_PREFIX + delivery_id, receipt)
        if result.get("status") not in ACK_STATUSES:
            raise MailboxTransportError("statut d'acquittement distant invalide")
        return result


def synchronize_mailbox(
    transport,
    keyring: Mapping[str, bytes],
    *,
    consumer: Optional[SessionActualHrConsumer] = None,
    limit: int = 20,
    received_at=None,
) -> dict[str, int]:
    """Traite un lot borné. Une panne d'ACK provoquera un replay idempotent."""
    limit = _limit(limit)
    if not callable(getattr(transport, "claim", None)) or not callable(getattr(transport, "acknowledge", None)):
        raise MailboxPullError("transport mailbox invalide")
    if not isinstance(keyring, Mapping) or not keyring:
        raise MailboxPullError("keyring HMAC obligatoire")

    deliveries = transport.claim(limit=limit)
    if not isinstance(deliveries, (tuple, list)):
        raise MailboxPullError("lot mailbox invalide")
    owned_consumer = consumer is None
    consumer = consumer or SessionActualHrConsumer()
    summary = {"claimed": len(deliveries), "accepted": 0, "replayed": 0, "rejected": 0, "retryable": 0, "acked": 0}
    try:
        for raw in deliveries:
            item = _delivery(raw)
            try:
                receipt = receive_signed_delivery(
                    item["signed_delivery"], keyring, consumer=consumer, received_at=received_at
                )
            except Exception as error:
                receipt = build_ack(
                    "retryable", item["idempotence_key"], item["correlation_id"], _safe_detail(error)
                )

            status = receipt.get("status")
            if status not in ACK_STATUSES:
                raise MailboxPullError("statut d'accusé local invalide")
            if status == "rejected" and (
                receipt.get("idempotence_key") != item["idempotence_key"]
                or receipt.get("correlation_id") != item["correlation_id"]
            ):
                receipt = build_ack(
                    "rejected",
                    item["idempotence_key"],
                    item["correlation_id"],
                    str(receipt.get("detail") or "")[:500],
                )
            else:
                if receipt.get("idempotence_key") != item["idempotence_key"]:
                    raise MailboxPullError("idempotence_key de l'accusé local incohérente")
                if receipt.get("correlation_id") != item["correlation_id"]:
                    raise MailboxPullError("correlation_id de l'accusé local incohérente")

            summary[status] += 1
            transport.acknowledge(item["delivery_id"], receipt)
            summary["acked"] += 1
        return summary
    finally:
        if owned_consumer:
            consumer.close()
