from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from domain.hr_connections import (
    ConnectionProfile,
    ConnectorCapability,
    EffectivePeriod,
    ExchangeStatus,
    ExpectedDocument,
    HrAuditEvent,
    HrAuditField,
    HrCase,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrEventKind,
    HrEventTargetKind,
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)


SCHEMA_VERSION = 1


class DuplicateHrAuditEventError(ValueError):
    """Un événement append-only avec le même identifiant existe déjà."""


class SqliteHrConnectionsRepository:
    """Persistance additive isolée des fondations Connexions RH.

    Ce repository est volontairement séparé des bases historiques de Teamworks. Il
    persiste uniquement les données non secrètes déjà définies par CRH-01 à CRH-08 :
    profils d'organismes, dossiers RH et journal d'audit. Aucun credential, token,
    mot de passe, cookie ou contenu médical n'a de colonne dans ce schéma.

    Les identifiants de salarié/structure restent des références métier textuelles :
    aucune clé étrangère n'est créée vers les tables historiques.
    """

    def __init__(self, path: str | Path = "hr_connections.sqlite") -> None:
        self.path = str(path)
        self.ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        path = Path(self.path)
        if self.path != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tw_hr_connections_schema (
                    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                    schema_version INTEGER NOT NULL
                );

                INSERT OR IGNORE INTO tw_hr_connections_schema(singleton_id, schema_version)
                VALUES (1, 1);

                CREATE TABLE IF NOT EXISTS tw_hr_connection_profiles (
                    structure_ref TEXT NOT NULL,
                    organization_code TEXT NOT NULL,
                    organization_label TEXT NOT NULL,
                    organization_kind TEXT NOT NULL,
                    effective_start TEXT,
                    effective_end TEXT,
                    PRIMARY KEY (structure_ref, organization_code)
                );

                CREATE TABLE IF NOT EXISTS tw_hr_connection_capabilities (
                    structure_ref TEXT NOT NULL,
                    organization_code TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    PRIMARY KEY (structure_ref, organization_code, capability),
                    FOREIGN KEY (structure_ref, organization_code)
                        REFERENCES tw_hr_connection_profiles(structure_ref, organization_code)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tw_hr_organization_references (
                    structure_ref TEXT NOT NULL,
                    organization_code TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    reference_type TEXT NOT NULL,
                    reference_value TEXT NOT NULL,
                    reference_label TEXT,
                    PRIMARY KEY (structure_ref, organization_code, position),
                    FOREIGN KEY (structure_ref, organization_code)
                        REFERENCES tw_hr_connection_profiles(structure_ref, organization_code)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tw_hr_portal_links (
                    structure_ref TEXT NOT NULL,
                    organization_code TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    label TEXT NOT NULL,
                    PRIMARY KEY (structure_ref, organization_code, position),
                    FOREIGN KEY (structure_ref, organization_code)
                        REFERENCES tw_hr_connection_profiles(structure_ref, organization_code)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tw_hr_cases (
                    structure_ref TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    case_type_code TEXT NOT NULL,
                    case_type_label TEXT NOT NULL,
                    subject_kind TEXT NOT NULL,
                    subject_identifier TEXT NOT NULL,
                    organization_code TEXT NOT NULL,
                    opened_on TEXT NOT NULL,
                    due_on TEXT,
                    status TEXT NOT NULL,
                    exchange_status TEXT NOT NULL,
                    source TEXT,
                    result TEXT,
                    comment TEXT,
                    PRIMARY KEY (structure_ref, case_id)
                );

                CREATE TABLE IF NOT EXISTS tw_hr_case_expected_documents (
                    structure_ref TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    document_code TEXT NOT NULL,
                    document_label TEXT NOT NULL,
                    required INTEGER NOT NULL CHECK (required IN (0, 1)),
                    PRIMARY KEY (structure_ref, case_id, document_code),
                    FOREIGN KEY (structure_ref, case_id)
                        REFERENCES tw_hr_cases(structure_ref, case_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tw_hr_audit_events (
                    structure_ref TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    event_kind TEXT NOT NULL,
                    target_kind TEXT NOT NULL,
                    target_ref TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    actor_ref TEXT,
                    source TEXT,
                    PRIMARY KEY (structure_ref, event_id)
                );

                CREATE TABLE IF NOT EXISTS tw_hr_audit_fields (
                    structure_ref TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    field_key TEXT NOT NULL,
                    field_value TEXT NOT NULL,
                    PRIMARY KEY (structure_ref, event_id, position),
                    UNIQUE (structure_ref, event_id, field_key),
                    FOREIGN KEY (structure_ref, event_id)
                        REFERENCES tw_hr_audit_events(structure_ref, event_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_tw_hr_profiles_kind
                    ON tw_hr_connection_profiles(structure_ref, organization_kind);
                CREATE INDEX IF NOT EXISTS idx_tw_hr_cases_status
                    ON tw_hr_cases(structure_ref, status, due_on);
                CREATE INDEX IF NOT EXISTS idx_tw_hr_cases_subject
                    ON tw_hr_cases(structure_ref, subject_kind, subject_identifier);
                CREATE INDEX IF NOT EXISTS idx_tw_hr_events_target
                    ON tw_hr_audit_events(structure_ref, target_kind, target_ref, occurred_at);
                """
            )
            version = conn.execute(
                "SELECT schema_version FROM tw_hr_connections_schema WHERE singleton_id = 1"
            ).fetchone()[0]
            if version != SCHEMA_VERSION:
                raise RuntimeError(
                    f"Version de schéma Connexions RH non prise en charge : {version}."
                )

    def schema_version(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT schema_version FROM tw_hr_connections_schema WHERE singleton_id = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("Le schéma Connexions RH n'est pas initialisé.")
        return int(row[0])

    # -- Profils d'organismes -------------------------------------------------

    def save_profile(self, profile: ConnectionProfile) -> ConnectionProfile:
        if not isinstance(profile, ConnectionProfile):
            raise TypeError("Le profil de connexion à persister est invalide.")

        period = profile.effective_period
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tw_hr_connection_profiles(
                    structure_ref, organization_code, organization_label,
                    organization_kind, effective_start, effective_end
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(structure_ref, organization_code) DO UPDATE SET
                    organization_label = excluded.organization_label,
                    organization_kind = excluded.organization_kind,
                    effective_start = excluded.effective_start,
                    effective_end = excluded.effective_end
                """,
                (
                    profile.structure_ref,
                    profile.organization.code,
                    profile.organization.label,
                    profile.organization.kind.value,
                    period.starts_on.isoformat() if period and period.starts_on else None,
                    period.ends_on.isoformat() if period and period.ends_on else None,
                ),
            )
            key = (profile.structure_ref, profile.organization.code)
            conn.execute(
                "DELETE FROM tw_hr_connection_capabilities WHERE structure_ref=? AND organization_code=?",
                key,
            )
            conn.execute(
                "DELETE FROM tw_hr_organization_references WHERE structure_ref=? AND organization_code=?",
                key,
            )
            conn.execute(
                "DELETE FROM tw_hr_portal_links WHERE structure_ref=? AND organization_code=?",
                key,
            )
            conn.executemany(
                "INSERT INTO tw_hr_connection_capabilities VALUES (?, ?, ?)",
                [
                    (profile.structure_ref, profile.organization.code, capability.value)
                    for capability in sorted(profile.capabilities, key=lambda item: item.value)
                ],
            )
            conn.executemany(
                "INSERT INTO tw_hr_organization_references VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        profile.structure_ref,
                        profile.organization.code,
                        position,
                        reference.reference_type,
                        reference.value,
                        reference.label,
                    )
                    for position, reference in enumerate(profile.references)
                ],
            )
            conn.executemany(
                "INSERT INTO tw_hr_portal_links VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        profile.structure_ref,
                        profile.organization.code,
                        position,
                        link.url,
                        link.label,
                    )
                    for position, link in enumerate(profile.portal_links)
                ],
            )
        return profile

    def get_profile(
        self,
        *,
        structure_ref: str,
        organization_code: str,
    ) -> ConnectionProfile | None:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        organization_code = _required_text(
            organization_code, "Le code de l'organisme est obligatoire."
        )
        with self._connect() as conn:
            header = conn.execute(
                """
                SELECT * FROM tw_hr_connection_profiles
                WHERE structure_ref=? AND organization_code=?
                """,
                (structure_ref, organization_code),
            ).fetchone()
            if header is None:
                return None
            capabilities = conn.execute(
                """
                SELECT capability FROM tw_hr_connection_capabilities
                WHERE structure_ref=? AND organization_code=? ORDER BY capability
                """,
                (structure_ref, organization_code),
            ).fetchall()
            references = conn.execute(
                """
                SELECT reference_type, reference_value, reference_label
                FROM tw_hr_organization_references
                WHERE structure_ref=? AND organization_code=? ORDER BY position
                """,
                (structure_ref, organization_code),
            ).fetchall()
            links = conn.execute(
                """
                SELECT url, label FROM tw_hr_portal_links
                WHERE structure_ref=? AND organization_code=? ORDER BY position
                """,
                (structure_ref, organization_code),
            ).fetchall()
        return _profile_from_rows(header, capabilities, references, links)

    def list_profiles(self, *, structure_ref: str) -> tuple[ConnectionProfile, ...]:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        with self._connect() as conn:
            codes = [
                row[0]
                for row in conn.execute(
                    """
                    SELECT organization_code FROM tw_hr_connection_profiles
                    WHERE structure_ref=? ORDER BY organization_code
                    """,
                    (structure_ref,),
                ).fetchall()
            ]
        return tuple(
            profile
            for profile in (
                self.get_profile(structure_ref=structure_ref, organization_code=code)
                for code in codes
            )
            if profile is not None
        )

    # -- Dossiers RH ----------------------------------------------------------

    def save_case(self, *, structure_ref: str, case: HrCase) -> HrCase:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        if not isinstance(case, HrCase):
            raise TypeError("Le dossier RH à persister est invalide.")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tw_hr_cases(
                    structure_ref, case_id, case_type_code, case_type_label,
                    subject_kind, subject_identifier, organization_code,
                    opened_on, due_on, status, exchange_status, source, result, comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(structure_ref, case_id) DO UPDATE SET
                    case_type_code=excluded.case_type_code,
                    case_type_label=excluded.case_type_label,
                    subject_kind=excluded.subject_kind,
                    subject_identifier=excluded.subject_identifier,
                    organization_code=excluded.organization_code,
                    opened_on=excluded.opened_on,
                    due_on=excluded.due_on,
                    status=excluded.status,
                    exchange_status=excluded.exchange_status,
                    source=excluded.source,
                    result=excluded.result,
                    comment=excluded.comment
                """,
                (
                    structure_ref,
                    case.case_id,
                    case.case_type.code,
                    case.case_type.label,
                    case.subject.kind.value,
                    case.subject.identifier,
                    case.organization_code,
                    case.opened_on.isoformat(),
                    case.due_on.isoformat() if case.due_on else None,
                    case.status.value,
                    case.exchange_status.value,
                    case.source,
                    case.result,
                    case.comment,
                ),
            )
            conn.execute(
                "DELETE FROM tw_hr_case_expected_documents WHERE structure_ref=? AND case_id=?",
                (structure_ref, case.case_id),
            )
            conn.executemany(
                "INSERT INTO tw_hr_case_expected_documents VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        structure_ref,
                        case.case_id,
                        document.code,
                        document.label,
                        1 if document.required else 0,
                    )
                    for document in sorted(case.expected_documents, key=lambda item: item.code)
                ],
            )
        return case

    def get_case(self, *, structure_ref: str, case_id: str) -> HrCase | None:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        case_id = _required_text(case_id, "L'identifiant du dossier RH est obligatoire.")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tw_hr_cases WHERE structure_ref=? AND case_id=?",
                (structure_ref, case_id),
            ).fetchone()
            if row is None:
                return None
            documents = conn.execute(
                """
                SELECT document_code, document_label, required
                FROM tw_hr_case_expected_documents
                WHERE structure_ref=? AND case_id=? ORDER BY document_code
                """,
                (structure_ref, case_id),
            ).fetchall()
        return _case_from_rows(row, documents)

    def list_cases(self, *, structure_ref: str) -> tuple[HrCase, ...]:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        with self._connect() as conn:
            ids = [
                row[0]
                for row in conn.execute(
                    """
                    SELECT case_id FROM tw_hr_cases
                    WHERE structure_ref=? ORDER BY opened_on, case_id
                    """,
                    (structure_ref,),
                ).fetchall()
            ]
        return tuple(
            case
            for case in (
                self.get_case(structure_ref=structure_ref, case_id=case_id) for case_id in ids
            )
            if case is not None
        )

    # -- Journal append-only --------------------------------------------------

    def append_event(self, *, structure_ref: str, event: HrAuditEvent) -> HrAuditEvent:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        if not isinstance(event, HrAuditEvent):
            raise TypeError("L'événement RH à persister est invalide.")
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO tw_hr_audit_events(
                        structure_ref, event_id, event_kind, target_kind, target_ref,
                        occurred_at, actor_ref, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        structure_ref,
                        event.event_id,
                        event.kind.value,
                        event.target_kind.value,
                        event.target_ref,
                        event.occurred_at.isoformat(),
                        event.actor_ref,
                        event.source,
                    ),
                )
                conn.executemany(
                    "INSERT INTO tw_hr_audit_fields VALUES (?, ?, ?, ?, ?)",
                    [
                        (structure_ref, event.event_id, position, field.key, field.value)
                        for position, field in enumerate(event.fields)
                    ],
                )
        except sqlite3.IntegrityError as exc:
            if self.get_event(structure_ref=structure_ref, event_id=event.event_id) is not None:
                raise DuplicateHrAuditEventError(
                    f"L'événement RH '{event.event_id}' est déjà persisté."
                ) from exc
            raise
        return event

    def get_event(self, *, structure_ref: str, event_id: str) -> HrAuditEvent | None:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        event_id = _required_text(event_id, "L'identifiant de l'événement RH est obligatoire.")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tw_hr_audit_events WHERE structure_ref=? AND event_id=?",
                (structure_ref, event_id),
            ).fetchone()
            if row is None:
                return None
            fields = conn.execute(
                """
                SELECT field_key, field_value FROM tw_hr_audit_fields
                WHERE structure_ref=? AND event_id=? ORDER BY position
                """,
                (structure_ref, event_id),
            ).fetchall()
        return _event_from_rows(row, fields)

    def list_events(
        self,
        *,
        structure_ref: str,
        target_kind: HrEventTargetKind | None = None,
        target_ref: str | None = None,
    ) -> tuple[HrAuditEvent, ...]:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        if target_kind is not None and not isinstance(target_kind, HrEventTargetKind):
            raise TypeError("La nature de la cible d'audit est invalide.")
        if target_ref is not None:
            target_ref = _required_text(target_ref, "La référence de la cible d'audit est obligatoire.")

        clauses = ["structure_ref=?"]
        params: list[str] = [structure_ref]
        if target_kind is not None:
            clauses.append("target_kind=?")
            params.append(target_kind.value)
        if target_ref is not None:
            clauses.append("target_ref=?")
            params.append(target_ref)
        query = (
            "SELECT event_id FROM tw_hr_audit_events WHERE "
            + " AND ".join(clauses)
            + " ORDER BY occurred_at, event_id"
        )
        with self._connect() as conn:
            ids = [row[0] for row in conn.execute(query, tuple(params)).fetchall()]
        return tuple(
            event
            for event in (
                self.get_event(structure_ref=structure_ref, event_id=event_id)
                for event_id in ids
            )
            if event is not None
        )


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


def _profile_from_rows(header, capabilities, references, links) -> ConnectionProfile:
    start = date.fromisoformat(header["effective_start"]) if header["effective_start"] else None
    end = date.fromisoformat(header["effective_end"]) if header["effective_end"] else None
    period = EffectivePeriod(starts_on=start, ends_on=end) if start or end else None
    return ConnectionProfile.create(
        structure_ref=header["structure_ref"],
        organization=HrOrganization.create(
            code=header["organization_code"],
            label=header["organization_label"],
            kind=OrganizationKind(header["organization_kind"]),
        ),
        capabilities=[ConnectorCapability(row["capability"]) for row in capabilities],
        references=[
            OrganizationReference.create(
                reference_type=row["reference_type"],
                value=row["reference_value"],
                label=row["reference_label"],
            )
            for row in references
        ],
        portal_links=[PortalLink.create(url=row["url"], label=row["label"]) for row in links],
        effective_period=period,
    )


def _case_from_rows(row, documents) -> HrCase:
    return HrCase(
        case_id=row["case_id"],
        case_type=HrCaseType.create(code=row["case_type_code"], label=row["case_type_label"]),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind(row["subject_kind"]),
            identifier=row["subject_identifier"],
        ),
        organization_code=row["organization_code"],
        opened_on=date.fromisoformat(row["opened_on"]),
        due_on=date.fromisoformat(row["due_on"]) if row["due_on"] else None,
        status=HrCaseStatus(row["status"]),
        exchange_status=ExchangeStatus(row["exchange_status"]),
        expected_documents=frozenset(
            ExpectedDocument.create(
                code=document["document_code"],
                label=document["document_label"],
                required=bool(document["required"]),
            )
            for document in documents
        ),
        source=row["source"],
        result=row["result"],
        comment=row["comment"],
    )


def _event_from_rows(row, fields) -> HrAuditEvent:
    return HrAuditEvent.create(
        event_id=row["event_id"],
        kind=HrEventKind(row["event_kind"]),
        target_kind=HrEventTargetKind(row["target_kind"]),
        target_ref=row["target_ref"],
        occurred_at=datetime.fromisoformat(row["occurred_at"]),
        actor_ref=row["actor_ref"],
        source=row["source"],
        fields=[
            HrAuditField.create(key=field["field_key"], value=field["field_value"])
            for field in fields
        ],
    )
