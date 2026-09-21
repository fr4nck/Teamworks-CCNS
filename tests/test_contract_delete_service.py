from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from application.services.contract_write import (
    ContractDeleteCommand,
    ContractEditSnapshot,
    delete_contract,
)
from application.services.transactional_write import WriteCode


def _snapshot(contract_id=417):
    return ContractEditSnapshot(
        contract_id=contract_id,
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


class DeleteRecordingPort:
    def __init__(
        self,
        *,
        exists=True,
        affected=1,
        fail_delete=False,
        fail_readback=False,
        readback_still_exists=False,
    ):
        self.exists = exists
        self.affected = affected
        self.fail_delete = fail_delete
        self.fail_readback = fail_readback
        self.readback_still_exists = readback_still_exists
        self.calls = []
        self.committed = False

    def contract_exists(self, contract_id):
        self.calls.append(("exists", contract_id))
        return self.exists

    def delete_contract(self, contract_id):
        self.calls.append(("delete", contract_id))
        if self.fail_delete:
            raise RuntimeError("delete")
        if self.affected == 1:
            self.exists = False
        return self.affected

    def commit(self):
        self.calls.append(("commit",))
        self.committed = True

    def rollback(self):
        self.calls.append(("rollback",))
        self.exists = True

    def read_contract(self, contract_id):
        self.calls.append(("readback", contract_id))
        if self.fail_readback:
            raise RuntimeError("readback")
        if self.readback_still_exists:
            return _snapshot(contract_id)
        return None

    # Autres méthodes du port non utilisées par ce use case.
    def person_exists(self, person_id):
        raise AssertionError("hors périmètre")

    def available_contract_type_codes(self):
        raise AssertionError("hors périmètre")

    def insert_contract(self, command):
        raise AssertionError("hors périmètre")

    def update_contract(self, command):
        raise AssertionError("hors périmètre")

    def update_indicator(self, contract_id, field, value):
        raise AssertionError("hors périmètre")

    def read_indicator(self, contract_id, field):
        raise AssertionError("hors périmètre")


def test_delete_requires_explicit_confirmation_before_database_access():
    port = DeleteRecordingPort()

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=417, confirmed=False),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert port.calls == []


@pytest.mark.parametrize("invalid_id", [None, 0, -1, True, False])
def test_delete_invalid_id_is_rejected_before_database_access(invalid_id):
    port = DeleteRecordingPort()

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=invalid_id, confirmed=True),
    )

    assert result.code == WriteCode.INVALID_TARGET_ID
    assert result.committed is False
    assert port.calls == []


def test_delete_missing_target_does_not_write_or_commit():
    port = DeleteRecordingPort(exists=False)

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=417, confirmed=True),
    )

    assert result.code == WriteCode.TARGET_NOT_FOUND
    assert result.committed is False
    assert port.calls == [("exists", 417)]


def test_delete_rowcount_zero_rolls_back_without_commit():
    port = DeleteRecordingPort(affected=0)

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=417, confirmed=True),
    )

    assert result.code == WriteCode.TARGET_NOT_FOUND
    assert result.committed is False
    assert port.calls == [
        ("exists", 417),
        ("delete", 417),
        ("rollback",),
    ]


def test_delete_rowcount_multiple_is_never_success():
    port = DeleteRecordingPort(affected=2)

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=417, confirmed=True),
    )

    assert result.code == WriteCode.UNEXPECTED_ROWCOUNT
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls


def test_delete_sql_error_rolls_back_without_commit():
    port = DeleteRecordingPort(fail_delete=True)

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=417, confirmed=True),
    )

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls


def test_delete_commits_once_and_confirms_absence_after_commit():
    port = DeleteRecordingPort()

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=417, confirmed=True),
    )

    assert result.ok is True
    assert result.code == WriteCode.OK
    assert result.committed is True
    assert result.target_id == 417
    assert result.value is True
    assert port.calls == [
        ("exists", 417),
        ("delete", 417),
        ("commit",),
        ("readback", 417),
    ]


def test_delete_readback_error_is_distinguished_after_commit():
    port = DeleteRecordingPort(fail_readback=True)

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=417, confirmed=True),
    )

    assert result.code == WriteCode.READBACK_ERROR
    assert result.ok is False
    assert result.committed is True
    assert ("commit",) in port.calls
    assert ("rollback",) not in port.calls


def test_delete_readback_that_still_finds_target_is_not_success():
    port = DeleteRecordingPort(readback_still_exists=True)

    result = delete_contract(
        port,
        command=ContractDeleteCommand(contract_id=417, confirmed=True),
    )

    assert result.code == WriteCode.READBACK_ERROR
    assert result.ok is False
    assert result.committed is True
    assert result.value is False
