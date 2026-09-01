from __future__ import annotations

from datetime import date, datetime
from typing import Callable

from domain.hr_connections import (
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
)


TEAMWORKS_HR_CASES_SCHEMA_VERSION = 1
_SCHEMA_COMPONENT = "hr_cases_runtime"

_CASE_COLUMNS = (
    "structure_ref",
    "case_id",
    "case_type_code",
    "case_type_label",
    "subject_kind",
    "subject_identifier",
    "organization_code",
    "opened_on",
    "due_on",
    "status",
    "exchange_status",
    "source",
    "result",
    "comment",
)

_EVENT_COLUMNS = (
    "structure_ref",
    "event_id",
    "event_kind",
    "target_kind",
    "target_ref",
    "occurred_at",
    "actor_ref",
    "source",
)

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS tw_hr_schema_versions (
        component VARCHAR(50) NOT NULL PRIMARY KEY,
        schema_version INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_cases (
        structure_ref VARCHAR(80) NOT NULL,
        case_id VARCHAR(100) NOT NULL,
        case_type_code VARCHAR(100) NOT NULL,
        case_type_label VARCHAR(200) NOT NULL,
        subject_kind VARCHAR(30) NOT NULL,
        subject_identifier VARCHAR(100) NOT NULL,
        organization_code VARCHAR(80) NOT NULL,
        opened_on VARCHAR(10) NOT NULL,
        due_on VARCHAR(10),
        status VARCHAR(30) NOT NULL,
        exchange_status VARCHAR(30) NOT NULL,
        source VARCHAR(120),
        result TEXT,
        comment TEXT,
        PRIMARY KEY (structure_ref, case_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_case_expected_documents (
        structure_ref VARCHAR(80) NOT NULL,
        case_id VARCHAR(100) NOT NULL,
        document_code VARCHAR(100) NOT NULL,
        document_label VARCHAR(200) NOT NULL,
        required INTEGER NOT NULL,
        PRIMARY KEY (structure_ref, case_id, document_code)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_audit_events (
        structure_ref VARCHAR(80) NOT NULL,
        event_id VARCHAR(100) NOT NULL,
        event_kind VARCHAR(60) NOT NULL,
        target_kind VARCHAR(40) NOT NULL,
        target_ref VARCHAR(120) NOT NULL,
        occurred_at VARCHAR(40) NOT NULL,
        actor_ref VARCHAR(120),
        source VARCHAR(120),
        PRIMARY KEY (structure_ref, event_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_audit_fields (
        structure_ref VARCHAR(80) NOT NULL,
        event_id VARCHAR(100) NOT NULL,
        position INTEGER NOT NULL,
        field_key VARCHAR(120) NOT NULL,
        field_value VARCHAR(500) NOT NULL,
        PRIMARY KEY (structure_ref, event_id, position)
    )
    """,
)

_INDEXES = (
    ("tw_hr_cases", "idx_tw_hr_cases_status", "structure_ref, status, due_on"),
    (
        "tw_hr_cases",
        "idx_tw_hr_cases_subject",
        "structure_ref, subject_kind, subject_identifier",
    ),
    (
        "tw_hr_cases",
        "idx_tw_hr_cases_organization",
        "structure_ref, organization_code, status, due_on",
    ),
    (
        "tw_hr_audit_events",
        "idx_tw_hr_events_target",
        "structure_ref, target_kind, target_ref, occurred_at",
    ),
)


class DuplicateTeamworksHrAuditEventError(ValueError):
    """Un événement append-only avec le même identifiant est déjà persisté."""


class TeamworksHrCasesRepository:
    """Persistance de production des démarches et événements Connexions RH.

    L'adaptateur utilise ``GestionDB.DB`` et reste compatible avec les bases locales
    SQLite et réseau MySQL de Teamworks. Le schéma est additif et possède son propre
    composant de version. Il ne crée aucune clé étrangère vers les tables historiques
    salariés, contrats ou structure.

    Les événements d'audit sont append-only : aucune méthode de modification ou de
    suppression n'est exposée.
    """

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        ensure_schema: bool = True,
    ) -> None:
        self._db_factory = db_factory or self._default_db_factory
        if ensure_schema:
            self.ensure_schema()

    @staticmethod
    def _default_db_factory():
        import GestionDB

        return GestionDB.DB()

    def ensure_schema(self) -> None:
        db = self._db_factory()
        try:
            for statement in _SCHEMA_STATEMENTS:
                _execute(db, statement)

            row = _fetchone(
                db,
                """
                SELECT schema_version
                FROM tw_hr_schema_versions
                WHERE component = ?
                """,
                (_SCHEMA_COMPONENT,),
            )
            if row is None:
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_schema_versions(component, schema_version)
                    VALUES (?, ?)
                    """,
                    (_SCHEMA_COMPONENT, TEAMWORKS_HR_CASES_SCHEMA_VERSION),
                )
            elif int(row[0]) != TEAMWORKS_HR_CASES_SCHEMA_VERSION:
                raise RuntimeError(
                    "Version de schéma des démarches RH Teamworks non prise en charge : "
                    f"{row[0]}."
                )

            for table, index_name, columns in _INDEXES:
                if not _index_exists(db, table=table, index_name=index_name):
                    _execute(db, f"CREATE INDEX {index_name} ON {table}({columns})")
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)

    def schema_version(self) -> int:
        db = self._db_factory()
        try:
            row = _fetchone(
                db,
                """
                SELECT schema_version
                FROM tw_hr_schema_versions
                WHERE component = ?
                """,
                (_SCHEMA_COMPONENT,),
            )
        finally:
            _close(db)
        if row is None:
            raise RuntimeError("Le schéma des démarches RH Teamworks n'est pas initialisé.")
        return int(row[0])

    # -- Dossiers RH ------------------------------------------------------

    def save_case(self, *, structure_ref: str, case: HrCase) -> HrCase:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(case, HrCase):
            raise TypeError("Le dossier RH à persister est invalide.")

        key = (structure_ref, case.case_id)
        values = _case_values(structure_ref=structure_ref, case=case)
        db = self._db_factory()
        try:
            exists = _fetchone(
                db,
                "SELECT 1 FROM tw_hr_cases WHERE structure_ref = ? AND case_id = ?",
                key,
            )
            if exists is None:
                placeholders = ", ".join("?" for _ in _CASE_COLUMNS)
                _execute(
                    db,
                    "INSERT INTO tw_hr_cases("
                    + ", ".join(_CASE_COLUMNS)
                    + f") VALUES ({placeholders})",
                    values,
                )
            else:
                update_columns = _CASE_COLUMNS[2:]
                assignments = ", ".join(f"{column} = ?" for column in update_columns)
                _execute(
                    db,
                    f"UPDATE tw_hr_cases SET {assignments} "
                    "WHERE structure_ref = ? AND case_id = ?",
                    values[2:] + key,
                )

            _execute(
                db,
                """
                DELETE FROM tw_hr_case_expected_documents
                WHERE structure_ref = ? AND case_id = ?
                """,
                key,
            )
            for document in sorted(case.expected_documents, key=lambda item: item.code):
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_case_expected_documents(
                        structure_ref, case_id, document_code, document_label, required
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    key
                    + (
                        document.code,
                        document.label,
                        1 if document.required else 0,
                    ),
                )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)
        return case

    def get_case(self, *, structure_ref: str, case_id: str) -> HrCase | None:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        case_id = _required_text(case_id, "L'identifiant du dossier RH est obligatoire.")
        db = self._db_factory()
        try:
            row = _fetchone(
                db,
                "SELECT " + ", ".join(_CASE_COLUMNS)
                + " FROM tw_hr_cases WHERE structure_ref = ? AND case_id = ?",
                (structure_ref, case_id),
            )
            if row is None:
                return None
            documents = _fetchall(
                db,
                """
                SELECT document_code, document_label, required
                FROM tw_hr_case_expected_documents
                WHERE structure_ref = ? AND case_id = ?
                ORDER BY document_code
                """,
                (structure_ref, case_id),
            )
        finally:
            _close(db)
        return _case_from_rows(row, documents)

    def list_cases(self, *, structure_ref: str) -> tuple[HrCase, ...]:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        db = self._db_factory()
        try:
            rows = _fetchall(
                db,
                "SELECT " + ", ".join(_CASE_COLUMNS)
                + " FROM tw_hr_cases WHERE structure_ref = ? "
                "ORDER BY opened_on, case_id",
                (structure_ref,),
            )
            document_rows = _fetchall(
                db,
                """
                SELECT case_id, document_code, document_label, required
                FROM tw_hr_case_expected_documents
                WHERE structure_ref = ?
                ORDER BY case_id, document_code
                """,
                (structure_ref,),
            )
        finally:
            _close(db)

        documents_by_case = {}
        for case_id, code, label, required in document_rows:
            documents_by_case.setdefault(case_id, []).append((code, label, required))
        return tuple(
            _case_from_rows(row, documents_by_case.get(row[1], ()))
            for row in rows
        )

    # -- Journal append-only --------------------------------------------

    def append_event(
        self,
        *,
        structure_ref: str,
        event: HrAuditEvent,
    ) -> HrAuditEvent:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(event, HrAuditEvent):
            raise TypeError("L'événement RH à persister est invalide.")

        db = self._db_factory()
        try:
            exists = _fetchone(
                db,
                """
                SELECT 1 FROM tw_hr_audit_events
                WHERE structure_ref = ? AND event_id = ?
                """,
                (structure_ref, event.event_id),
            )
            if exists is not None:
                raise DuplicateTeamworksHrAuditEventError(
                    f"L'événement RH '{event.event_id}' est déjà persisté."
                )

            _execute(
                db,
                "INSERT INTO tw_hr_audit_events("
                + ", ".join(_EVENT_COLUMNS)
                + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                _event_values(structure_ref=structure_ref, event=event),
            )
            for position, field in enumerate(event.fields):
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_audit_fields(
                        structure_ref, event_id, position, field_key, field_value
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (structure_ref, event.event_id, position, field.key, field.value),
                )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)
        return event

    def get_event(self, *, structure_ref: str, event_id: str) -> HrAuditEvent | None:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        event_id = _required_text(
            event_id,
            "L'identifiant de l'événement RH est obligatoire.",
        )
        db = self._db_factory()
        try:
            row = _fetchone(
                db,
                "SELECT " + ", ".join(_EVENT_COLUMNS)
                + " FROM tw_hr_audit_events WHERE structure_ref = ? AND event_id = ?",
                (structure_ref, event_id),
            )
            if row is None:
                return None
            fields = _fetchall(
                db,
                """
                SELECT field_key, field_value
                FROM tw_hr_audit_fields
                WHERE structure_ref = ? AND event_id = ?
                ORDER BY position
                """,
                (structure_ref, event_id),
            )
        finally:
            _close(db)
        return _event_from_rows(row, fields)

    def list_events(
        self,
        *,
        structure_ref: str,
        target_kind: HrEventTargetKind | None = None,
        target_ref: str | None = None,
    ) -> tuple[HrAuditEvent, ...]:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if target_kind is not None and not isinstance(target_kind, HrEventTargetKind):
            raise TypeError("La nature de la cible d'audit est invalide.")
        if target_ref is not None:
            target_ref = _required_text(
                target_ref,
                "La référence de la cible d'audit est obligatoire.",
            )

        clauses = ["structure_ref = ?"]
        params = [structure_ref]
        if target_kind is not None:
            clauses.append("target_kind = ?")
            params.append(target_kind.value)
        if target_ref is not None:
            clauses.append("target_ref = ?")
            params.append(target_ref)

        db = self._db_factory()
        try:
            rows = _fetchall(
                db,
                "SELECT " + ", ".join(_EVENT_COLUMNS)
                + " FROM tw_hr_audit_events WHERE "
                + " AND ".join(clauses)
                + " ORDER BY occurred_at, event_id",
                tuple(params),
            )
            field_rows = _fetchall(
                db,
                """
                SELECT event_id, position, field_key, field_value
                FROM tw_hr_audit_fields
                WHERE structure_ref = ?
                ORDER BY event_id, position
                """,
                (structure_ref,),
            )
        finally:
            _close(db)

        fields_by_event = {}
        for event_id, _position, key, value in field_rows:
            fields_by_event.setdefault(event_id, []).append((key, value))
        return tuple(
            _event_from_rows(row, fields_by_event.get(row[1], ()))
            for row in rows
        )


def _adapt_placeholders(db, statement: str) -> str:
    if bool(getattr(db, "isNetwork", False)):
        return statement.replace("?", "%s")
    return statement.replace("%s", "?")


def _execute(db, statement: str, params: tuple = ()):
    sql = _adapt_placeholders(db, statement)
    db.cursor.execute(sql, tuple(params))
    return db.cursor


def _fetchone(db, statement: str, params: tuple = ()):
    return _execute(db, statement, params).fetchone()


def _fetchall(db, statement: str, params: tuple = ()):
    return _execute(db, statement, params).fetchall()


def _index_exists(db, *, table: str, index_name: str) -> bool:
    if bool(getattr(db, "isNetwork", False)):
        row = _fetchone(db, f"SHOW INDEX FROM {table} WHERE Key_name = ?", (index_name,))
    else:
        row = _fetchone(
            db,
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name = ?",
            (index_name,),
        )
    return row is not None


def _commit(db) -> None:
    commit = getattr(db, "Commit", None)
    if callable(commit):
        commit()
    else:
        db.connexion.commit()


def _rollback(db) -> None:
    try:
        db.connexion.rollback()
    except Exception:
        pass


def _close(db) -> None:
    close = getattr(db, "Close", None)
    if callable(close):
        close()
    else:
        try:
            db.connexion.close()
        except Exception:
            pass


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _case_values(*, structure_ref: str, case: HrCase) -> tuple:
    return (
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
    )


def _case_from_rows(row, documents) -> HrCase:
    return HrCase(
        case_id=row[1],
        case_type=HrCaseType.create(code=row[2], label=row[3]),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind(row[4]),
            identifier=row[5],
        ),
        organization_code=row[6],
        opened_on=date.fromisoformat(row[7]),
        due_on=_optional_date(row[8]),
        status=HrCaseStatus(row[9]),
        exchange_status=ExchangeStatus(row[10]),
        expected_documents=frozenset(
            ExpectedDocument.create(
                code=document[0],
                label=document[1],
                required=bool(document[2]),
            )
            for document in documents
        ),
        source=row[11],
        result=row[12],
        comment=row[13],
    )


def _event_values(*, structure_ref: str, event: HrAuditEvent) -> tuple:
    return (
        structure_ref,
        event.event_id,
        event.kind.value,
        event.target_kind.value,
        event.target_ref,
        event.occurred_at.isoformat(),
        event.actor_ref,
        event.source,
    )


def _event_from_rows(row, fields) -> HrAuditEvent:
    return HrAuditEvent.create(
        event_id=row[1],
        kind=HrEventKind(row[2]),
        target_kind=HrEventTargetKind(row[3]),
        target_ref=row[4],
        occurred_at=datetime.fromisoformat(row[5]),
        actor_ref=row[6],
        source=row[7],
        fields=(
            HrAuditField.create(key=field[0], value=field[1])
            for field in fields
        ),
    )
