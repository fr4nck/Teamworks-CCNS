from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

from application.services.contract_write import (
    ContractEditCommand,
    ContractEditSnapshot,
    update_contract,
)
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
        start_date=date(2026, 9, 1),
        end_date=None,
        break_date=None,
        modern_fields_supported=True,
    )
    return replace(base, **changes)


def _command(snapshot, **changes):
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


class EditRecordingPort:
    def __init__(
        self,
        snapshot=None,
        *,
        affected=1,
        fail_write=False,
        fail_readback=False,
    ):
        self.current = snapshot or _snapshot()
        self.affected = affected
        self.fail_write = fail_write
        self.fail_readback = fail_readback
        self.calls = []
        self.committed = False

    def read_contract(self, contract_id):
        self.calls.append(("read_contract", contract_id))
        if self.fail_readback and self.committed:
            raise RuntimeError("readback")
        return self.current if contract_id == self.current.contract_id else None

    def contract_exists(self, contract_id):
        self.calls.append(("exists", contract_id))
        return contract_id == self.current.contract_id

    def update_contract(self, command):
        self.calls.append(("write", command.contract_id))
        if self.fail_write:
            raise RuntimeError("sql")
        self.current = ContractEditSnapshot(
            contract_id=command.contract_id,
            person_id=self.current.person_id,
            contract_type_code=command.contract_type_code,
            contract_type_label=self.current.contract_type_label,
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
        return self.affected

    def commit(self):
        self.calls.append(("commit",))
        self.committed = True

    def rollback(self):
        self.calls.append(("rollback",))

    # Le même port sert aussi aux indicateurs, sans être utilisé dans ces tests.
    def update_indicator(self, contract_id, field, value):
        raise AssertionError("hors périmètre")

    def read_indicator(self, contract_id, field):
        raise AssertionError("hors périmètre")


def test_invalid_dates_are_rejected_before_write():
    original = _snapshot()
    port = EditRecordingPort(original)
    command = _command(
        original,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 9, 30),
    )

    result = update_contract(port, command=command)

    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert not any(call[0] == "write" for call in port.calls)
    assert ("commit",) not in port.calls


def test_ccns_salary_below_minimum_is_rejected_before_write():
    original = _snapshot()
    port = EditRecordingPort(original)
    command = _command(
        original,
        gross_monthly_salary=Decimal("1.00"),
    )

    result = update_contract(port, command=command)

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "minimum CCNS/SMIC" in result.message
    assert not any(call[0] == "write" for call in port.calls)


def test_modify_contract_commits_once_and_reads_back():
    original = _snapshot()
    port = EditRecordingPort(original)
    command = _command(
        original,
        start_date=date(2026, 10, 1),
        ccns_group="G4",
        weekly_hours=Decimal("28.00"),
        gross_monthly_salary=Decimal("3000.00"),
    )

    result = update_contract(port, command=command)

    assert result.ok is True
    assert result.code == WriteCode.OK
    assert result.committed is True
    assert result.value is not None
    assert result.value.start_date == date(2026, 10, 1)
    assert result.value.ccns_group == "G4"
    assert result.value.weekly_hours == Decimal("28.00")
    assert port.calls == [
        ("read_contract", 417),
        ("exists", 417),
        ("write", 417),
        ("commit",),
        ("read_contract", 417),
    ]


def test_modify_contract_sql_error_rolls_back_without_commit():
    original = _snapshot()
    port = EditRecordingPort(original, fail_write=True)
    command = _command(original, start_date=date(2026, 10, 1))

    result = update_contract(port, command=command)

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls


def test_modify_contract_zero_rowcount_is_not_success():
    original = _snapshot()
    port = EditRecordingPort(original, affected=0)
    command = _command(original, start_date=date(2026, 10, 1))

    result = update_contract(port, command=command)

    assert result.code == WriteCode.TARGET_NOT_FOUND
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls


def test_modify_contract_readback_failure_is_distinguished_after_commit():
    original = _snapshot()
    port = EditRecordingPort(original, fail_readback=True)
    command = _command(original, start_date=date(2026, 10, 1))

    result = update_contract(port, command=command)

    assert result.code == WriteCode.READBACK_ERROR
    assert result.ok is False
    assert result.committed is True
    assert ("commit",) in port.calls
    assert ("rollback",) not in port.calls


def test_no_change_does_not_write_or_commit():
    original = _snapshot()
    port = EditRecordingPort(original)

    result = update_contract(port, command=_command(original))

    assert result.ok is True
    assert result.committed is False
    assert result.message == "Aucune modification à enregistrer."
    assert port.calls == [("read_contract", 417)]


def test_legacy_schema_can_modify_dates_without_modern_ccns_fields():
    original = _snapshot(
        convention_code=None,
        ccns_group=None,
        weekly_hours=None,
        gross_monthly_salary=None,
        modern_fields_supported=False,
    )
    port = EditRecordingPort(original)
    command = _command(
        original,
        start_date=date(2026, 10, 1),
    )

    result = update_contract(port, command=command)

    assert result.ok is True
    assert result.committed is True
    assert result.value.start_date == date(2026, 10, 1)
