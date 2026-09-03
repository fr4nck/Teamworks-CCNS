from __future__ import annotations

import json
from urllib import error as urllib_error

import pytest

from application.services import inter_domain_mailbox_client_hr as client

IDEMPOTENCE = "session-actual:test:r1:hr_employment"
CORRELATION = "11111111-1111-1111-1111-111111111111"
DELIVERY_ID = "22222222-2222-2222-2222-222222222222"


def delivery(target="hr_employment"):
    return {
        "mailbox_version": "inter-domain-mailbox-pull/1",
        "delivery_id": DELIVERY_ID,
        "target_domain": target,
        "idempotence_key": IDEMPOTENCE,
        "correlation_id": CORRELATION,
        "attempts": 1,
        "signed_delivery": {"envelope": {"x": 1}, "signature": "a" * 64},
    }


class FakeTransport:
    def __init__(self, deliveries=None, ack_error=None):
        self.deliveries = list(deliveries or [])
        self.acks = []
        self.ack_error = ack_error

    def claim(self, limit=20):
        self.limit = limit
        return tuple(self.deliveries)

    def acknowledge(self, delivery_id, receipt):
        if self.ack_error:
            raise self.ack_error
        self.acks.append((delivery_id, dict(receipt)))
        return {"status": receipt["status"]}


class FakeConsumer:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_applied_delivery_is_acked(monkeypatch):
    transport = FakeTransport([delivery()])
    receipt = {"status": "accepted", "idempotence_key": IDEMPOTENCE, "correlation_id": CORRELATION, "detail": ""}
    monkeypatch.setattr(client, "receive_signed_delivery", lambda *a, **k: receipt)
    summary = client.synchronize_mailbox(transport, {"kid": b"x" * 32}, consumer=FakeConsumer(), limit=4)
    assert summary["accepted"] == 1
    assert summary["acked"] == 1
    assert transport.acks[0][1]["status"] == "accepted"


def test_technical_consumer_failure_becomes_retryable(monkeypatch):
    transport = FakeTransport([delivery()])

    def fail(*args, **kwargs):
        raise RuntimeError("db offline")

    monkeypatch.setattr(client, "receive_signed_delivery", fail)
    summary = client.synchronize_mailbox(transport, {"kid": b"x" * 32}, consumer=FakeConsumer())
    assert summary["retryable"] == 1
    assert transport.acks[0][1]["status"] == "retryable"
    assert "Bearer" not in transport.acks[0][1].get("detail", "")


def test_malformed_signed_delivery_uses_outer_ids_for_rejected_ack(monkeypatch):
    transport = FakeTransport([delivery()])
    rejected = {"status": "rejected", "idempotence_key": "invalid", "correlation_id": "invalid", "detail": "signature HMAC invalide"}
    monkeypatch.setattr(client, "receive_signed_delivery", lambda *a, **k: rejected)
    summary = client.synchronize_mailbox(transport, {"kid": b"x" * 32}, consumer=FakeConsumer())
    assert summary["rejected"] == 1
    ack = transport.acks[0][1]
    assert ack["idempotence_key"] == IDEMPOTENCE
    assert ack["correlation_id"] == CORRELATION


def test_non_rejected_identifier_mismatch_fails_closed(monkeypatch):
    transport = FakeTransport([delivery()])
    bad = {"status": "accepted", "idempotence_key": "wrong", "correlation_id": CORRELATION, "detail": ""}
    monkeypatch.setattr(client, "receive_signed_delivery", lambda *a, **k: bad)
    with pytest.raises(client.MailboxPullError, match="idempotence_key"):
        client.synchronize_mailbox(transport, {"kid": b"x" * 32}, consumer=FakeConsumer())
    assert transport.acks == []


def test_ack_failure_is_not_swallowed(monkeypatch):
    transport = FakeTransport([delivery()], ack_error=client.MailboxTransportError("offline"))
    receipt = {"status": "accepted", "idempotence_key": IDEMPOTENCE, "correlation_id": CORRELATION, "detail": ""}
    monkeypatch.setattr(client, "receive_signed_delivery", lambda *a, **k: receipt)
    with pytest.raises(client.MailboxTransportError):
        client.synchronize_mailbox(transport, {"kid": b"x" * 32}, consumer=FakeConsumer())


def test_other_domain_is_rejected_before_consumer(monkeypatch):
    transport = FakeTransport([delivery(target="activity_users")])
    calls = []
    monkeypatch.setattr(client, "receive_signed_delivery", lambda *a, **k: calls.append(True))
    with pytest.raises(client.MailboxPullError, match="domaine cible"):
        client.synchronize_mailbox(transport, {"kid": b"x" * 32}, consumer=FakeConsumer())
    assert calls == []


def test_http_transport_requires_https_and_keeps_bearer_in_header_only():
    with pytest.raises(client.MailboxTransportError):
        client.MailboxHttpTransport("http://example.invalid", "secret")
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        seen["auth"] = request.headers.get("Authorization")
        seen["body"] = request.data
        return FakeResponse({"deliveries": []})

    transport = client.MailboxHttpTransport(
        "https://portal.example.test",
        "mbx1.token.secret-value-long-enough-for-test",
        opener=opener,
    )
    assert transport.claim(limit=3) == ()
    assert seen["auth"] == "Bearer mbx1.token.secret-value-long-enough-for-test"
    assert b"secret-value" not in seen["body"]
    assert seen["url"].endswith(client.CLAIM_PATH)


def test_redirect_handler_refuses_cross_origin_and_downgrade():
    handler = client._NoRedirectHandler()
    request = client.urllib_request.Request(
        "https://portal.example.test" + client.CLAIM_PATH,
        data=b"{}",
        headers={"Authorization": "Bearer secret"},
        method="POST",
    )
    assert handler.redirect_request(
        request, None, 302, "Found", {"Location": "http://attacker.invalid/steal"}, "http://attacker.invalid/steal"
    ) is None


def test_redirect_error_is_sanitized():
    def redirecting(request, timeout):
        raise urllib_error.HTTPError(
            request.full_url, 302, "Found", {"Location": "http://attacker.invalid/steal"}, None
        )

    transport = client.MailboxHttpTransport(
        "https://portal.example.test",
        "mbx1.token.secret-value-long-enough-for-test",
        opener=redirecting,
    )
    with pytest.raises(client.MailboxTransportError) as error:
        transport.claim()
    assert "302" in str(error.value)
    assert "attacker.invalid" not in str(error.value)
