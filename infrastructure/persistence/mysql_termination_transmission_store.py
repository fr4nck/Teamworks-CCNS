"""Commandes atomiques de transmission à Impact Emploi — SORTIE-003 (MySQL/MariaDB).

Chaque commande s'exécute dans UNE transaction :

1. verrou exclusif de la ligne ``tw_contract_termination`` (clé primaire) ;
2. recherche du ``command_id`` (rejeu idempotent ou conflit explicite) ;
3. contrôle de la version attendue (optimistic locking SORTIE-002) ;
4. règles du domaine, payload canonique, snapshot suivant (V1, V2…) ;
5. insertion du snapshot, de la commande (audit sans payload) ;
6. mise à jour de la sortie, version + 1 exactement ;
7. commit — ou rollback complet au moindre échec.

Toutes les écritures d'une même sortie sont sérialisées par le verrou de sa
ligne, pris en premier. Les lectures qui suivent sont des lectures cohérentes
ouvertes *après* ce verrou : elles voient tout ce qui a été validé avant lui,
sans verrou d'intervalle (source classique d'interblocages entre sorties).

Retry ciblé : seule l'erreur InnoDB 1213 (interblocage, transaction déjà
annulée par le serveur) rejoue la transaction complète, au plus
``max_attempts`` fois, avec le même ``command_id``. Rien d'autre n'est rejoué.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable, Optional

from domain.employment.termination import TerminationDomainError
from domain.employment.termination_repository import (
    CommandIdempotencyConflict,
    SnapshotIntegrityError,
    TerminationNotFound,
    TerminationPersistenceError,
    TerminationVersionConflict,
    TransmissionRetryExhausted,
)
from domain.employment.termination_transmission import (
    CommandType,
    CorrectionRequestResult,
    RequestCorrection,
    TerminationTransmissionSnapshot,
    TransmissionResult,
    TransmitTermination,
    create_transmission_snapshot,
)
from infrastructure.persistence.mysql_termination_repository import (
    TABLE as TERMINATION_TABLE,
    TERMINATION_COLUMNS,
    correction_values,
    row_to_termination,
)

SNAPSHOT_TABLE = "tw_termination_transmission_snapshot"
COMMAND_TABLE = "tw_termination_command"
DEADLOCK_ERRNO = 1213
DUPLICATE_KEY_ERRNO = 1062

_SNAPSHOT_COLUMNS = (
    "snapshot_id", "termination_id", "version", "canonical_payload", "payload_hash",
    "created_at", "created_by", "transmitted_at", "transmitted_by", "channel",
    "external_reference", "supersedes_snapshot_id", "correction_reason",
)
_SELECT_SNAPSHOT = "SELECT " + ", ".join(_SNAPSHOT_COLUMNS) + " FROM " + SNAPSHOT_TABLE
_COMMAND_COLUMNS = (
    "command_id", "command_type", "command_hash", "termination_id", "snapshot_id",
    "snapshot_version", "payload_hash", "termination_version_before",
    "termination_version_after", "actor_id", "recorded_at",
)


class _CommandIdRace(Exception):
    """Le même command_id vient d'être validé par une autre transaction."""


def _errno(exc: BaseException) -> Optional[int]:
    errno = getattr(exc, "errno", None)
    if errno is None and getattr(exc, "args", None) and isinstance(exc.args[0], int):
        errno = exc.args[0]
    return errno


def _to_storage(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)


def _from_storage(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _row_to_snapshot(row) -> TerminationTransmissionSnapshot:
    values = dict(zip(_SNAPSHOT_COLUMNS, row))
    try:
        return TerminationTransmissionSnapshot(
            snapshot_id=values["snapshot_id"],
            termination_id=values["termination_id"],
            version=int(values["version"]),
            canonical_payload=values["canonical_payload"],
            payload_hash=values["payload_hash"],
            created_at=_from_storage(values["created_at"]),
            created_by=values["created_by"],
            transmitted_at=_from_storage(values["transmitted_at"]),
            transmitted_by=values["transmitted_by"],
            channel=values["channel"],
            external_reference=values["external_reference"],
            supersedes_snapshot_id=values["supersedes_snapshot_id"],
            correction_reason=values["correction_reason"],
        )
    except TerminationDomainError as exc:
        raise SnapshotIntegrityError(exc.code, "stored snapshot failed verification: %s" % exc) from exc


class MySqlTerminationTransmissionStore:
    def __init__(
        self,
        connection_factory: Callable[[], object],
        failure_injector: Optional[Callable[[str], None]] = None,
        clock: Callable[[], datetime] = _utcnow,
        max_attempts: int = 3,
        retry_backoff_seconds: float = 0.05,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self._connect = connection_factory
        self._failure_injector = failure_injector
        self._clock = clock
        self._max_attempts = max_attempts
        self._backoff = retry_backoff_seconds
        self._sleep = sleep
        self.last_attempts = 0

    # ------------------------------------------------------------------ outils

    def _failure_point(self, name: str) -> None:
        if self._failure_injector is not None:
            self._failure_injector(name)

    def _open(self):
        conn = self._connect()
        if getattr(conn, "autocommit", False) is True:
            conn.close()
            raise TerminationPersistenceError(
                "AUTOCOMMIT_NOT_ALLOWED",
                "termination transmission requires a transactional connection (autocommit off)",
            )
        conn.rollback()  # aucune vue de lecture ouverte avant le verrou de la sortie
        return conn

    def _execute(self, operation):
        deadlocks = 0
        resolved_race = False
        self.last_attempts = 0
        while True:
            self.last_attempts += 1
            self._failure_point("attempt")
            conn = self._open()
            try:
                result = operation(conn)
                self._failure_point("before_commit")
                conn.commit()
                return result
            except _CommandIdRace:
                conn.rollback()
                if resolved_race:
                    raise TerminationPersistenceError(
                        "COMMAND_ID_RACE_UNRESOLVED", "command id collision could not be resolved"
                    )
                resolved_race = True  # relire : rejeu ou conflit explicite
            except Exception as exc:
                conn.rollback()
                if _errno(exc) != DEADLOCK_ERRNO:
                    raise
                deadlocks += 1
                if deadlocks >= self._max_attempts:
                    raise TransmissionRetryExhausted(deadlocks) from exc
                self._sleep(self._backoff * deadlocks)
            finally:
                conn.close()

    def _now(self) -> datetime:
        return _to_storage(self._clock()).replace(tzinfo=timezone.utc)

    @staticmethod
    def _lock_termination(cur, termination_id: str):
        cur.execute(
            "SELECT " + ", ".join(TERMINATION_COLUMNS) + " FROM " + TERMINATION_TABLE
            + " WHERE termination_id = %s FOR UPDATE",
            (termination_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise TerminationNotFound(termination_id)
        return row_to_termination(row)

    @staticmethod
    def _recorded_command(cur, command_id: str, command_type: CommandType, command_hash: str):
        cur.execute(
            "SELECT command_type, command_hash, snapshot_id, termination_version_after, termination_id"
            " FROM " + COMMAND_TABLE + " WHERE command_id = %s",
            (command_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        if row[0] != command_type.value or row[1] != command_hash:
            raise CommandIdempotencyConflict(command_id)
        return row

    @staticmethod
    def _latest_snapshot(cur, termination_id: str) -> Optional[TerminationTransmissionSnapshot]:
        cur.execute(
            _SELECT_SNAPSHOT + " WHERE termination_id = %s ORDER BY version DESC LIMIT 1",
            (termination_id,),
        )
        row = cur.fetchone()
        return None if row is None else _row_to_snapshot(row)

    def _insert_command(self, cur, command_id, command_type, command_hash, termination,
                        snapshot, actor_id, recorded_at) -> None:
        values = (
            command_id, command_type.value, command_hash, termination.termination_id,
            None if snapshot is None else snapshot.snapshot_id,
            None if snapshot is None else snapshot.version,
            None if snapshot is None else snapshot.payload_hash,
            termination.version, termination.version + 1, actor_id, _to_storage(recorded_at),
        )
        try:
            cur.execute(
                "INSERT INTO " + COMMAND_TABLE + " (" + ", ".join(_COMMAND_COLUMNS) + ") VALUES ("
                + ", ".join(["%s"] * len(_COMMAND_COLUMNS)) + ")",
                values,
            )
        except Exception as exc:
            if _errno(exc) == DUPLICATE_KEY_ERRNO:
                raise _CommandIdRace() from exc
            raise

    def _update_termination(self, cur, termination, expected_version: int) -> None:
        corrections = correction_values(termination)
        cur.execute(
            "UPDATE " + TERMINATION_TABLE + " SET workflow_status = %s, updated_at = %s,"
            " correction_reason = %s, correction_requested_at = %s, correction_requested_by = %s,"
            " version = version + 1 WHERE termination_id = %s AND version = %s",
            (
                termination.workflow_status.value, _to_storage(termination.updated_at),
                corrections["correction_reason"], corrections["correction_requested_at"],
                corrections["correction_requested_by"], termination.termination_id, expected_version,
            ),
        )
        if cur.rowcount != 1:  # impossible sous le verrou ; garde-fou
            raise TerminationVersionConflict(termination.termination_id, expected_version)

    def _snapshot_by_id(self, cur, snapshot_id: str) -> TerminationTransmissionSnapshot:
        cur.execute(_SELECT_SNAPSHOT + " WHERE snapshot_id = %s", (snapshot_id,))
        row = cur.fetchone()
        if row is None:
            raise SnapshotIntegrityError("SNAPSHOT_MISSING", "recorded command points to a missing snapshot")
        return _row_to_snapshot(row)

    # --------------------------------------------------------------- commandes

    def transmit(self, command: TransmitTermination) -> TransmissionResult:
        """Première transmission : PRET -> TRANSMIS + snapshot V1, atomiquement."""
        return self._transmit(command, CommandType.TRANSMIT)

    def transmit_correction(self, command: TransmitTermination) -> TransmissionResult:
        """Transmission corrective : snapshot V(n+1) supersédant V(n), V(n) intact."""
        return self._transmit(command, CommandType.TRANSMIT_CORRECTION)

    def _transmit(self, command: TransmitTermination, command_type: CommandType) -> TransmissionResult:
        command_hash = command.fingerprint(command_type)

        def operation(conn):
            cur = conn.cursor()
            termination = self._lock_termination(cur, command.termination_id)
            self._failure_point("after_termination_lock")
            recorded = self._recorded_command(cur, command.command_id, command_type, command_hash)
            if recorded is not None:
                return TransmissionResult(self._snapshot_by_id(cur, recorded[2]), int(recorded[3]), True)
            if termination.version != command.expected_version:
                raise TerminationVersionConflict(termination.termination_id, command.expected_version)
            previous = self._latest_snapshot(cur, termination.termination_id)
            if command_type is CommandType.TRANSMIT and previous is not None:
                raise TerminationDomainError("SNAPSHOT_ALREADY_TRANSMITTED", "V1 already exists: request a correction")
            if command_type is CommandType.TRANSMIT_CORRECTION and previous is None:
                raise TerminationDomainError("SNAPSHOT_PREDECESSOR_REQUIRED", "nothing was transmitted yet")
            now = self._now()
            snapshot = create_transmission_snapshot(
                termination,
                previous=previous,
                hr_items=command.hr_items,
                created_at=now,
                created_by=command.actor_id,
                transmitted_at=command.transmitted_at,
                transmitted_by=command.transmitted_by,
                channel=command.channel,
                external_reference=command.external_reference,
                expected_payload_hash=command.expected_payload_hash,
            )
            if command_type is CommandType.TRANSMIT:
                termination.record_first_transmission(snapshot)
            else:
                termination.record_correction_transmission(snapshot)
            self._failure_point("before_snapshot_insert")
            cur.execute(
                "INSERT INTO " + SNAPSHOT_TABLE + " (" + ", ".join(_SNAPSHOT_COLUMNS) + ") VALUES ("
                + ", ".join(["%s"] * len(_SNAPSHOT_COLUMNS)) + ")",
                (
                    snapshot.snapshot_id, snapshot.termination_id, snapshot.version,
                    snapshot.canonical_payload, snapshot.payload_hash,
                    _to_storage(snapshot.created_at), snapshot.created_by,
                    _to_storage(snapshot.transmitted_at), snapshot.transmitted_by,
                    snapshot.channel.value, snapshot.external_reference,
                    snapshot.supersedes_snapshot_id, snapshot.correction_reason,
                ),
            )
            self._failure_point("after_snapshot_insert")
            self._insert_command(
                cur, command.command_id, command_type, command_hash, termination,
                snapshot, command.actor_id, now,
            )
            self._failure_point("after_command_insert")
            self._update_termination(cur, termination, command.expected_version)
            self._failure_point("after_termination_update")
            return TransmissionResult(snapshot, command.expected_version + 1, False)

        return self._execute(operation)

    def request_correction(self, command: RequestCorrection) -> CorrectionRequestResult:
        """Ouvre explicitement une correction sur une sortie déjà transmise."""
        command_hash = command.fingerprint()

        def operation(conn):
            cur = conn.cursor()
            termination = self._lock_termination(cur, command.termination_id)
            self._failure_point("after_termination_lock")
            recorded = self._recorded_command(
                cur, command.command_id, CommandType.REQUEST_CORRECTION, command_hash
            )
            if recorded is not None:
                return CorrectionRequestResult(termination.termination_id, int(recorded[3]), True)
            if termination.version != command.expected_version:
                raise TerminationVersionConflict(termination.termination_id, command.expected_version)
            now = self._now()
            termination.request_correction(
                command.reason, requested_by=command.requested_by, requested_at=now
            )
            self._insert_command(
                cur, command.command_id, CommandType.REQUEST_CORRECTION, command_hash,
                termination, None, command.requested_by, now,
            )
            self._failure_point("after_command_insert")
            self._update_termination(cur, termination, command.expected_version)
            self._failure_point("after_termination_update")
            return CorrectionRequestResult(termination.termination_id, command.expected_version + 1, False)

        return self._execute(operation)

    # ---------------------------------------------------------------- lectures

    def list_snapshots(self, termination_id: str) -> list[TerminationTransmissionSnapshot]:
        """Historique complet, vérifié : hash, versions consécutives, supersession."""
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(_SELECT_SNAPSHOT + " WHERE termination_id = %s ORDER BY version", (termination_id,))
            rows = cur.fetchall()
            conn.rollback()
        finally:
            conn.close()
        snapshots = [_row_to_snapshot(row) for row in rows]
        previous = None
        for snapshot in snapshots:
            expected_version = 1 if previous is None else previous.version + 1
            expected_parent = None if previous is None else previous.snapshot_id
            if snapshot.version != expected_version or snapshot.supersedes_snapshot_id != expected_parent:
                raise SnapshotIntegrityError("SNAPSHOT_CHAIN_BROKEN", "snapshot history is not a linear chain")
            previous = snapshot
        return snapshots

    def get_snapshot(self, snapshot_id: str) -> Optional[TerminationTransmissionSnapshot]:
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(_SELECT_SNAPSHOT + " WHERE snapshot_id = %s", (snapshot_id,))
            row = cur.fetchone()
            conn.rollback()
        finally:
            conn.close()
        return None if row is None else _row_to_snapshot(row)

    def audit_trail(self, termination_id: str) -> list[dict]:
        """Qui a fait quoi, quand, sur quelle version — sans aucun payload RH."""
        conn = self._open()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT " + ", ".join(_COMMAND_COLUMNS) + " FROM " + COMMAND_TABLE
                + " WHERE termination_id = %s ORDER BY termination_version_after",
                (termination_id,),
            )
            rows = cur.fetchall()
            conn.rollback()
        finally:
            conn.close()
        trail = []
        for row in rows:
            entry = dict(zip(_COMMAND_COLUMNS, row))
            entry["recorded_at"] = _from_storage(entry["recorded_at"])
            trail.append(entry)
        return trail
