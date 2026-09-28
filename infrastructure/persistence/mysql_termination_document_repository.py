"""Persistance transactionnelle des documents de sortie — SORTIE-004."""
from __future__ import annotations

from datetime import datetime, timezone

from domain.employment.termination import TerminationDomainError
from domain.employment.termination_documents import TerminationDocument
from domain.employment.termination_repository import TerminationPersistenceError

TABLE = "tw_termination_document"
_COLUMNS = (
    "document_id", "termination_id", "document_type", "source", "document_date",
    "received_at", "received_by", "file_reference", "sha256", "external_reference",
    "archived_at", "archived_by", "delivered_at", "delivered_by",
)
_SELECT = "SELECT " + ", ".join(_COLUMNS) + " FROM " + TABLE


def _to_storage(value):
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)


def _from_storage(value):
    return None if value is None else value.replace(tzinfo=timezone.utc)


def _row(row):
    v = dict(zip(_COLUMNS, row))
    return TerminationDocument(
        document_id=v["document_id"], termination_id=v["termination_id"],
        document_type=v["document_type"], source=v["source"], document_date=v["document_date"],
        received_at=_from_storage(v["received_at"]), received_by=v["received_by"],
        file_reference=v["file_reference"], sha256=v["sha256"], external_reference=v["external_reference"],
        archived_at=_from_storage(v["archived_at"]), archived_by=v["archived_by"],
        delivered_at=_from_storage(v["delivered_at"]), delivered_by=v["delivered_by"],
    )


def _duplicate(exc):
    errno = getattr(exc, "errno", None)
    if errno is None and getattr(exc, "args", None) and isinstance(exc.args[0], int):
        errno = exc.args[0]
    return errno == 1062


class MySqlTerminationDocumentRepository:
    def __init__(self, connection_factory):
        self._connect = connection_factory

    def _open(self):
        conn = self._connect()
        if getattr(conn, "autocommit", False) is True:
            conn.close()
            raise TerminationPersistenceError("AUTOCOMMIT_NOT_ALLOWED", "document repository requires autocommit off")
        conn.rollback()
        return conn

    def add(self, document: TerminationDocument):
        conn = self._open()
        try:
            cur = conn.cursor()
            values = (
                document.document_id, document.termination_id, document.document_type.value,
                document.source.value, document.document_date, _to_storage(document.received_at),
                document.received_by, document.file_reference, document.sha256, document.external_reference,
                _to_storage(document.archived_at), document.archived_by,
                _to_storage(document.delivered_at), document.delivered_by,
            )
            try:
                cur.execute(
                    "INSERT INTO " + TABLE + " (" + ", ".join(_COLUMNS) + ") VALUES (" +
                    ", ".join(["%s"] * len(_COLUMNS)) + ")", values,
                )
            except Exception as exc:
                if _duplicate(exc):
                    raise TerminationPersistenceError("DOCUMENT_DUPLICATE", "same document is already recorded for this termination") from exc
                raise
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get(self, document_id: str):
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(_SELECT + " WHERE document_id = %s", (document_id,))
            row = cur.fetchone()
            return None if row is None else _row(row)
        finally:
            conn.rollback()
            conn.close()

    def list_for_termination(self, termination_id: str):
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(_SELECT + " WHERE termination_id = %s ORDER BY received_at, document_id", (termination_id,))
            return tuple(_row(row) for row in cur.fetchall())
        finally:
            conn.rollback()
            conn.close()

    def _mark_once(self, document_id: str, *, column_at: str, column_by: str, at: datetime, by: str):
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE " + TABLE + " SET " + column_at + " = %s, " + column_by + " = %s"
                " WHERE document_id = %s AND " + column_at + " IS NULL AND received_at <= %s",
                (_to_storage(at), by, document_id, _to_storage(at)),
            )
            if cur.rowcount != 1:
                cur.execute(_SELECT + " WHERE document_id = %s", (document_id,))
                row = cur.fetchone()
                if row is None:
                    raise TerminationPersistenceError("DOCUMENT_NOT_FOUND", "termination document not found")
                raise TerminationPersistenceError("DOCUMENT_STATE_CONFLICT", "document state was already changed or timestamp is invalid")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def mark_archived(self, document_id: str, *, at: datetime, by: str):
        self._mark_once(document_id, column_at="archived_at", column_by="archived_by", at=at, by=by)

    def mark_delivered(self, document_id: str, *, at: datetime, by: str):
        self._mark_once(document_id, column_at="delivered_at", column_by="delivered_by", at=at, by=by)
