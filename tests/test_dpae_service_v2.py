import json

import pytest

from application.services.dpae_service import (
    DpaeBusinessData, DpaeService, PrepareDpae, RetryDpaeSubmission,
    SubmitDpae, TransmissionResult,
)


class Resolver:
    """Resolver espion : chaque appel représente une lecture des sources RH/DUE vivantes."""
    def __init__(self):
        self.calls = 0
        self.hiring_time = "0830"

    def resolve(self, contract_id):
        self.calls += 1
        payload = json.dumps(
            {"contract": {"contract_id": contract_id, "hiring_time": self.hiring_time}},
            sort_keys=True,
            separators=(",", ":"),
        )
        suffix = self.hiring_time
        return DpaeBusinessData(
            contract_id,
            payload,
            "source-" + suffix,
            "2026-09-27.1",
            "payload-" + suffix,
        )


class Adapter:
    def __init__(self):
        self.replays = {}
        self.prepared = []
        self.snapshots = {}
        self.submissions = {}
        self.finished = []

    def replay_prepare(self, cmd):
        return self.replays.get(cmd.command_id)

    def prepare(self, cmd, data):
        snapshot_id = "snap-" + data.payload_hash
        result = {
            "case_id": "case-1",
            "snapshot_id": snapshot_id,
            "canonical_payload": data.canonical_payload,
            "source_fingerprint": data.source_fingerprint,
            "payload_hash": data.payload_hash,
            "status": "READY",
            "replayed": False,
        }
        self.snapshots[snapshot_id] = dict(result)
        self.prepared.append((cmd, data, result))
        self.replays[cmd.command_id] = dict(result, replayed=True)
        return result

    def submit(self, cmd):
        snapshot = self.snapshots["snap-payload-0830"]
        durable = {
            "case_id": cmd.case_id,
            "submission_id": "sub-1",
            "snapshot_id": snapshot["snapshot_id"],
            "payload_hash": snapshot["payload_hash"],
            "canonical_payload": snapshot["canonical_payload"],
            "source_fingerprint": snapshot["source_fingerprint"],
            "replayed": False,
        }
        self.submissions["sub-1"] = dict(durable)
        return durable

    def start_transmission(self, submission_id):
        pass

    def finish_transmission(self, submission_id, result):
        self.finished.append((submission_id, result.outcome))

    def retry_submission(self, submission_id):
        durable = dict(self.submissions[submission_id])
        durable.update(attempt_no=1, replayed=False)
        return durable


class Transport:
    def __init__(self, fail_first=False):
        self.calls = []
        self.fail_first = fail_first

    def send(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_first and len(self.calls) == 1:
            raise TimeoutError("lost ACK")
        return TransmissionResult("SENT", external_flux_id="flux-1")


def command(command_id):
    return PrepareDpae(command_id=command_id, case_key="contract-742", contract_id="742", actor_id="user")


def hiring_time(result):
    return json.loads(result["canonical_payload"])["contract"]["hiring_time"]


def test_prepare_captures_h1_and_snapshot_remains_immutable_after_source_changes_to_h2():
    adapter = Adapter(); resolver = Resolver(); service = DpaeService(adapter, resolver=resolver)
    first = service.prepare(command("cmd-1"))
    assert resolver.calls == 1; assert hiring_time(first) == "0830"
    f1 = first["source_fingerprint"]; p1 = first["payload_hash"]
    resolver.hiring_time = "0915"
    stored = adapter.snapshots[first["snapshot_id"]]
    assert hiring_time(stored) == "0830"; assert stored["source_fingerprint"] == f1; assert stored["payload_hash"] == p1


def test_prepare_replay_after_h1_to_h2_does_not_call_resolver_or_create_snapshot():
    adapter = Adapter(); resolver = Resolver(); service = DpaeService(adapter, resolver=resolver)
    first = service.prepare(command("cmd-1")); assert resolver.calls == 1
    snapshot_count = len(adapter.snapshots); f1 = first["source_fingerprint"]; p1 = first["payload_hash"]
    resolver.hiring_time = "0915"
    replay = service.prepare(command("cmd-1"))
    assert resolver.calls == 1; assert len(adapter.snapshots) == snapshot_count
    assert replay["snapshot_id"] == first["snapshot_id"]; assert hiring_time(replay) == "0830"
    assert replay["source_fingerprint"] == f1; assert replay["payload_hash"] == p1


def test_new_prepare_after_h1_to_h2_creates_s2_without_mutating_s1():
    adapter = Adapter(); resolver = Resolver(); service = DpaeService(adapter, resolver=resolver)
    first = service.prepare(command("cmd-1")); f1 = first["source_fingerprint"]; p1 = first["payload_hash"]
    resolver.hiring_time = "0915"; second = service.prepare(command("cmd-2"))
    assert resolver.calls == 2; assert first["snapshot_id"] != second["snapshot_id"]
    assert hiring_time(first) == "0830"; assert first["source_fingerprint"] == f1; assert first["payload_hash"] == p1
    assert hiring_time(second) == "0915"; assert second["source_fingerprint"] != f1; assert second["payload_hash"] != p1
    assert hiring_time(adapter.snapshots[first["snapshot_id"]]) == "0830"


def test_submission_retry_after_h1_to_h2_reuses_s1_without_resolver():
    adapter = Adapter(); resolver = Resolver(); transport = Transport(fail_first=True); service = DpaeService(adapter, transport=transport, resolver=resolver)
    first = service.prepare(command("prepare-1")); assert resolver.calls == 1; assert hiring_time(first) == "0830"
    f1 = first["source_fingerprint"]; p1 = first["payload_hash"]
    with pytest.raises(TimeoutError):
        service.submit(SubmitDpae("submit-1", "case-1", "user"))
    resolver.hiring_time = "0915"
    retried = service.retry_submission(RetryDpaeSubmission("sub-1"))
    assert resolver.calls == 1
    assert retried["submission_id"] == "sub-1"; assert retried["snapshot_id"] == first["snapshot_id"]; assert retried["attempt_no"] == 1
    assert hiring_time(retried) == "0830"; assert retried["source_fingerprint"] == f1; assert retried["payload_hash"] == p1
    assert transport.calls[0]["canonical_payload"] == transport.calls[1]["canonical_payload"] == first["canonical_payload"]
    assert transport.calls[0]["payload_hash"] == transport.calls[1]["payload_hash"] == p1
