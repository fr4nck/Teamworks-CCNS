from __future__ import annotations

from datetime import date
from decimal import Decimal

from application.services.contract_write import (
    ContractEditSnapshot,
    ContractLegacyClassificationCommand,
    load_legacy_contract_options,
    update_contract_legacy_classification,
)
from application.services.transactional_write import WriteCode


def _snapshot(**changes):
    values = dict(
        contract_id=417,
        person_id=12,
        contract_type_code="CDD",
        contract_type_label="CDD",
        convention_code=None,
        ccns_group=None,
        cee_qualification=None,
        weekly_hours=None,
        gross_monthly_salary=None,
        gross_annual_salary=None,
        start_date=date(2026, 9, 15),
        end_date=date(2026, 12, 31),
        break_date=None,
        modern_fields_supported=True,
        operation_type="NEW",
        previous_contract_id=None,
        legacy_classification_id=2,
        legacy_point_id=10,
    )
    values.update(changes)
    return ContractEditSnapshot(**values)


class RecordingPort:
    def __init__(self, *, snapshot=None, ignore_update=False):
        self.snapshot = snapshot or _snapshot()
        self.ignore_update = ignore_update
        self.calls = []
        self.committed = False
        self.updated_classification_id = self.snapshot.legacy_classification_id
        self.updated_point_id = self.snapshot.legacy_point_id

    def read_contract(self, contract_id):
        self.calls.append(("read_contract", contract_id))
        if contract_id != self.snapshot.contract_id:
            return None
        return _snapshot(
            legacy_classification_id=self.updated_classification_id,
            legacy_point_id=self.updated_point_id,
            convention_code=self.snapshot.convention_code,
            ccns_group=self.snapshot.ccns_group,
            contract_type_code=self.snapshot.contract_type_code,
            start_date=self.snapshot.start_date,
        )

    def list_legacy_classifications(self):
        self.calls.append(("classifications",))
        return (
            (1, "Personnel de service"),
            (2, "Animateur BAFA"),
            (3, "Direction"),
        )

    def list_legacy_point_values(self):
        self.calls.append(("points",))
        return (
            (9, Decimal("6.10"), "2026-01-01"),
            (10, Decimal("6.20"), "2026-09-01"),
            (11, Decimal("6.30"), "2026-10-01"),
        )

    def contract_exists(self, contract_id):
        self.calls.append(("exists", contract_id))
        return contract_id == self.snapshot.contract_id

    def update_legacy_classification(self, contract_id, classification_id, point_id):
        self.calls.append(
            ("update_legacy", contract_id, classification_id, point_id)
        )
        if not self.ignore_update:
            self.updated_classification_id = classification_id
            self.updated_point_id = point_id
        return 1

    def commit(self):
        self.calls.append(("commit",))
        self.committed = True

    def rollback(self):
        self.calls.append(("rollback",))


def test_legacy_options_select_latest_point_effective_on_contract_date():
    port = RecordingPort()

    result = load_legacy_contract_options(
        port,
        reference_date=date(2026, 9, 15),
    )

    assert result.ok is True
    assert result.value is not None
    assert [item.classification_id for item in result.value.classifications] == [1, 2, 3]
    assert [item.point_id for item in result.value.point_values] == [9, 10, 11]
    assert result.value.applicable_point_id == 10


def test_legacy_options_do_not_use_future_point_value():
    port = RecordingPort()

    result = load_legacy_contract_options(
        port,
        reference_date=date(2026, 8, 31),
    )

    assert result.ok is True
    assert result.value is not None
    assert result.value.applicable_point_id == 9


def test_legacy_classification_update_commits_and_reads_back_both_historical_ids():
    port = RecordingPort()

    result = update_contract_legacy_classification(
        port,
        command=ContractLegacyClassificationCommand(
            contract_id=417,
            classification_id=3,
            point_id=10,
        ),
    )

    assert result.ok is True
    assert result.code == WriteCode.OK
    assert result.committed is True
    assert result.value is not None
    assert result.value.legacy_classification_id == 3
    assert result.value.legacy_point_id == 10
    assert port.calls == [
        ("read_contract", 417),
        ("classifications",),
        ("points",),
        ("exists", 417),
        ("update_legacy", 417, 3, 10),
        ("commit",),
        ("read_contract", 417),
    ]


def test_legacy_classification_rejects_point_not_applicable_to_contract_date():
    port = RecordingPort()

    result = update_contract_legacy_classification(
        port,
        command=ContractLegacyClassificationCommand(
            contract_id=417,
            classification_id=3,
            point_id=11,
        ),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "ne correspond pas à la date" in result.message
    assert not any(call[0] == "update_legacy" for call in port.calls)
    assert ("commit",) not in port.calls


def test_legacy_classification_rejects_unknown_classification():
    port = RecordingPort()

    result = update_contract_legacy_classification(
        port,
        command=ContractLegacyClassificationCommand(
            contract_id=417,
            classification_id=999,
            point_id=10,
        ),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "n'existe pas" in result.message
    assert not any(call[0] == "update_legacy" for call in port.calls)


def test_legacy_classification_is_not_used_for_modern_ccns_contract():
    port = RecordingPort(
        snapshot=_snapshot(convention_code="CCNS", ccns_group="G3"),
    )

    result = update_contract_legacy_classification(
        port,
        command=ContractLegacyClassificationCommand(
            contract_id=417,
            classification_id=3,
            point_id=10,
        ),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "groupe CCNS" in result.message
    assert ("classifications",) not in port.calls


def test_legacy_classification_is_not_used_for_cee():
    port = RecordingPort(
        snapshot=_snapshot(
            contract_type_code="CEE",
            convention_code="CCNS",
            ccns_group=None,
        ),
    )

    result = update_contract_legacy_classification(
        port,
        command=ContractLegacyClassificationCommand(
            contract_id=417,
            classification_id=3,
            point_id=10,
        ),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "CEE" in result.message
    assert ("classifications",) not in port.calls



def test_legacy_classification_detects_post_commit_readback_mismatch():
    port = RecordingPort(ignore_update=True)

    result = update_contract_legacy_classification(
        port,
        command=ContractLegacyClassificationCommand(
            contract_id=417,
            classification_id=3,
            point_id=10,
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.READBACK_ERROR
    assert result.committed is True
    assert ("commit",) in port.calls
    assert ("rollback",) not in port.calls
