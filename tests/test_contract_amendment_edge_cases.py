from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

from application.services.contract_amendment import (
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
    return ContractEditCommand(
        contract_id=snapshot.contract_id,
        contract_type_code=snapshot.contract_type_code,
        convention_code=snapshot.convention_code,
        ccns_group=changes.get("ccns_group", snapshot.ccns_group),
        cee_qualification=changes.get("cee_qualification", snapshot.cee_qualification),
        weekly_hours=changes.get("weekly_hours", snapshot.weekly_hours),
        gross_monthly_salary=changes.get(
            "gross_monthly_salary", snapshot.gross_monthly_salary
        ),
        gross_annual_salary=changes.get(
            "gross_annual_salary", snapshot.gross_annual_salary
        ),
        start_date=changes.get("start_date", snapshot.start_date),
        end_date=changes.get("end_date", snapshot.end_date),
        break_date=changes.get("break_date", snapshot.break_date),
        modern_fields_supported=snapshot.modern_fields_supported,
    )


def _command(snapshot, **changes):
    return ContractAmendmentCommand(
        edit=_edit(snapshot, **changes),
        effective_date=date(2026, 9, 1),
        idempotency_key=changes.get("idempotency_key", "edge-001"),
        expected_before_hash=contract_state_hash(snapshot),
        expected_person_id=snapshot.person_id,
    )


class CompactPort:
    def __init__(self, snapshot):
        self.current = snapshot
        self.pending = None
        self.pending_record = None
        self.record = None
        self.commits = 0
        self.rollbacks = 0
        self.insert_calls = 0
        self.update_calls = 0

    def find_amendment_by_key(self, key):
        return self.record if self.record and self.record.idempotency_key == key else None

    def lock_contract(self, contract_id):
        if self.current is None or self.current.contract_id != contract_id:
            return None
        return self.current

    def latest_amendment(self, contract_id):
        return self.record if self.record and self.record.contract_id == contract_id else None

    def insert_amendment(self, **values):
        self.insert_calls += 1
        self.pending_record = ContractAmendmentRecord(
            amendment_id=1,
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
        return 1

    def read_amendment(self, amendment_id):
        return self.record if self.record and self.record.amendment_id == amendment_id else None

    def read_contract(self, contract_id):
        return self.current if self.current and self.current.contract_id == contract_id else None

    def contract_exists(self, contract_id):
        return self.current is not None and self.current.contract_id == contract_id

    def update_contract(self, command):
        self.update_calls += 1
        self.pending = replace(
            self.current,
            ccns_group=command.ccns_group,
            cee_qualification=command.cee_qualification,
            weekly_hours=command.weekly_hours,
            gross_monthly_salary=command.gross_monthly_salary,
            gross_annual_salary=command.gross_annual_salary,
            start_date=command.start_date,
            end_date=command.end_date,
            break_date=command.break_date,
        )
        return 1

    def commit(self):
        self.commits += 1
        if self.pending is not None:
            self.current = self.pending
        if self.pending_record is not None:
            self.record = self.pending_record
        self.pending = None
        self.pending_record = None

    def rollback(self):
        self.rollbacks += 1
        self.pending = None
        self.pending_record = None

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


def test_missing_contract_is_rejected_before_history_insert():
    original = _snapshot()
    port = CompactPort(None)

    result = apply_contract_amendment(
        port,
        command=_command(original, gross_monthly_salary=Decimal("3200.00")),
        business_date=date(2026, 9, 29),
    )

    assert result.code == WriteCode.TARGET_NOT_FOUND
    assert result.committed is False
    assert port.insert_calls == 0
    assert port.commits == 0


def test_noop_amendment_is_rejected_without_write():
    original = _snapshot()
    port = CompactPort(original)

    result = apply_contract_amendment(
        port,
        command=_command(original),
        business_date=date(2026, 9, 29),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "aucune clause" in result.message
    assert port.insert_calls == 0
    assert port.update_calls == 0
    assert port.commits == 0


def test_cdd_to_cdi_chain_metadata_survives_later_cdi_amendment():
    original = _snapshot(
        operation_type="CDD_TO_CDI",
        previous_contract_id=301,
    )
    port = CompactPort(original)

    result = apply_contract_amendment(
        port,
        command=_command(original, gross_monthly_salary=Decimal("3200.00")),
        business_date=date(2026, 9, 29),
    )

    assert result.ok is True
    assert result.committed is True
    assert port.current.operation_type == "CDD_TO_CDI"
    assert port.current.previous_contract_id == 301
    assert port.record is not None
    assert port.record.kind == "REMUNERATION"
