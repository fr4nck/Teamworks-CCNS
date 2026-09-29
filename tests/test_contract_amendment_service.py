from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

from application.services.contract_amendment import (
    CONCURRENT_MODIFICATION,
    IDEMPOTENT_REPLAY,
    ContractAmendmentCommand,
    ContractAmendmentRecord,
    apply_contract_amendment,
    contract_state_hash,
)
from application.services.contract_write import ContractEditCommand, ContractEditSnapshot
from application.services.transactional_write import WriteCode


def _snapshot(**changes):
    base = ContractEditSnapshot(
        contract_id=417,
        person_id=12,
        contract_type_code="CDI",
        contract_type_label="CDI",
        convention_code="CCNS",
        ccns_group="G3",
        cee_qualification=None,
        weekly_hours=Decimal("35.00"),
        gross_monthly_salary=Decimal("3000.00"),
        gross_annual_salary=None,
        start_date=date(2026, 1, 1),
        end_date=None,
        break_date=None,
        modern_fields_supported=True,
        operation_type="NEW",
        previous_contract_id=None,
    )
    return replace(base, **changes)


def _edit(snapshot, **changes):
    base = ContractEditCommand(
        contract_id=snapshot.contract_id,
        contract_type_code=snapshot.contract_type_code,
        convention_code=snapshot.convention_code,
        ccns_group=snapshot.ccns_group,
        cee_qualification=snapshot.cee_qualification,
        weekly_hours=snapshot.weekly_hours,
        gross_monthly_salary=snapshot.gross_monthly_salary,
        gross_annual_salary=snapshot.gross_annual_salary,
        start_date=snapshot.start_date,
        end_date=snapshot.end_date,
        break_date=snapshot.break_date,
        modern_fields_supported=snapshot.modern_fields_supported,
    )
    return replace(base, **changes)


def _command(snapshot, *, key="amendment-001", effective=date(2026, 9, 1), **changes):
    return ContractAmendmentCommand(
        edit=_edit(snapshot, **changes),
        effective_date=effective,
        idempotency_key=key,
        expected_before_hash=contract_state_hash(snapshot),
    )


class AmendmentRecordingPort:
    def __init__(self, snapshot=None):
        self.current = snapshot or _snapshot()
        self.pending_snapshot = None
        self.pending_records = []
        self.records = []
        self.next_id = 1
        self.commit_count = 0
        self.rollback_count = 0
        self.fail_insert = False
        self.fail_contract_readback_after_commit = False
        self.fail_amendment_readback = False
        self.committed_once = False

    def lock_contract(self, contract_id):
        return self.current if self.current and self.current.contract_id == contract_id else None

    def read_contract(self, contract_id):
        if self.fail_contract_readback_after_commit and self.committed_once:
            raise RuntimeError("contract readback")
        if self.current is None or self.current.contract_id != contract_id:
            return None
        return self.current

    def contract_exists(self, contract_id):
        return self.current is not None and self.current.contract_id == contract_id

    def update_contract(self, command):
        self.pending_snapshot = replace(
            self.current,
            convention_code=command.convention_code,
            ccns_group=command.ccns_group,
            cee_qualification=command.cee_qualification,
            weekly_hours=command.weekly_hours,
            gross_monthly_salary=command.gross_monthly_salary,
            gross_annual_salary=command.gross_annual_salary,
            start_date=command.start_date,
            end_date=command.end_date,
            break_date=command.break_date,
            modern_fields_supported=command.modern_fields_supported,
        )
        return 1

    def find_amendment_by_key(self, idempotency_key):
        for record in self.records:
            if record.idempotency_key == idempotency_key:
                return record
        return None

    def latest_amendment(self, contract_id):
        candidates = [record for record in self.records if record.contract_id == contract_id]
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: (item.effective_date, item.amendment_id))[-1]

    def insert_amendment(self, **values):
        if self.fail_insert:
            raise RuntimeError("insert amendment")
        amendment_id = self.next_id
        self.next_id += 1
        self.pending_records.append(
            ContractAmendmentRecord(
                amendment_id=amendment_id,
                contract_id=values["contract_id"],
                effective_date=values["effective_date"],
                kind=values["kind"],
                idempotency_key=values["idempotency_key"],
                request_hash=values["request_hash"],
                changed_fields=values["changed_fields"],
                before_hash=values["before_hash"],
                after_hash=values["after_hash"],
                before_payload=values["before_payload"],
                after_payload=values["after_payload"],
                created_at="2026-09-29 12:00:00",
            )
        )
        return amendment_id

    def read_amendment(self, amendment_id):
        if self.fail_amendment_readback:
            raise RuntimeError("amendment readback")
        for record in self.records:
            if record.amendment_id == amendment_id:
                return record
        return None

    def commit(self):
        self.commit_count += 1
        if self.pending_snapshot is not None:
            self.current = self.pending_snapshot
        self.records.extend(self.pending_records)
        self.pending_snapshot = None
        self.pending_records = []
        self.committed_once = True

    def rollback(self):
        self.rollback_count += 1
        self.pending_snapshot = None
        self.pending_records = []

    # Méthodes du port Contrats hors du chemin avenant testé.
    def person_exists(self, person_id):
        raise AssertionError("hors périmètre")

    def available_contract_type_codes(self):
        raise AssertionError("hors périmètre")

    def insert_contract(self, command):
        raise AssertionError("hors périmètre")

    def delete_contract(self, contract_id):
        raise AssertionError("hors périmètre")

    def update_indicator(self, contract_id, field, value):
        raise AssertionError("hors périmètre")

    def read_indicator(self, contract_id, field):
        raise AssertionError("hors périmètre")

    def list_legacy_classifications(self):
        raise AssertionError("hors périmètre")

    def list_legacy_point_values(self):
        raise AssertionError("hors périmètre")

    def update_legacy_classification(self, contract_id, classification_id, point_id):
        raise AssertionError("hors périmètre")


def test_cdi_remuneration_amendment_is_historized_and_applied_once():
    original = _snapshot()
    port = AmendmentRecordingPort(original)
    command = _command(original, gross_monthly_salary=Decimal("3200.00"))

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.ok is True
    assert result.committed is True
    assert result.code == WriteCode.OK
    assert port.commit_count == 1
    assert port.current.gross_monthly_salary == Decimal("3200.00")
    assert len(port.records) == 1
    assert port.records[0].changed_fields == ("gross_monthly_salary",)
    assert port.records[0].kind == "REMUNERATION"
    assert port.records[0].before_hash == contract_state_hash(original)


def test_duration_and_group_change_becomes_multi_clause_amendment():
    original = _snapshot()
    port = AmendmentRecordingPort(original)
    command = _command(
        original,
        weekly_hours=Decimal("28.00"),
        ccns_group="G4",
        gross_monthly_salary=Decimal("3000.00"),
    )

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.ok is True
    assert result.value.kind == "MULTI_CLAUSE"
    assert result.value.changed_fields == ("ccns_group", "weekly_hours")
    assert port.current.operation_type == "NEW"
    assert port.current.previous_contract_id is None


def test_same_idempotency_key_replays_without_second_write():
    original = _snapshot()
    port = AmendmentRecordingPort(original)
    command = _command(original, gross_monthly_salary=Decimal("3200.00"))

    first = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))
    second = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert first.ok is True
    assert second.ok is True
    assert second.code == IDEMPOTENT_REPLAY
    assert port.commit_count == 1
    assert len(port.records) == 1


def test_reusing_idempotency_key_for_different_request_is_rejected():
    original = _snapshot()
    port = AmendmentRecordingPort(original)
    first = _command(original, gross_monthly_salary=Decimal("3200.00"))
    apply_contract_amendment(port, command=first, business_date=date(2026, 9, 29))
    second = ContractAmendmentCommand(
        edit=_edit(port.current, gross_monthly_salary=Decimal("3300.00")),
        effective_date=date(2026, 9, 2),
        idempotency_key="amendment-001",
        expected_before_hash=contract_state_hash(port.current),
    )

    result = apply_contract_amendment(port, command=second, business_date=date(2026, 9, 29))

    assert result.code == WriteCode.VALIDATION_ERROR
    assert port.commit_count == 1


def test_stale_expected_state_is_rejected_as_concurrent_modification():
    original = _snapshot()
    command = _command(original, gross_monthly_salary=Decimal("3200.00"))
    port = AmendmentRecordingPort(
        replace(original, gross_monthly_salary=Decimal("3100.00"))
    )

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.code == CONCURRENT_MODIFICATION
    assert result.committed is False
    assert port.commit_count == 0
    assert port.records == []


def test_future_effect_is_not_projected_early():
    original = _snapshot()
    port = AmendmentRecordingPort(original)
    command = _command(
        original,
        effective=date(2026, 10, 1),
        gross_monthly_salary=Decimal("3200.00"),
    )

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "effet futur" in result.message
    assert port.current == original
    assert port.records == []


def test_cdd_amendment_preserves_renewal_chain_metadata():
    original = _snapshot(
        contract_type_code="CDD",
        contract_type_label="CDD",
        end_date=date(2026, 12, 31),
        operation_type="CDD_RENEWAL",
        previous_contract_id=301,
    )
    port = AmendmentRecordingPort(original)
    command = _command(original, weekly_hours=Decimal("32.00"))

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.ok is True
    assert port.current.operation_type == "CDD_RENEWAL"
    assert port.current.previous_contract_id == 301
    assert result.value.kind == "WORKING_TIME"


def test_renewal_dates_cannot_be_smuggled_through_generic_amendment():
    original = _snapshot(
        contract_type_code="CDD",
        contract_type_label="CDD",
        end_date=date(2026, 12, 31),
    )
    port = AmendmentRecordingPort(original)
    command = ContractAmendmentCommand(
        edit=_edit(original, end_date=date(2027, 1, 31)),
        effective_date=date(2026, 9, 1),
        idempotency_key="amendment-renewal-bypass",
        expected_before_hash=contract_state_hash(original),
    )

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "renouvellement CDD" in result.message
    assert port.records == []


def test_business_validation_failure_rolls_back_pending_history():
    original = _snapshot()
    port = AmendmentRecordingPort(original)
    command = _command(original, gross_monthly_salary=Decimal("1.00"))

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert port.rollback_count >= 1
    assert port.records == []
    assert port.current == original


def test_readback_failure_after_commit_never_claims_a_rollback():
    original = _snapshot()
    port = AmendmentRecordingPort(original)
    port.fail_contract_readback_after_commit = True
    command = _command(original, gross_monthly_salary=Decimal("3200.00"))

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.code == WriteCode.READBACK_ERROR
    assert result.committed is True
    assert port.commit_count == 1
    assert len(port.records) == 1
    assert port.current.gross_monthly_salary == Decimal("3200.00")


def test_amendment_before_contract_start_is_rejected():
    original = _snapshot(start_date=date(2026, 9, 10))
    port = AmendmentRecordingPort(original)
    command = _command(
        original,
        effective=date(2026, 9, 1),
        gross_monthly_salary=Decimal("3200.00"),
    )

    result = apply_contract_amendment(port, command=command, business_date=date(2026, 9, 29))

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "antérieure au début" in result.message
    assert port.records == []
