from __future__ import annotations

from datetime import date
from hashlib import sha256
from typing import Callable

from domain.hr_connections import (
    HrAuditEvent,
    HrCaseDocumentReceipt,
    HrCaseDocumentState,
    HrCaseStatus,
    HrEventKind,
    HrEventTargetKind,
)

from .teamworks_hr_cases_repository import TeamworksHrCasesRepository
from .teamworks_hr_connections_repository import (
    _close,
    _commit,
    _execute,
    _fetchall,
    _fetchone,
    _index_exists,
    _required_text,
    _rollback,
)


TEAMWORKS_HR_CASE_DOCUMENTS_SCHEMA_VERSION = 1
_SCHEMA_COMPONENT = "hr_case_documents_runtime"

_COLUMNS = (
    "structure_ref",
    "receipt_key",
    "case_id",
    "document_code",
    "state",
    "received_on",
    "withdrawn_on",
    "artifact_ref",
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
    CREATE TABLE IF NOT EXISTS tw_hr_case_document_receipts (
        structure_ref VARCHAR(80) NOT NULL,
        receipt_key VARCHAR(64) NOT NULL,
        case_id VARCHAR(100) NOT NULL,
        document_code VARCHAR(100) NOT NULL,
        state VARCHAR(30) NOT NULL,
        received_on VARCHAR(10) NOT NULL,
        withdrawn_on VARCHAR(10),
        artifact_ref VARCHAR(240),
        source VARCHAR(120),
        PRIMARY KEY (structure_ref, receipt_key)
    )
    """,
)

_INDEXES = (
    (
        "tw_hr_case_document_receipts",
        "idx_tw_hr_case_document_case",
        "structure_ref, case_id",
    ),
)


class StaleTeamworksHrCaseDocumentStateError(RuntimeError):
    """L'état courant d'une pièce a changé depuis la lecture du cas d'usage."""


class TeamworksHrCaseDocumentRepository:
    """Persistance de production du suivi administratif des pièces de démarche.

    Le schéma est additif et indépendant du schéma CRH-22. Aucune clé étrangère
    n'est ajoutée aux tables historiques. Une modification de réception et son
    événement d'audit sont écrits dans une même transaction. La projection de
    réception n'est jamais supprimée : un retrait est un état explicite et audité.

    La clé primaire utilise un hash déterministe du couple ``case_id/document_code``
    afin de ne pas dépasser les limites d'index des anciens serveurs MySQL lorsque
    les colonnes texte utilisent un encodage multioctet. Les valeurs métier restent
    conservées intégralement dans leurs colonnes dédiées.
    """

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        ensure_schema: bool = True,
    ) -> None:
        self._db_factory = db_factory or self._default_db_factory
        if ensure_schema:
            # Garantit l'existence des tables dossier/pièces attendues/audit CRH-22.
            TeamworksHrCasesRepository(db_factory=self._db_factory)
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
                    (_SCHEMA_COMPONENT, TEAMWORKS_HR_CASE_DOCUMENTS_SCHEMA_VERSION),
                )
            elif int(row[0]) != TEAMWORKS_HR_CASE_DOCUMENTS_SCHEMA_VERSION:
                raise RuntimeError(
                    "Version de schéma du suivi des pièces RH non prise en charge : "
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
            raise RuntimeError("Le schéma de suivi des pièces RH n'est pas initialisé.")
        return int(row[0])

    def get_case(self, *, structure_ref: str, case_id: str):
        return TeamworksHrCasesRepository(
            db_factory=self._db_factory,
            ensure_schema=False,
        ).get_case(structure_ref=structure_ref, case_id=case_id)

    def get_receipt(
        self,
        *,
        structure_ref: str,
        case_id: str,
        document_code: str,
    ) -> HrCaseDocumentReceipt | None:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        case_id = _required_text(case_id, "L'identifiant de la démarche RH est obligatoire.")
        document_code = _required_text(document_code, "Le code de la pièce RH est obligatoire.")
        db = self._db_factory()
        try:
            row = _fetchone(
                db,
                "SELECT "
                + ", ".join(_COLUMNS)
                + " FROM tw_hr_case_document_receipts "
                "WHERE structure_ref = ? AND receipt_key = ?",
                (structure_ref, _receipt_key(case_id, document_code)),
            )
        finally:
            _close(db)
        if row is None:
            return None
        receipt = _receipt_from_row(row)
        if receipt.case_id != case_id or receipt.document_code != document_code:
            raise RuntimeError("Collision de clé technique dans le suivi des pièces RH.")
        return receipt

    def list_receipts(
        self,
        *,
        structure_ref: str,
        case_id: str,
    ) -> tuple[HrCaseDocumentReceipt, ...]:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        case_id = _required_text(case_id, "L'identifiant de la démarche RH est obligatoire.")
        db = self._db_factory()
        try:
            rows = _fetchall(
                db,
                "SELECT "
                + ", ".join(_COLUMNS)
                + " FROM tw_hr_case_document_receipts "
                "WHERE structure_ref = ? AND case_id = ? ORDER BY document_code",
                (structure_ref, case_id),
            )
        finally:
            _close(db)
        return tuple(_receipt_from_row(row) for row in rows)

    def persist_receipt_change(
        self,
        *,
        structure_ref: str,
        expected_state: HrCaseDocumentState | None,
        receipt: HrCaseDocumentReceipt,
        event: HrAuditEvent,
    ) -> HrCaseDocumentReceipt:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if expected_state is not None and not isinstance(expected_state, HrCaseDocumentState):
            raise TypeError("L'état attendu de la pièce RH est invalide.")
        if not isinstance(receipt, HrCaseDocumentReceipt):
            raise TypeError("La réception de pièce RH à persister est invalide.")
        if not isinstance(event, HrAuditEvent):
            raise TypeError("L'événement de pièce RH à persister est invalide.")
        self._validate_event(receipt=receipt, event=event)

        receipt_key = _receipt_key(receipt.case_id, receipt.document_code)
        db = self._db_factory()
        try:
            case_row = _fetchone(
                db,
                """
                SELECT status
                FROM tw_hr_cases
                WHERE structure_ref = ? AND case_id = ?
                """,
                (structure_ref, receipt.case_id),
            )
            if case_row is None:
                raise LookupError("La démarche RH demandée est introuvable.")
            if HrCaseStatus(case_row[0]) in {HrCaseStatus.ACCEPTED, HrCaseStatus.CANCELLED}:
                raise StaleTeamworksHrCaseDocumentStateError(
                    "La démarche RH a été clôturée avant l'enregistrement de la pièce."
                )

            expected_document = _fetchone(
                db,
                """
                SELECT 1
                FROM tw_hr_case_expected_documents
                WHERE structure_ref = ? AND case_id = ? AND document_code = ?
                """,
                (structure_ref, receipt.case_id, receipt.document_code),
            )
            if expected_document is None:
                raise ValueError(
                    "Cette pièce n'est pas déclarée comme attendue dans la démarche RH."
                )

            current = _fetchone(
                db,
                """
                SELECT case_id, document_code, state
                FROM tw_hr_case_document_receipts
                WHERE structure_ref = ? AND receipt_key = ?
                """,
                (structure_ref, receipt_key),
            )
            if current is not None and (
                current[0] != receipt.case_id or current[1] != receipt.document_code
            ):
                raise RuntimeError("Collision de clé technique dans le suivi des pièces RH.")
            current_state = HrCaseDocumentState(current[2]) if current is not None else None
            if current_state is not expected_state:
                raise StaleTeamworksHrCaseDocumentStateError(
                    "L'état de la pièce RH a changé depuis sa lecture ; actualisez la démarche."
                )

            duplicate_event = _fetchone(
                db,
                """
                SELECT 1 FROM tw_hr_audit_events
                WHERE structure_ref = ? AND event_id = ?
                """,
                (structure_ref, event.event_id),
            )
            if duplicate_event is not None:
                raise ValueError(
                    f"L'événement RH '{event.event_id}' est déjà persisté."
                )

            values = _receipt_values(structure_ref, receipt_key, receipt)
            key = (structure_ref, receipt_key)
            if current is None:
                placeholders = ", ".join("?" for _ in _COLUMNS)
                _execute(
                    db,
                    "INSERT INTO tw_hr_case_document_receipts("
                    + ", ".join(_COLUMNS)
                    + f") VALUES ({placeholders})",
                    values,
                )
            else:
                update_columns = _COLUMNS[2:]
                assignments = ", ".join(f"{column} = ?" for column in update_columns)
                _execute(
                    db,
                    f"UPDATE tw_hr_case_document_receipts SET {assignments} "
                    "WHERE structure_ref = ? AND receipt_key = ?",
                    values[2:] + key,
                )

            _execute(
                db,
                """
                INSERT INTO tw_hr_audit_events(
                    structure_ref,
                    event_id,
                    event_kind,
                    target_kind,
                    target_ref,
                    occurred_at,
                    actor_ref,
                    source
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
            for position, field in enumerate(event.fields):
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_audit_fields(
                        structure_ref,
                        event_id,
                        position,
                        field_key,
                        field_value
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        structure_ref,
                        event.event_id,
                        position,
                        field.key,
                        field.value,
                    ),
                )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)
        return receipt

    @staticmethod
    def _validate_event(*, receipt: HrCaseDocumentReceipt, event: HrAuditEvent) -> None:
        if event.target_kind is not HrEventTargetKind.CASE or event.target_ref != receipt.case_id:
            raise ValueError("L'événement de pièce RH doit cibler la démarche concernée.")
        expected_kind = (
            HrEventKind.DOCUMENT_ADDED
            if receipt.state is HrCaseDocumentState.RECEIVED
            else HrEventKind.DOCUMENT_REMOVED
        )
        if event.kind is not expected_kind:
            raise ValueError("L'événement d'audit ne correspond pas à l'état de la pièce RH.")
        document_fields = [field.value for field in event.fields if field.key == "document_code"]
        if document_fields != [receipt.document_code]:
            raise ValueError("L'événement d'audit ne décrit pas la pièce RH persistée.")


def _receipt_key(case_id: str, document_code: str) -> str:
    payload = (case_id + "\0" + document_code).encode("utf-8")
    return sha256(payload).hexdigest()


def _receipt_values(
    structure_ref: str,
    receipt_key: str,
    receipt: HrCaseDocumentReceipt,
) -> tuple:
    return (
        structure_ref,
        receipt_key,
        receipt.case_id,
        receipt.document_code,
        receipt.state.value,
        receipt.received_on.isoformat(),
        receipt.withdrawn_on.isoformat() if receipt.withdrawn_on else None,
        receipt.artifact_ref,
        receipt.source,
    )


def _receipt_from_row(row) -> HrCaseDocumentReceipt:
    return HrCaseDocumentReceipt(
        case_id=row[2],
        document_code=row[3],
        state=HrCaseDocumentState(row[4]),
        received_on=date.fromisoformat(row[5]),
        withdrawn_on=date.fromisoformat(row[6]) if row[6] else None,
        artifact_ref=row[7],
        source=row[8],
    )
