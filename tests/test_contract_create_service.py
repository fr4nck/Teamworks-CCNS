from __future__ import annotations

from datetime import date
from decimal import Decimal

from application.services.contract_write import (
    ContractCreateCommand,
    ContractEditSnapshot,
    create_contract,
)
from application.services.transactional_write import WriteCode


def _command(**changes):
    values = dict(
        person_id=12,
        contract_type_code="CDI",
        convention_code="CCNS",
        ccns_group="G3",
        cee_qualification=None,
        weekly_hours=Decimal("35.00"),
        gross_monthly_salary=Decimal("3000.00"),
        gross_annual_salary=None,
        start_date=date(2026, 10, 1),
        end_date=None,
        trial_period_value=2,
        trial_period_unit="MONTH",
        confirm_no_trial=False,
    )
    values.update(changes)
    return ContractCreateCommand(**values)


def _snapshot(contract_id=900):
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
        start_date=date(2026, 10, 1),
        end_date=None,
        break_date=None,
        modern_fields_supported=True,
    )


class CreateRecordingPort:
    def __init__(
        self,
        *,
        person_exists=True,
        available=("CDI", "CDD"),
        created_id=900,
        fail_insert=False,
        fail_readback=False,
    ):
        self.person_found = person_exists
        self.available = available
        self.created_id = created_id
        self.fail_insert = fail_insert
        self.fail_readback = fail_readback
        self.calls = []
        self.committed = False

    def person_exists(self, person_id):
        self.calls.append(("person_exists", person_id))
        return self.person_found

    def available_contract_type_codes(self):
        self.calls.append(("types",))
        return self.available

    def insert_contract(self, command):
        self.calls.append(("insert", command.person_id, command.contract_type_code))
        if self.fail_insert:
            raise RuntimeError("insert")
        return self.created_id

    def commit(self):
        self.calls.append(("commit",))
        self.committed = True

    def rollback(self):
        self.calls.append(("rollback",))

    def read_contract(self, contract_id):
        self.calls.append(("readback", contract_id))
        if self.fail_readback:
            raise RuntimeError("readback")
        return _snapshot(contract_id)

    # Autres méthodes du port non utilisées par ce use case.
    def contract_exists(self, contract_id):
        raise AssertionError("hors périmètre")

    def update_contract(self, command):
        raise AssertionError("hors périmètre")

    def update_indicator(self, contract_id, field, value):
        raise AssertionError("hors périmètre")

    def read_indicator(self, contract_id, field):
        raise AssertionError("hors périmètre")


def test_create_contract_validates_before_any_database_call():
    port = CreateRecordingPort()

    result = create_contract(
        port,
        command=_command(gross_monthly_salary=Decimal("1.00")),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert port.calls == []


def test_create_contract_missing_person_never_inserts():
    port = CreateRecordingPort(person_exists=False)

    result = create_contract(port, command=_command())

    assert result.code == WriteCode.TARGET_NOT_FOUND
    assert result.committed is False
    assert port.calls == [("person_exists", 12)]


def test_create_contract_missing_type_never_inserts():
    port = CreateRecordingPort(available=("CDD",))

    result = create_contract(port, command=_command())

    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert not any(call[0] == "insert" for call in port.calls)
    assert ("commit",) not in port.calls


def test_create_contract_commits_once_and_reads_created_id():
    port = CreateRecordingPort(created_id=900)

    result = create_contract(port, command=_command())

    assert result.ok is True
    assert result.code == WriteCode.OK
    assert result.committed is True
    assert result.target_id == 900
    assert result.value is not None
    assert result.value.contract_id == 900
    assert port.calls == [
        ("person_exists", 12),
        ("types",),
        ("insert", 12, "CDI"),
        ("commit",),
        ("readback", 900),
    ]


def test_create_contract_insert_error_rolls_back_without_commit():
    port = CreateRecordingPort(fail_insert=True)

    result = create_contract(port, command=_command())

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls


def test_create_contract_invalid_created_id_rolls_back():
    port = CreateRecordingPort(created_id=0)

    result = create_contract(port, command=_command())

    assert result.code == WriteCode.INVALID_TARGET_ID
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls


def test_create_contract_readback_failure_is_distinguished_after_commit():
    port = CreateRecordingPort(fail_readback=True)

    result = create_contract(port, command=_command())

    assert result.code == WriteCode.READBACK_ERROR
    assert result.ok is False
    assert result.committed is True
    assert result.target_id == 900
    assert ("commit",) in port.calls
    assert ("rollback",) not in port.calls


def test_zero_trial_requires_explicit_confirmation():
    port = CreateRecordingPort()

    result = create_contract(
        port,
        command=_command(
            trial_period_value=0,
            trial_period_unit="DAY",
            confirm_no_trial=False,
        ),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "Confirmez explicitement" in result.message
    assert port.calls == []
