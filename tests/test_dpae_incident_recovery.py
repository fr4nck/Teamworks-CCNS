import pytest

from application.services.dpae_service import (
    DpaeService,
    RecoverInterruptedDpaeSubmission,
    RetryDpaeSubmission,
    TransmissionResult,
)


class ResolverSpy:
    def __init__(self):
        self.calls = 0

    def resolve(self, contract_id):
        self.calls += 1
        raise AssertionError("recovery/retry must not resolve live Teamworks data")


class TransportSpy:
    def __init__(self):
        self.calls = []

    def send(self, **kwargs):
        self.calls.append(kwargs)
        return TransmissionResult("SENT", external_flux_id="flux-recovery")


class RecoveryError(Exception):
    pass


class RecoveryAdapter:
    def __init__(self, state="SENDING"):
        self.state = state
        self.recoveries = 0
        self.submission_count = 1
        self.durable = {
            "case_id": "case-1",
            "submission_id": "sub-1",
            "snapshot_id": "snap-1",
            "payload_hash": "payload-h1",
            "canonical_payload": '{"contract":{"hiring_time":"0830"}}',
            "attempt_no": 1,
        }

    def recover_interrupted_submission(self, submission_id):
        if submission_id != "sub-1":
            raise RecoveryError("SUBMISSION_NOT_FOUND")
        if self.state == "OUTCOME_UNKNOWN":
            return dict(self.durable, state="OUTCOME_UNKNOWN", replayed=True)
        if self.state != "SENDING":
            raise RecoveryError("SUBMISSION_NOT_RECOVERABLE")
        self.state = "OUTCOME_UNKNOWN"
        self.recoveries += 1
        return dict(self.durable, state=self.state, replayed=False)

    def retry_submission(self, submission_id):
        if submission_id != "sub-1" or self.state != "OUTCOME_UNKNOWN":
            raise RecoveryError("SUBMISSION_NOT_RETRYABLE")
        self.state = "SENDING"
        return dict(self.durable, replayed=False)

    def finish_transmission(self, submission_id, result):
        assert submission_id == "sub-1"
        self.state = "TECHNICALLY_ACCEPTED" if result.outcome == "SENT" else result.outcome


def service_for(state="SENDING"):
    adapter = RecoveryAdapter(state)
    resolver = ResolverSpy()
    transport = TransportSpy()
    return DpaeService(adapter, transport=transport, resolver=resolver), adapter, resolver, transport


def test_recovery_marks_abandoned_sending_unknown_without_transport_or_resolver():
    service, adapter, resolver, transport = service_for()
    result = service.recover_interrupted_submission(RecoverInterruptedDpaeSubmission("sub-1"))
    assert result["state"] == "OUTCOME_UNKNOWN"
    assert result["submission_id"] == "sub-1"
    assert result["snapshot_id"] == "snap-1"
    assert adapter.submission_count == 1
    assert adapter.recoveries == 1
    assert resolver.calls == 0
    assert transport.calls == []


def test_recovery_replay_is_idempotent_and_does_not_create_an_effect():
    service, adapter, resolver, transport = service_for()
    first = service.recover_interrupted_submission(RecoverInterruptedDpaeSubmission("sub-1"))
    second = service.recover_interrupted_submission(RecoverInterruptedDpaeSubmission("sub-1"))
    assert first["replayed"] is False
    assert second["replayed"] is True
    assert adapter.recoveries == 1
    assert adapter.submission_count == 1
    assert resolver.calls == 0
    assert transport.calls == []


def test_explicit_retry_after_recovery_uses_historical_snapshot_only():
    service, adapter, resolver, transport = service_for()
    service.recover_interrupted_submission(RecoverInterruptedDpaeSubmission("sub-1"))
    retried = service.retry_submission(RetryDpaeSubmission("sub-1"))
    assert retried["submission_id"] == "sub-1"
    assert retried["snapshot_id"] == "snap-1"
    assert retried["payload_hash"] == "payload-h1"
    assert transport.calls == [{
        "submission_id": "sub-1",
        "payload_hash": "payload-h1",
        "canonical_payload": '{"contract":{"hiring_time":"0830"}}',
    }]
    assert resolver.calls == 0
    assert adapter.state == "TECHNICALLY_ACCEPTED"


def test_live_source_mutation_is_irrelevant_to_recovery_and_retry():
    service, adapter, resolver, transport = service_for()
    live_source = {"hiring_time": "0830"}
    service.recover_interrupted_submission(RecoverInterruptedDpaeSubmission("sub-1"))
    live_source["hiring_time"] = "0915"
    service.retry_submission(RetryDpaeSubmission("sub-1"))
    assert live_source["hiring_time"] == "0915"
    assert '"0830"' in transport.calls[0]["canonical_payload"]
    assert '"0915"' not in transport.calls[0]["canonical_payload"]
    assert resolver.calls == 0


@pytest.mark.parametrize("state", ["PREPARED", "TECHNICALLY_ACCEPTED", "REJECTED"])
def test_recovery_rejects_incompatible_states(state):
    service, adapter, resolver, transport = service_for(state)
    with pytest.raises(RecoveryError, match="SUBMISSION_NOT_RECOVERABLE"):
        service.recover_interrupted_submission(RecoverInterruptedDpaeSubmission("sub-1"))
    assert adapter.state == state
    assert resolver.calls == 0
    assert transport.calls == []


def test_recovery_rejects_unknown_submission():
    service, adapter, resolver, transport = service_for()
    with pytest.raises(RecoveryError, match="SUBMISSION_NOT_FOUND"):
        service.recover_interrupted_submission(RecoverInterruptedDpaeSubmission("missing"))
    assert adapter.state == "SENDING"
    assert resolver.calls == 0
    assert transport.calls == []
