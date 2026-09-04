"""Persistance additive du contrat ``session-actual/1`` dans le domaine RH.

Le dépôt ouvre ``GestionDB`` uniquement lorsqu'il est réellement utilisé. Les
migrations sont explicites et aucune écriture n'est faite dans le planning, les
contrats ou la paie.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping, Optional

from domain.employment import SOURCE_DOMAIN, SessionActual, SessionActualContractError

MAPPING_TABLE = "tw_hr_person_uid_mapping"
INBOX_TABLE = "tw_session_actual_inbox"
WORK_TABLE = "tw_session_actual_work"


class SessionActualHrPersistenceError(ValueError):
    """Erreur déterministe de persistance ou de contrat, non rejouable."""


class SessionActualHrTechnicalError(RuntimeError):
    """Panne technique/transitoire de persistance, éligible au retry transport."""


@dataclass(frozen=True, slots=True)
class SessionActualReceiveResult:
    status: str
    session_uid: str
    actual_revision: int
    person_id: Optional[int]


class SessionActualHrRepository:
    def __init__(self, db_factory: Optional[Callable[[], object]] = None):
        self._db_factory = db_factory or self._default_db_factory
        self._db = None

    @staticmethod
    def _default_db_factory():
        import GestionDB
        return GestionDB.DB()

    @property
    def db(self):
        if self._db is None:
            self._db = self._db_factory()
        return self._db

    @property
    def network(self) -> bool:
        return bool(getattr(self.db, "isNetwork", False))

    def close(self) -> None:
        if self._db is None:
            return
        close = getattr(self._db, "Close", None)
        if callable(close):
            close()
        else:
            connection = getattr(self._db, "connexion", None)
            if connection is not None:
                connection.close()
        self._db = None

    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.network else sql

    def _execute(self, sql: str, params: tuple[Any, ...] = ()):
        cursor = getattr(self.db, "cursor", None)
        if cursor is None:
            raise SessionActualHrTechnicalError("La connexion ne fournit pas de curseur SQL")
        cursor.execute(self._sql(sql), params)
        return cursor

    def _fetchone(self, sql: str, params: tuple[Any, ...] = (), *, lock: bool = False):
        if lock and self.network:
            sql = sql.rstrip().rstrip(";") + " FOR UPDATE"
        cursor = self._execute(sql, params)
        return cursor.fetchone()

    def _commit(self) -> None:
        commit = getattr(self.db, "Commit", None)
        if callable(commit):
            commit()
            return
        connection = getattr(self.db, "connexion", None)
        if connection is None:
            raise SessionActualHrTechnicalError("La connexion ne permet pas le commit")
        connection.commit()

    def _rollback(self) -> None:
        rollback = getattr(self.db, "Rollback", None)
        if callable(rollback):
            rollback()
            return
        connection = getattr(self.db, "connexion", None)
        if connection is None:
            raise SessionActualHrTechnicalError("La connexion ne permet pas le rollback")
        connection.rollback()

    @staticmethod
    def _timestamp(value: Optional[datetime] = None) -> str:
        value = value or datetime.now()
        if not isinstance(value, datetime):
            raise SessionActualHrPersistenceError("horodatage invalide")
        return value.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _key(value: Any, field: str, maximum: int) -> str:
        if not isinstance(value, str) or not (normalized := value.strip()):
            raise SessionActualHrPersistenceError(f"{field} obligatoire")
        if len(normalized) > maximum or any(ord(c) < 32 for c in normalized):
            raise SessionActualHrPersistenceError(f"{field} invalide")
        return normalized

    def _table_exists(self, table: str) -> bool:
        checker = getattr(self.db, "IsTableExists", None)
        if callable(checker):
            return bool(checker(table))
        if self.network:
            return self._fetchone("SHOW TABLES LIKE ?", (table,)) is not None
        return self._fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ) is not None

    @staticmethod
    def _schema_statements(network: bool) -> tuple[str, ...]:
        auto_id = "INTEGER PRIMARY KEY AUTO_INCREMENT" if network else "INTEGER PRIMARY KEY AUTOINCREMENT"
        return (
            f"""CREATE TABLE IF NOT EXISTS {MAPPING_TABLE} (
                IDmapping {auto_id}, person_uid VARCHAR(100) NOT NULL UNIQUE,
                IDpersonne INTEGER NOT NULL UNIQUE, is_active BOOLEAN NOT NULL DEFAULT 1,
                date_creation DATETIME, date_modification DATETIME)""",
            f"""CREATE TABLE IF NOT EXISTS {INBOX_TABLE} (
                IDinbox {auto_id}, idempotence_key VARCHAR(255) NOT NULL UNIQUE,
                revision_key VARCHAR(255) NOT NULL UNIQUE, source_domain VARCHAR(64) NOT NULL,
                contract_version VARCHAR(64) NOT NULL, event_type VARCHAR(64) NOT NULL,
                actual_uuid VARCHAR(64) NOT NULL, session_uid VARCHAR(128) NOT NULL,
                actual_revision INTEGER NOT NULL, payload_sha256 VARCHAR(64) NOT NULL,
                date_reception DATETIME NOT NULL)""",
            f"""CREATE TABLE IF NOT EXISTS {WORK_TABLE} (
                IDactual {auto_id}, session_uid VARCHAR(128) NOT NULL UNIQUE,
                actual_uuid VARCHAR(64) NOT NULL UNIQUE, IDpersonne INTEGER,
                actual_staff_uid VARCHAR(100), assignment_date DATE NOT NULL,
                session_status VARCHAR(32) NOT NULL, actual_place_uid VARCHAR(128),
                actual_start_time VARCHAR(5), actual_end_time VARCHAR(5),
                actual_duration_minutes INTEGER, actual_comment TEXT,
                actual_revision INTEGER NOT NULL, validated_at VARCHAR(64) NOT NULL,
                source_domain VARCHAR(64) NOT NULL, payload_sha256 VARCHAR(64) NOT NULL,
                date_creation DATETIME, date_modification DATETIME)""",
        )

    def ensure_schema(self, apply: bool = False) -> tuple[str, ...]:
        missing = tuple(t for t in (MAPPING_TABLE, INBOX_TABLE, WORK_TABLE) if not self._table_exists(t))
        if not missing or not apply:
            return missing
        try:
            for statement in self._schema_statements(self.network):
                self._execute(statement)
            self._commit()
        except Exception:
            self._rollback()
            raise
        remaining = tuple(t for t in (MAPPING_TABLE, INBOX_TABLE, WORK_TABLE) if not self._table_exists(t))
        if remaining:
            raise SessionActualHrPersistenceError("Schéma du réalisé RH incomplet: %s" % ", ".join(remaining))
        return ()

    def _require_schema(self) -> None:
        missing = self.ensure_schema(False)
        if missing:
            raise SessionActualHrTechnicalError("Tables du réalisé RH absentes: %s" % ", ".join(missing))

    def register_person_uid(self, person_uid: str, person_id: int) -> int:
        self._require_schema()
        person_uid = self._key(person_uid, "person_uid", 100)
        if type(person_id) is not int or person_id < 1:
            raise SessionActualHrPersistenceError("IDpersonne invalide")
        if self._fetchone("SELECT IDpersonne FROM personnes WHERE IDpersonne=?", (person_id,)) is None:
            raise SessionActualHrPersistenceError("Personne Teamworks introuvable")

        by_uid = self._fetchone(
            f"SELECT IDpersonne, is_active FROM {MAPPING_TABLE} WHERE person_uid=?", (person_uid,)
        )
        now = self._timestamp()
        if by_uid is not None:
            if int(by_uid[0]) != person_id:
                raise SessionActualHrPersistenceError("Cet UID RH est déjà associé à une autre personne")
            if int(by_uid[1]) != 1:
                self._execute(
                    f"UPDATE {MAPPING_TABLE} SET is_active=1, date_modification=? WHERE person_uid=?",
                    (now, person_uid),
                )
                self._commit()
            return person_id
        if self._fetchone(f"SELECT person_uid FROM {MAPPING_TABLE} WHERE IDpersonne=?", (person_id,)) is not None:
            raise SessionActualHrPersistenceError("Cette personne possède déjà un UID RH stable")
        try:
            self._execute(
                f"INSERT INTO {MAPPING_TABLE} (person_uid,IDpersonne,is_active,date_creation,date_modification) VALUES (?,?,1,?,?)",
                (person_uid, person_id, now, now),
            )
            self._commit()
        except Exception:
            self._rollback()
            raise
        return person_id

    def resolve_person_uid(self, person_uid: str) -> Optional[int]:
        self._require_schema()
        person_uid = self._key(person_uid, "actual_staff_uid", 100)
        row = self._fetchone(
            f"SELECT IDpersonne FROM {MAPPING_TABLE} WHERE person_uid=? AND is_active=1", (person_uid,)
        )
        return int(row[0]) if row else None

    def _result(self, status: str, actual: SessionActual, person_id: Optional[int]) -> SessionActualReceiveResult:
        return SessionActualReceiveResult(status, actual.session_uid, actual.actual_revision, person_id)

    def receive(
        self,
        payload: Mapping[str, Any],
        idempotence_key: str,
        source_domain: str = SOURCE_DOMAIN,
        received_at: Optional[datetime] = None,
    ) -> SessionActualReceiveResult:
        self._require_schema()
        source_domain = self._key(source_domain, "source_domain", 64)
        if source_domain != SOURCE_DOMAIN:
            raise SessionActualHrPersistenceError("domaine source non supporté")
        idempotence_key = self._key(idempotence_key, "idempotence_key", 255)
        try:
            actual = SessionActual.from_payload(payload)
        except SessionActualContractError as error:
            raise SessionActualHrPersistenceError(str(error)) from error

        payload_hash = actual.payload_sha256()
        revision_key = f"{source_domain}|{actual.session_uid}|{actual.actual_revision}"
        if len(revision_key) > 255:
            raise SessionActualHrPersistenceError("revision_key invalide")
        received_sql = self._timestamp(received_at)

        exact = self._fetchone(
            f"SELECT session_uid,actual_revision,payload_sha256 FROM {INBOX_TABLE} WHERE idempotence_key=?",
            (idempotence_key,),
        )
        if exact is not None:
            if exact[0] == actual.session_uid and int(exact[1]) == actual.actual_revision and exact[2] == payload_hash:
                current = self._fetchone(f"SELECT IDpersonne FROM {WORK_TABLE} WHERE session_uid=?", (actual.session_uid,))
                person_id = int(current[0]) if current and current[0] is not None else None
                return self._result("replayed", actual, person_id)
            raise SessionActualHrPersistenceError("clé d'idempotence déjà utilisée avec un autre payload")

        try:
            current = self._fetchone(
                f"SELECT actual_uuid,actual_revision,payload_sha256,IDpersonne FROM {WORK_TABLE} WHERE session_uid=?",
                (actual.session_uid,), lock=True,
            )
            if current is not None:
                if current[0] != actual.actual_uuid:
                    raise SessionActualHrPersistenceError("l'identité du réalisé ne peut pas changer pour une séance")
                current_revision = int(current[1])
                current_person = int(current[3]) if current[3] is not None else None
                if actual.actual_revision < current_revision:
                    raise SessionActualHrPersistenceError("révision du réalisé obsolète")
                if actual.actual_revision == current_revision:
                    if current[2] == payload_hash:
                        return self._result("replayed", actual, current_person)
                    raise SessionActualHrPersistenceError("révision déjà reçue avec un autre payload")
            else:
                current_person = None

            same_revision = self._fetchone(
                f"SELECT payload_sha256 FROM {INBOX_TABLE} WHERE revision_key=?", (revision_key,)
            )
            if same_revision is not None:
                if same_revision[0] == payload_hash:
                    return self._result("replayed", actual, current_person)
                raise SessionActualHrPersistenceError("révision déjà reçue avec un autre payload")

            person_id = current_person
            if actual.session_status == "realisee":
                person_id = self.resolve_person_uid(actual.actual_staff_uid or "")
                if person_id is None:
                    raise SessionActualHrPersistenceError("UID RH inconnu: aucun salarié n'est créé automatiquement")

            values = (
                actual.actual_uuid, person_id, actual.actual_staff_uid,
                actual.assignment_date.isoformat(), actual.session_status,
                actual.actual_place_uid, actual.actual_start_time, actual.actual_end_time,
                actual.actual_duration_minutes, actual.actual_comment, actual.actual_revision,
                actual.validated_at, source_domain, payload_hash,
            )
            now = received_sql
            if current is None:
                self._execute(
                    f"""INSERT INTO {WORK_TABLE} (
                        session_uid,actual_uuid,IDpersonne,actual_staff_uid,assignment_date,
                        session_status,actual_place_uid,actual_start_time,actual_end_time,
                        actual_duration_minutes,actual_comment,actual_revision,validated_at,
                        source_domain,payload_sha256,date_creation,date_modification)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (actual.session_uid,) + values + (now, now),
                )
            else:
                cursor = self._execute(
                    f"""UPDATE {WORK_TABLE} SET
                        actual_uuid=?,IDpersonne=?,actual_staff_uid=?,assignment_date=?,session_status=?,
                        actual_place_uid=?,actual_start_time=?,actual_end_time=?,actual_duration_minutes=?,
                        actual_comment=?,actual_revision=?,validated_at=?,source_domain=?,payload_sha256=?,date_modification=?
                        WHERE session_uid=? AND actual_revision < ?""",
                    values + (now, actual.session_uid, actual.actual_revision),
                )
                if getattr(cursor, "rowcount", 1) != 1:
                    raise SessionActualHrPersistenceError("révision du réalisé modifiée concurremment")

            self._execute(
                f"""INSERT INTO {INBOX_TABLE} (
                    idempotence_key,revision_key,source_domain,contract_version,event_type,
                    actual_uuid,session_uid,actual_revision,payload_sha256,date_reception)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    idempotence_key, revision_key, source_domain, actual.contract_version,
                    actual.event_type, actual.actual_uuid, actual.session_uid,
                    actual.actual_revision, payload_hash, received_sql,
                ),
            )
            self._commit()
            return self._result("applied", actual, person_id)
        except SessionActualHrPersistenceError:
            self._rollback()
            raise
        except Exception as error:
            self._rollback()
            raise SessionActualHrTechnicalError("échec transactionnel du réalisé RH: %s" % error) from error
