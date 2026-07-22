from __future__ import annotations

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID

from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot, ContractSalaryControlSnapshotRow
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory


def _uuid(value: Optional[UUID]) -> Optional[str]: return str(value) if value is not None else None
def _decimal(value: Optional[Decimal]) -> Optional[str]: return format(value, "f") if value is not None else None
def _date(value: date) -> str: return value.isoformat()
def _datetime(value: datetime) -> str: return value.isoformat()
def _enum(value: Optional[Enum]) -> Optional[str]: return value.value if value is not None else None
def _str(value: Optional[str]) -> Optional[str]: return value

def _parse_uuid(value: Optional[str]) -> Optional[UUID]: return UUID(value) if value is not None else None
def _parse_decimal(value: Optional[str]) -> Optional[Decimal]: return Decimal(value) if value is not None else None

def _parse_enum(enum_type, value): return enum_type(value) if value is not None else None


class DuplicateContractSalaryControlSnapshotError(ValueError):
    """Snapshot strictement identique déjà présent."""


class SqliteContractSalaryControlSnapshotRepository:
    """Repository SQLite atomique des snapshots salariaux CCNS."""

    def __init__(self, path: str | Path = "ccns_salary_control_snapshots.sqlite") -> None:
        self.path = str(path)
        self.ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.path)

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tw_contract_salary_control_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    reference_date TEXT NOT NULL,
                    executed_at TEXT NOT NULL,
                    total_contracts INTEGER NOT NULL,
                    compliant_contracts INTEGER NOT NULL,
                    non_compliant_contracts INTEGER NOT NULL,
                    not_evaluated_contracts INTEGER NOT NULL,
                    total_shortfall_amount TEXT NOT NULL,
                    created_by TEXT,
                    schema_version INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tw_contract_salary_control_snapshot_rows (
                    snapshot_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    contract_id TEXT NOT NULL,
                    employee_id TEXT,
                    status TEXT NOT NULL,
                    remuneration_amount TEXT,
                    applicable_minimum_amount TEXT,
                    shortfall_amount TEXT NOT NULL,
                    classification_code TEXT,
                    minimum_source TEXT,
                    territory TEXT,
                    failure_reason TEXT,
                    failure_message TEXT,
                    issue_code TEXT,
                    issue_message TEXT,
                    PRIMARY KEY (snapshot_id, position),
                    FOREIGN KEY (snapshot_id) REFERENCES tw_contract_salary_control_snapshots(snapshot_id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tw_salary_snapshots_reference_date ON tw_contract_salary_control_snapshots(reference_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tw_salary_snapshots_executed_at ON tw_contract_salary_control_snapshots(executed_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tw_salary_snapshot_rows_contract_id ON tw_contract_salary_control_snapshot_rows(contract_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tw_salary_snapshot_rows_employee_id ON tw_contract_salary_control_snapshot_rows(employee_id)")

    def save(self, snapshot: ContractSalaryControlSnapshot) -> ContractSalaryControlSnapshot:
        if self._find_duplicate(snapshot) is not None:
            raise DuplicateContractSalaryControlSnapshotError("Un snapshot salarial strictement identique existe déjà.")
        try:
            with self._connect() as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("BEGIN")
                conn.execute("""
                    INSERT INTO tw_contract_salary_control_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(snapshot.snapshot_id), _date(snapshot.reference_date), _datetime(snapshot.executed_at), snapshot.total_contracts, snapshot.compliant_contracts, snapshot.non_compliant_contracts, snapshot.not_evaluated_contracts, _decimal(snapshot.total_shortfall_amount), snapshot.created_by, snapshot.schema_version))
                for pos, row in enumerate(snapshot.rows):
                    conn.execute("""
                        INSERT INTO tw_contract_salary_control_snapshot_rows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(snapshot.snapshot_id), pos, str(row.contract_id), _uuid(row.employee_id), _enum(row.status), _decimal(row.remuneration_amount), _decimal(row.applicable_minimum_amount), _decimal(row.shortfall_amount), row.classification_code, _enum(row.minimum_source), _enum(row.territory), _enum(row.failure_reason), row.failure_message, row.issue_code, row.issue_message))
        except Exception:
            raise
        return snapshot

    def get(self, snapshot_id: UUID) -> Optional[ContractSalaryControlSnapshot]:
        with self._connect() as conn:
            header = conn.execute("SELECT * FROM tw_contract_salary_control_snapshots WHERE snapshot_id=?", (str(snapshot_id),)).fetchone()
            if header is None: return None
            rows = conn.execute("SELECT * FROM tw_contract_salary_control_snapshot_rows WHERE snapshot_id=? ORDER BY position", (str(snapshot_id),)).fetchall()
        return self._snapshot(header, rows)

    def list_all(self) -> tuple[ContractSalaryControlSnapshot, ...]:
        with self._connect() as conn:
            ids = [UUID(row[0]) for row in conn.execute("SELECT snapshot_id FROM tw_contract_salary_control_snapshots ORDER BY executed_at, snapshot_id").fetchall()]
        return tuple(s for s in (self.get(i) for i in ids) if s is not None)

    def list_by_reference_date(self, reference_date: date) -> tuple[ContractSalaryControlSnapshot, ...]:
        with self._connect() as conn:
            ids = [UUID(row[0]) for row in conn.execute("SELECT snapshot_id FROM tw_contract_salary_control_snapshots WHERE reference_date=? ORDER BY executed_at, snapshot_id", (reference_date.isoformat(),)).fetchall()]
        return tuple(s for s in (self.get(i) for i in ids) if s is not None)

    def _snapshot(self, h, rows):
        return ContractSalaryControlSnapshot(UUID(h[0]), date.fromisoformat(h[1]), datetime.fromisoformat(h[2]), h[3], h[4], h[5], h[6], Decimal(h[7]), tuple(self._row(r) for r in rows), h[8], h[9])

    def _row(self, r):
        return ContractSalaryControlSnapshotRow(UUID(r[2]), _parse_uuid(r[3]), ContractSalaryControlStatus(r[4]), _parse_decimal(r[5]), _parse_decimal(r[6]), Decimal(r[7]), r[8], _parse_enum(ApplicableSalaryMinimumSource, r[9]), _parse_enum(SmicTerritory, r[10]), _parse_enum(ContractSalaryEvaluationFailureReason, r[11]), r[12], r[13], r[14])

    def _find_duplicate(self, snapshot):
        for existing in self.list_by_reference_date(snapshot.reference_date):
            if existing.duplicate_key() == snapshot.duplicate_key():
                return existing
        return None
