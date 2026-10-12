from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from domain.hr_connections import (
    EffectivePeriod,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    OrganizationKind,
)


EMPLOYEE_PROTECTION_SCHEMA_VERSION = 1


class SqliteEmployeeProtectionRepository:
    """Adaptateur de référence isolé pour les suivis de protection sociale salarié.

    Ce store reste séparé des bases historiques de Teamworks et du store CRH-09.
    L'objectif est de qualifier le contrat de persistance du sous-domaine salarié
    avant un raccordement ultérieur à l'adaptateur de production. Les références de
    structure, salarié, organisme et justificatif sont donc textuelles et ne créent
    volontairement aucune clé étrangère vers les tables historiques ni vers les
    profils d'organismes : un historique salarié doit rester lisible même si un
    ancien profil d'organisme est retiré.
    """

    def __init__(self, path: str | Path = "hr_employee_protection.sqlite") -> None:
        self.path = str(path)
        self.ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        path = Path(self.path)
        if self.path != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tw_hr_employee_protection_schema (
                    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                    schema_version INTEGER NOT NULL
                );

                INSERT OR IGNORE INTO tw_hr_employee_protection_schema(
                    singleton_id, schema_version
                ) VALUES (1, 1);

                CREATE TABLE IF NOT EXISTS tw_hr_employee_protection (
                    structure_ref TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    employee_ref TEXT NOT NULL,
                    organization_code TEXT NOT NULL,
                    organization_kind TEXT NOT NULL,
                    relation_kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    effective_start TEXT,
                    effective_end TEXT,
                    scheme_code TEXT,
                    option_code TEXT,
                    contribution_profile_code TEXT,
                    waiver_reason_code TEXT,
                    external_reference TEXT,
                    document_ref TEXT,
                    administrative_deadline TEXT,
                    source TEXT,
                    PRIMARY KEY (structure_ref, record_id)
                );

                CREATE INDEX IF NOT EXISTS idx_tw_hr_employee_protection_employee
                    ON tw_hr_employee_protection(structure_ref, employee_ref, effective_start);
                CREATE INDEX IF NOT EXISTS idx_tw_hr_employee_protection_organization
                    ON tw_hr_employee_protection(structure_ref, organization_code);
                CREATE INDEX IF NOT EXISTS idx_tw_hr_employee_protection_deadline
                    ON tw_hr_employee_protection(
                        structure_ref, employee_ref, administrative_deadline, status
                    );
                """
            )
            version = conn.execute(
                """
                SELECT schema_version
                FROM tw_hr_employee_protection_schema
                WHERE singleton_id = 1
                """
            ).fetchone()[0]
            if version != EMPLOYEE_PROTECTION_SCHEMA_VERSION:
                raise RuntimeError(
                    "Version de schéma du suivi de protection sociale salarié "
                    f"non prise en charge : {version}."
                )

    def schema_version(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT schema_version
                FROM tw_hr_employee_protection_schema
                WHERE singleton_id = 1
                """
            ).fetchone()
        if row is None:
            raise RuntimeError(
                "Le schéma du suivi de protection sociale salarié n'est pas initialisé."
            )
        return int(row[0])

    def save_employee_protection(
        self,
        record: EmployeeProtectionRecord,
    ) -> EmployeeProtectionRecord:
        if not isinstance(record, EmployeeProtectionRecord):
            raise TypeError("Le suivi de protection sociale à persister est invalide.")

        period = record.effective_period
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tw_hr_employee_protection(
                    structure_ref,
                    record_id,
                    employee_ref,
                    organization_code,
                    organization_kind,
                    relation_kind,
                    status,
                    effective_start,
                    effective_end,
                    scheme_code,
                    option_code,
                    contribution_profile_code,
                    waiver_reason_code,
                    external_reference,
                    document_ref,
                    administrative_deadline,
                    source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(structure_ref, record_id) DO UPDATE SET
                    employee_ref = excluded.employee_ref,
                    organization_code = excluded.organization_code,
                    organization_kind = excluded.organization_kind,
                    relation_kind = excluded.relation_kind,
                    status = excluded.status,
                    effective_start = excluded.effective_start,
                    effective_end = excluded.effective_end,
                    scheme_code = excluded.scheme_code,
                    option_code = excluded.option_code,
                    contribution_profile_code = excluded.contribution_profile_code,
                    waiver_reason_code = excluded.waiver_reason_code,
                    external_reference = excluded.external_reference,
                    document_ref = excluded.document_ref,
                    administrative_deadline = excluded.administrative_deadline,
                    source = excluded.source
                """,
                (
                    record.structure_ref,
                    record.record_id,
                    record.employee_ref,
                    record.organization_code,
                    record.organization_kind.value,
                    record.relation_kind.value,
                    record.status.value,
                    period.starts_on.isoformat() if period.starts_on else None,
                    period.ends_on.isoformat() if period.ends_on else None,
                    record.scheme_code,
                    record.option_code,
                    record.contribution_profile_code,
                    record.waiver_reason_code,
                    record.external_reference,
                    record.document_ref,
                    record.administrative_deadline.isoformat()
                    if record.administrative_deadline
                    else None,
                    record.source,
                ),
            )
        return record

    def get_employee_protection(
        self,
        *,
        structure_ref: str,
        record_id: str,
    ) -> EmployeeProtectionRecord | None:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        record_id = _required_text(
            record_id,
            "L'identifiant du suivi de protection sociale est obligatoire.",
        )
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM tw_hr_employee_protection
                WHERE structure_ref = ? AND record_id = ?
                """,
                (structure_ref, record_id),
            ).fetchone()
        return _record_from_row(row) if row is not None else None

    def list_employee_protection(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
    ) -> tuple[EmployeeProtectionRecord, ...]:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        employee_ref = _required_text(
            employee_ref,
            "La référence du salarié est obligatoire.",
        )
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM tw_hr_employee_protection
                WHERE structure_ref = ? AND employee_ref = ?
                ORDER BY
                    CASE WHEN effective_start IS NULL THEN 1 ELSE 0 END,
                    effective_start,
                    record_id
                """,
                (structure_ref, employee_ref),
            ).fetchall()
        return tuple(_record_from_row(row) for row in rows)


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _record_from_row(row: sqlite3.Row) -> EmployeeProtectionRecord:
    return EmployeeProtectionRecord.create(
        record_id=row["record_id"],
        structure_ref=row["structure_ref"],
        employee_ref=row["employee_ref"],
        organization_code=row["organization_code"],
        organization_kind=OrganizationKind(row["organization_kind"]),
        relation_kind=EmployeeProtectionRelationKind(row["relation_kind"]),
        status=EmployeeProtectionStatus(row["status"]),
        effective_period=EffectivePeriod(
            starts_on=_optional_date(row["effective_start"]),
            ends_on=_optional_date(row["effective_end"]),
        ),
        scheme_code=row["scheme_code"],
        option_code=row["option_code"],
        contribution_profile_code=row["contribution_profile_code"],
        waiver_reason_code=row["waiver_reason_code"],
        external_reference=row["external_reference"],
        document_ref=row["document_ref"],
        administrative_deadline=_optional_date(row["administrative_deadline"]),
        source=row["source"],
    )
