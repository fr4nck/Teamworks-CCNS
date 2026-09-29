from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from infrastructure.persistence.contract_amendment_adapter import (
    AMENDMENT_TABLE,
    GestionDbContractAmendmentAdapter,
)


MODERN_COLUMNS = (
    "IDcontrat",
    "IDpersonne",
    "IDclassification",
    "IDtype",
    "valeur_point",
    "date_debut",
    "date_fin",
    "date_rupture",
    "essai",
    "signature",
    "due",
    "convention_code",
    "ccns_group",
    "cee_qualification",
    "weekly_hours",
    "gross_monthly_salary",
    "gross_annual_salary",
    "operation_type",
    "previous_contract_id",
    "trial_period_value",
    "trial_period_unit",
)


class FakeMySqlCursor:
    def __init__(self):
        self.executed = []
        self.rowcount = 1
        self._last_query = ""

    def execute(self, query, params=None):
        self._last_query = query
        self.executed.append((query, params))
        self.rowcount = 1

    def fetchone(self):
        if "SELECT IDcontrat FROM contrats" in self._last_query:
            return (501,)
        if "FROM contrats c" in self._last_query:
            return (
                12,
                4,
                "CDD",
                "CDD",
                "2026-01-01",
                "2026-12-31",
                None,
                2,
                10,
                0,
                "CCNS",
                "G3",
                None,
                Decimal("35.00"),
                Decimal("3000.00"),
                None,
                "CDD_RENEWAL",
                400,
                0,
                "DAY",
            )
        if "FROM tw_contract_amendment" in self._last_query:
            return (
                77,
                501,
                "2026-09-01",
                "REMUNERATION",
                "amendment-001",
                "a" * 64,
                "gross_monthly_salary",
                "b" * 64,
                "c" * 64,
                '{"gross_monthly_salary":"3000.00"}',
                '{"gross_monthly_salary":"3200.00"}',
                "2026-09-29 12:00:00",
            )
        return None


class FakeMySqlDb:
    def __init__(self):
        self.isNetwork = True
        self.echec = 0
        self.cursor = FakeMySqlCursor()
        self.connexion = self
        self.req_insert_calls = []
        self.commits = 0
        self.rollbacks = 0

    def GetListeChamps2(self, table_name):
        assert table_name == "contrats"
        return tuple((name, "VARCHAR(255)") for name in MODERN_COLUMNS)

    def ReqInsert(self, table_name, data, commit=True):
        self.req_insert_calls.append((table_name, tuple(data), commit))
        return 77

    def Commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_network_adapter_locks_contract_row_before_reading_snapshot():
    db = FakeMySqlDb()
    adapter = GestionDbContractAmendmentAdapter(db)

    snapshot = adapter.lock_contract(501)

    assert snapshot is not None
    assert snapshot.contract_id == 501
    assert snapshot.operation_type == "CDD_RENEWAL"
    assert snapshot.previous_contract_id == 400
    lock_query, lock_params = db.cursor.executed[0]
    assert "SELECT IDcontrat FROM contrats WHERE IDcontrat=%s FOR UPDATE" in lock_query
    assert lock_params == (501,)
    assert "?" not in lock_query


def test_amendment_insert_is_append_only_and_never_commits_adapter_side():
    db = FakeMySqlDb()
    adapter = GestionDbContractAmendmentAdapter(db)

    amendment_id = adapter.insert_amendment(
        contract_id=501,
        effective_date=date(2026, 9, 1),
        kind="REMUNERATION",
        idempotency_key="amendment-001",
        request_hash="a" * 64,
        changed_fields=("gross_monthly_salary",),
        before_hash="b" * 64,
        after_hash="c" * 64,
        before_payload='{"gross_monthly_salary":"3000.00"}',
        after_payload='{"gross_monthly_salary":"3200.00"}',
    )

    assert amendment_id == 77
    assert db.commits == 0
    assert db.rollbacks == 0
    assert len(db.req_insert_calls) == 1
    table_name, data, commit = db.req_insert_calls[0]
    assert table_name == AMENDMENT_TABLE
    assert commit is False
    assert ("contract_id", 501) in data
    assert ("idempotency_key", "amendment-001") in data
    assert ("changed_fields", "gross_monthly_salary") in data


def test_amendment_readback_keeps_chain_metadata_separate_from_history():
    db = FakeMySqlDb()
    adapter = GestionDbContractAmendmentAdapter(db)

    record = adapter.read_amendment(77)

    assert record is not None
    assert record.contract_id == 501
    assert record.kind == "REMUNERATION"
    assert record.changed_fields == ("gross_monthly_salary",)
    query, params = db.cursor.executed[-1]
    assert "FROM tw_contract_amendment" in query
    assert "amendment_id=%s" in query
    assert params == (77,)
    assert "?" not in query


def test_mysql55_schema_uses_only_legacy_compatible_primitives():
    sql_path = (
        Path(__file__).resolve().parents[1]
        / "infrastructure"
        / "persistence"
        / "sql"
        / "contract_amendment_v1.sql"
    )
    sql = sql_path.read_text(encoding="utf-8")
    sql_without_comments = "\n".join(
        line.split("--", 1)[0] for line in sql.splitlines()
    )
    upper = sql_without_comments.upper()

    assert "CREATE TABLE IF NOT EXISTS TW_CONTRACT_AMENDMENT" in upper
    assert "ENGINE=INNODB" in upper
    assert "UNIQUE KEY UQ_TW_CONTRACT_AMENDMENT_IDEMPOTENCY" in upper
    assert "IX_TW_CONTRACT_AMENDMENT_CONTRACT_EFFECTIVE" in upper
    assert " JSON" not in upper
    assert "GENERATED" not in upper
    assert " CHECK " not in upper
