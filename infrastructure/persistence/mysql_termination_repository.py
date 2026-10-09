"""Adaptateur MySQL/MariaDB des sorties salarié — SORTIE-002.

Chaque opération ouvre sa propre connexion DB-API (``connection_factory``),
s'exécute dans une transaction unique, est annulée intégralement en cas
d'erreur et referme toujours la connexion.

La table est décrite par ``sql/mysql/termination_v1.sql``. Les horodatages sont
stockés en UTC, à la seconde (compatibilité MySQL 5.5) ; après une écriture
réussie, l'objet porte exactement les valeurs relues depuis la base.

Voir ``domain.employment.termination_repository`` pour le contrat de version.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional

from domain.employment.termination import (
    ContractTermination,
    HrInputChecks,
    TerminationWorkflowStatus,
)
from domain.employment.termination_repository import (
    ActiveTerminationExists,
    TerminationAlreadyExists,
    TerminationNotFound,
    TerminationPersistenceError,
    TerminationVersionConflict,
)

TABLE = "tw_contract_termination"
ACTIVE_UNIQUE_KEY = "uq_tw_contract_termination_active"
_DUPLICATE_KEY_ERRNO = 1062

_COLUMNS = (
    "termination_id", "contract_id", "active_contract_id", "decision_date", "known_at",
    "effective_end_date", "termination_reason", "notification_date", "last_worked_date",
    "notice_status", "notice_start", "notice_end", "comments", "hr_hours", "hr_absences",
    "hr_leave", "hr_variable_pay", "hr_exceptional_items", "workflow_status", "created_at",
    "created_by", "updated_at", "version",
)
# Colonnes réécrites par save ; l'identité, le contrat et la création sont figés.
_MUTABLE_COLUMNS = tuple(
    name for name in _COLUMNS
    if name not in ("termination_id", "contract_id", "created_at", "created_by", "version")
)
_SELECT = "SELECT " + ", ".join(_COLUMNS) + " FROM " + TABLE


def _to_storage(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)


def _from_storage(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc)


def _active_contract_id(termination: ContractTermination) -> Optional[str]:
    if termination.workflow_status is TerminationWorkflowStatus.CLOTURE:
        return None
    return termination.contract_id


def _mutable_values(termination: ContractTermination) -> dict:
    checks = termination.hr_checks
    return {
        "active_contract_id": _active_contract_id(termination),
        "decision_date": termination.decision_date,
        "known_at": _to_storage(termination.known_at),
        "effective_end_date": termination.effective_end_date,
        "termination_reason": termination.termination_reason.value,
        "notification_date": termination.notification_date,
        "last_worked_date": termination.last_worked_date,
        "notice_status": termination.notice_status.value,
        "notice_start": termination.notice_start,
        "notice_end": termination.notice_end,
        "comments": termination.comments,
        "hr_hours": checks.hours.value,
        "hr_absences": checks.absences.value,
        "hr_leave": checks.leave.value,
        "hr_variable_pay": checks.variable_pay.value,
        "hr_exceptional_items": checks.exceptional_items.value,
        "workflow_status": termination.workflow_status.value,
        "updated_at": _to_storage(termination.updated_at),
    }


def _row_to_domain(row) -> ContractTermination:
    values = dict(zip(_COLUMNS, row))
    return ContractTermination(
        termination_id=values["termination_id"],
        contract_id=values["contract_id"],
        decision_date=values["decision_date"],
        known_at=_from_storage(values["known_at"]),
        effective_end_date=values["effective_end_date"],
        termination_reason=values["termination_reason"],
        notification_date=values["notification_date"],
        last_worked_date=values["last_worked_date"],
        notice_status=values["notice_status"],
        notice_start=values["notice_start"],
        notice_end=values["notice_end"],
        comments=values["comments"],
        hr_checks=HrInputChecks(
            hours=values["hr_hours"],
            absences=values["hr_absences"],
            leave=values["hr_leave"],
            variable_pay=values["hr_variable_pay"],
            exceptional_items=values["hr_exceptional_items"],
        ),
        workflow_status=values["workflow_status"],
        created_at=_from_storage(values["created_at"]),
        created_by=values["created_by"],
        updated_at=_from_storage(values["updated_at"]),
        version=int(values["version"]),
    )


def _is_duplicate_key(exc: BaseException) -> bool:
    errno = getattr(exc, "errno", None)
    if errno is None and getattr(exc, "args", None):
        errno = exc.args[0]
    return errno == _DUPLICATE_KEY_ERRNO


def _apply_stored_timestamps(target: ContractTermination, stored: dict) -> None:
    target.known_at = _from_storage(stored["known_at"])
    target.updated_at = _from_storage(stored["updated_at"])


class MySqlContractTerminationRepository:
    def __init__(
        self,
        connection_factory: Callable[[], object],
        failure_injector: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._connect = connection_factory
        self._failure_injector = failure_injector

    def _failure_point(self, name: str) -> None:
        if self._failure_injector is not None:
            self._failure_injector(name)

    def _open(self):
        conn = self._connect()
        if getattr(conn, "autocommit", False) is True:
            conn.close()
            raise TerminationPersistenceError(
                "AUTOCOMMIT_NOT_ALLOWED",
                "termination persistence requires a transactional connection (autocommit off)",
            )
        return conn

    def add(self, termination: ContractTermination) -> None:
        if termination.version != 0:
            raise TerminationPersistenceError(
                "TERMINATION_ALREADY_PERSISTED",
                "only a never-persisted termination (version 0) can be added",
            )
        values = _mutable_values(termination)
        values.update(
            termination_id=termination.termination_id,
            contract_id=termination.contract_id,
            created_at=_to_storage(termination.created_at),
            created_by=termination.created_by,
            version=1,
        )
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO " + TABLE + " (" + ", ".join(_COLUMNS) + ") VALUES ("
                + ", ".join(["%s"] * len(_COLUMNS)) + ")",
                tuple(values[name] for name in _COLUMNS),
            )
            self._failure_point("after_insert")
            conn.commit()
        except Exception as exc:
            conn.rollback()
            if _is_duplicate_key(exc):
                if ACTIVE_UNIQUE_KEY in str(exc):
                    raise ActiveTerminationExists(termination.contract_id) from exc
                raise TerminationAlreadyExists(termination.termination_id) from exc
            raise
        finally:
            conn.close()
        termination.created_at = _from_storage(values["created_at"])
        _apply_stored_timestamps(termination, values)
        termination.version = 1

    def get(self, termination_id: str) -> Optional[ContractTermination]:
        return self._fetch_one(_SELECT + " WHERE termination_id = %s", (termination_id,))

    def get_active_for_contract(self, contract_id: str) -> Optional[ContractTermination]:
        return self._fetch_one(_SELECT + " WHERE active_contract_id = %s", (contract_id,))

    def list_for_contract(self, contract_id: str) -> list[ContractTermination]:
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(
                _SELECT + " WHERE contract_id = %s ORDER BY created_at, termination_id",
                (contract_id,),
            )
            rows = cur.fetchall()
            conn.rollback()
        finally:
            conn.close()
        return [_row_to_domain(row) for row in rows]

    def _fetch_one(self, sql: str, params: tuple) -> Optional[ContractTermination]:
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.rollback()
        finally:
            conn.close()
        return None if row is None else _row_to_domain(row)

    def save(self, termination: ContractTermination) -> None:
        expected = termination.version
        if expected < 1:
            raise TerminationPersistenceError(
                "TERMINATION_NOT_PERSISTED", "a termination must be added before being saved"
            )
        values = _mutable_values(termination)
        assignments = ", ".join(name + " = %s" for name in _MUTABLE_COLUMNS)
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE " + TABLE + " SET " + assignments + ", version = version + 1"
                " WHERE termination_id = %s AND contract_id = %s AND version = %s",
                tuple(values[name] for name in _MUTABLE_COLUMNS)
                + (termination.termination_id, termination.contract_id, expected),
            )
            if cur.rowcount != 1:
                cur.execute(
                    "SELECT contract_id, version FROM " + TABLE + " WHERE termination_id = %s",
                    (termination.termination_id,),
                )
                current = cur.fetchone()
                conn.rollback()
                if current is None:
                    raise TerminationNotFound(termination.termination_id)
                if current[0] != termination.contract_id:
                    raise TerminationPersistenceError(
                        "TERMINATION_CONTRACT_IMMUTABLE",
                        "contract_id of a persisted termination cannot change",
                    )
                raise TerminationVersionConflict(termination.termination_id, expected)
            self._failure_point("after_update")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        _apply_stored_timestamps(termination, values)
        termination.version = expected + 1
