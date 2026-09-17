from pathlib import Path
import sqlite3

import pytest

from application.services.contract_write import update_contract_indicator
from application.services.transactional_write import WriteCode
from infrastructure.persistence.contract_write_adapter import GestionDbContractWriteAdapter


class RecordingPort:
    def __init__(
        self,
        *,
        exists=True,
        affected=1,
        read_value="Oui",
        fail_exists=False,
        fail_write=False,
        fail_commit=False,
        fail_readback=False,
    ):
        self.exists = exists
        self.affected = affected
        self.read_value = read_value
        self.fail_exists = fail_exists
        self.fail_write = fail_write
        self.fail_commit = fail_commit
        self.fail_readback = fail_readback
        self.calls = []

    def contract_exists(self, contract_id):
        self.calls.append(("exists", contract_id))
        if self.fail_exists:
            raise RuntimeError("preflight")
        return self.exists

    def update_indicator(self, contract_id, field, value):
        self.calls.append(("write", contract_id, field, value))
        if self.fail_write:
            raise RuntimeError("sql")
        return self.affected

    def commit(self):
        self.calls.append(("commit",))
        if self.fail_commit:
            raise RuntimeError("commit")

    def rollback(self):
        self.calls.append(("rollback",))

    def read_indicator(self, contract_id, field):
        self.calls.append(("readback", contract_id, field))
        if self.fail_readback:
            raise RuntimeError("readback")
        return self.read_value


@pytest.mark.parametrize("target_id", [None, 0, -1, "12", True])
def test_invalid_stable_id_is_rejected_before_any_database_call(target_id):
    port = RecordingPort()

    result = update_contract_indicator(
        port,
        contract_id=target_id,
        field="signature",
        value="Oui",
    )

    assert result.ok is False
    assert result.code == WriteCode.INVALID_TARGET_ID
    assert result.committed is False
    assert port.calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("classification", "Oui"),
        ("signature", "1"),
        ("due", None),
    ],
)
def test_invalid_contract_indicator_is_rejected_before_write(field, value):
    port = RecordingPort()

    result = update_contract_indicator(
        port,
        contract_id=17,
        field=field,
        value=value,
    )

    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert port.calls == []


def test_missing_target_never_writes_or_commits():
    port = RecordingPort(exists=False)

    result = update_contract_indicator(
        port,
        contract_id=17,
        field="due",
        value="Oui",
    )

    assert result.code == WriteCode.TARGET_NOT_FOUND
    assert result.committed is False
    assert port.calls == [("exists", 17)]


def test_success_commits_once_then_reads_back():
    port = RecordingPort(read_value="Oui")

    result = update_contract_indicator(
        port,
        contract_id=17,
        field="signature",
        value="Oui",
    )

    assert result.ok is True
    assert result.code == WriteCode.OK
    assert result.committed is True
    assert result.value == "Oui"
    assert port.calls == [
        ("exists", 17),
        ("write", 17, "signature", "Oui"),
        ("commit",),
        ("readback", 17, "signature"),
    ]


def test_sql_failure_rolls_back_without_commit():
    port = RecordingPort(fail_write=True)

    result = update_contract_indicator(
        port,
        contract_id=17,
        field="signature",
        value="Oui",
    )

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls
    assert not any(call[0] == "readback" for call in port.calls)


def test_commit_failure_attempts_rollback():
    port = RecordingPort(fail_commit=True)

    result = update_contract_indicator(
        port,
        contract_id=17,
        field="signature",
        value="Oui",
    )

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert port.calls[-1] == ("rollback",)


def test_zero_rowcount_is_not_a_false_success():
    port = RecordingPort(affected=0)

    result = update_contract_indicator(
        port,
        contract_id=17,
        field="signature",
        value="Oui",
    )

    assert result.code == WriteCode.TARGET_NOT_FOUND
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls


def test_multiple_rows_affected_is_rejected_and_rolled_back():
    port = RecordingPort(affected=2)

    result = update_contract_indicator(
        port,
        contract_id=17,
        field="due",
        value="",
    )

    assert result.code == WriteCode.UNEXPECTED_ROWCOUNT
    assert result.committed is False
    assert ("rollback",) in port.calls
    assert ("commit",) not in port.calls


def test_readback_failure_reports_that_write_is_already_committed():
    port = RecordingPort(fail_readback=True)

    result = update_contract_indicator(
        port,
        contract_id=17,
        field="due",
        value="Oui",
    )

    assert result.code == WriteCode.READBACK_ERROR
    assert result.ok is False
    assert result.committed is True
    assert port.calls[-2:] == [
        ("commit",),
        ("readback", 17, "due"),
    ]
    assert ("rollback",) not in port.calls


class SqliteGestionDbCompat:
    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.echec = 0
        self.isNetwork = False
        self.commit_count = 0
        self.cursor.execute(
            "CREATE TABLE contrats ("
            "IDcontrat INTEGER PRIMARY KEY, "
            "signature TEXT, "
            "due TEXT)"
        )
        self.cursor.execute(
            "INSERT INTO contrats (IDcontrat, signature, due) VALUES (?, ?, ?)",
            (17, "", ""),
        )
        self.connexion.commit()

    def Commit(self):
        self.commit_count += 1
        self.connexion.commit()


def test_sqlite_adapter_roundtrip_uses_stable_contract_id_and_real_rowcount():
    db = SqliteGestionDbCompat()
    adapter = GestionDbContractWriteAdapter(db)

    result = update_contract_indicator(
        adapter,
        contract_id=17,
        field="signature",
        value="Oui",
    )

    assert result.ok is True
    assert result.value == "Oui"
    assert result.committed is True
    assert db.commit_count == 1
    assert db.connexion.execute(
        "SELECT signature FROM contrats WHERE IDcontrat=17"
    ).fetchone() == ("Oui",)


def test_write_boundary_has_no_wx_or_qt_dependency():
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "application/services/transactional_write.py",
        "application/services/contract_write.py",
        "infrastructure/persistence/contract_write_adapter.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert "import wx" not in source
        assert "from wx" not in source
        assert "PySide6" not in source
