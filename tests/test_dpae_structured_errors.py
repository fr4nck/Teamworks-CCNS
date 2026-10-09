import pytest

from application.services.dpae_errors import DpaeConfigurationError, DpaeDataError
from application.services.dpae_service import DpaeBusinessData, DpaeService, PrepareDpae


class NoReplayAdapter:
    def replay_prepare(self, command):
        return None

    def prepare(self, command, business_data):
        raise AssertionError("prepare must not persist invalid resolver data")


class MismatchedResolver:
    def resolve(self, contract_id):
        return DpaeBusinessData(
            contract_id="other-contract",
            canonical_payload='{"private":"must-not-leak"}',
            source_fingerprint="source-fingerprint",
            rules_version="rules-v1",
            payload_hash="payload-hash",
        )


def command():
    return PrepareDpae(
        command_id="cmd-structured-error",
        case_key="case-key",
        contract_id="contract-42",
        actor_id="operator-1",
    )


def test_missing_resolver_exposes_stable_code_and_technical_context():
    service = DpaeService(NoReplayAdapter())

    with pytest.raises(DpaeConfigurationError) as caught:
        service.prepare(command())

    error = caught.value
    assert error.code == "DPAE_BUSINESS_RESOLVER_REQUIRED"
    assert error.entity_type == "contract"
    assert error.entity_id == "contract-42"
    assert error.field is None


def test_resolver_contract_mismatch_exposes_stable_code_without_payload_leak():
    service = DpaeService(NoReplayAdapter(), resolver=MismatchedResolver())

    with pytest.raises(DpaeDataError) as caught:
        service.prepare(command())

    error = caught.value
    assert error.code == "DPAE_RESOLVER_CONTRACT_MISMATCH"
    assert error.field == "contract_id"
    assert error.entity_type == "contract"
    assert error.entity_id == "contract-42"
    assert "must-not-leak" not in str(error)
    assert "payload-hash" not in str(error)
    assert "source-fingerprint" not in str(error)


def test_structured_errors_preserve_legacy_runtime_and_value_error_compatibility():
    assert issubclass(DpaeConfigurationError, RuntimeError)
    assert issubclass(DpaeDataError, ValueError)
