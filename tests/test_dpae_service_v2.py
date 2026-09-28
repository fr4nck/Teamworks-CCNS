import pytest

from application.services.dpae_service import (
    DpaeBusinessData, DpaeService, PrepareDpae, RetryDpaeSubmission,
    SubmitDpae, TransmissionResult,
)


class Resolver:
    def __init__(self):
        self.calls = 0
        self.version = "v1"
    def resolve(self, contract_id):
        self.calls += 1
        return DpaeBusinessData(contract_id, self.version, "source-" + self.version, "2026-09-27.1", "payload-" + self.version)


class Adapter:
    def __init__(self):
        self.replays = {}
        self.prepared = []
        self.finished = []
    def replay_prepare(self, cmd): return self.replays.get(cmd.command_id)
    def prepare(self, cmd, data):
        result = {"case_id": "case-1", "snapshot_id": "snap-" + data.payload_hash, "payload_hash": data.payload_hash, "status": "READY", "replayed": False}
        self.prepared.append((cmd, data, result)); self.replays[cmd.command_id] = dict(result, replayed=True); return result
    def submit(self, cmd):
        return {"case_id": cmd.case_id, "submission_id": "sub-1", "snapshot_id": "snap-payload-v1", "payload_hash": "payload-v1", "canonical_payload": "v1", "replayed": False}
    def start_transmission(self, submission_id): pass
    def finish_transmission(self, submission_id, result): self.finished.append((submission_id, result.outcome))
    def retry_submission(self, submission_id):
        return {"case_id": "case-1", "submission_id": submission_id, "snapshot_id": "snap-payload-v1", "payload_hash": "payload-v1", "canonical_payload": "v1", "attempt_no": 1, "replayed": False}


class Transport:
    def __init__(self, fail_first=False): self.calls=[]; self.fail_first=fail_first
    def send(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_first and len(self.calls) == 1: raise TimeoutError("lost ACK")
        return TransmissionResult("SENT", external_flux_id="flux-1")


def command(command_id): return PrepareDpae(command_id=command_id, case_key="contract-742", contract_id="742", actor_id="user")


def test_prepare_replay_does_not_reread_live_teamworks_data():
    adapter = Adapter(); resolver = Resolver(); service = DpaeService(adapter, resolver=resolver)
    first = service.prepare(command("cmd-1")); assert resolver.calls == 1
    resolver.version = "v2"; replay = service.prepare(command("cmd-1"))
    assert resolver.calls == 1; assert replay["snapshot_id"] == first["snapshot_id"]; assert replay["payload_hash"] == "payload-v1"


def test_new_prepare_after_business_change_resolves_new_snapshot_data():
    adapter = Adapter(); resolver = Resolver(); service = DpaeService(adapter, resolver=resolver)
    first = service.prepare(command("cmd-1")); resolver.version = "v2"; second = service.prepare(command("cmd-2"))
    assert resolver.calls == 2; assert first["snapshot_id"] != second["snapshot_id"]
    assert adapter.prepared[0][1].canonical_payload == "v1"; assert adapter.prepared[1][1].canonical_payload == "v2"


def test_transport_retry_reuses_durable_snapshot_without_resolver():
    adapter = Adapter(); resolver = Resolver(); transport = Transport(fail_first=True); service = DpaeService(adapter, transport=transport, resolver=resolver)
    service.prepare(command("prepare-1")); assert resolver.calls == 1
    with pytest.raises(TimeoutError): service.submit(SubmitDpae("submit-1", "case-1", "user"))
    resolver.version = "v2"
    retried = service.retry_submission(RetryDpaeSubmission("sub-1"))
    assert resolver.calls == 1
    assert retried["submission_id"] == "sub-1"; assert retried["snapshot_id"] == "snap-payload-v1"; assert retried["attempt_no"] == 1
    assert transport.calls[0]["canonical_payload"] == "v1"; assert transport.calls[1]["canonical_payload"] == "v1"
    assert transport.calls[0]["payload_hash"] == transport.calls[1]["payload_hash"] == "payload-v1"
