from application.services.dpae_service import DpaeBusinessData, DpaeService, PrepareDpae


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
    def replay_prepare(self, cmd):
        return self.replays.get(cmd.command_id)
    def prepare(self, cmd, data):
        result = {"case_id": "case-1", "snapshot_id": "snap-" + data.payload_hash, "payload_hash": data.payload_hash, "status": "READY", "replayed": False}
        self.prepared.append((cmd, data, result))
        self.replays[cmd.command_id] = dict(result, replayed=True)
        return result


def command(command_id):
    return PrepareDpae(command_id=command_id, case_key="contract-742", contract_id="742", actor_id="user")


def test_prepare_replay_does_not_reread_live_teamworks_data():
    adapter = Adapter(); resolver = Resolver(); service = DpaeService(adapter, resolver=resolver)
    first = service.prepare(command("cmd-1"))
    assert resolver.calls == 1
    resolver.version = "v2"
    replay = service.prepare(command("cmd-1"))
    assert resolver.calls == 1
    assert replay["snapshot_id"] == first["snapshot_id"]
    assert replay["payload_hash"] == "payload-v1"


def test_new_prepare_after_business_change_resolves_new_snapshot_data():
    adapter = Adapter(); resolver = Resolver(); service = DpaeService(adapter, resolver=resolver)
    first = service.prepare(command("cmd-1"))
    resolver.version = "v2"
    second = service.prepare(command("cmd-2"))
    assert resolver.calls == 2
    assert first["snapshot_id"] != second["snapshot_id"]
    assert adapter.prepared[0][1].canonical_payload == "v1"
    assert adapter.prepared[1][1].canonical_payload == "v2"
