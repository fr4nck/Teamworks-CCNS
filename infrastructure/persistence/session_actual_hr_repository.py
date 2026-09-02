"""Persistance du contrat ``session-actual/1`` dans le domaine RH.

Le dépôt repose sur ``GestionDB`` par défaut mais n'en dépend pas à l'import :
les tests et autres environnements peuvent injecter une fabrique de connexion.
Les tables sont additives et n'écrivent jamais dans la paie ni dans le planning
prévisionnel historique.
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
    """Conflit, mapping manquant ou persistance impossible du réalisé RH."""


@dataclass(frozen=True, slots=True)
class SessionActualReceiveResult:
    status: str
    session_uid: str
    actual_revision: int
    person_id: Optional[int]


class SessionActualHrRepository:
    """Inbox idempotente et journal RH du réalisé validé."""

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

    def close(self) -> None:
        if self._db is not None:
            close = getattr(self._db, "Close", None)
            if callable(close):
                close()
            self._db = None

    def _execute(self, sql: str, params: tuple[Any, ...] = ()):
        cursor = getattr(self.db, "cursor", None)
        if cursor is None:
            raise SessionActualHrPersistenceError("La connexion ne fournit pas de curseur SQL")
        if getattr(self.db, "isNetwork", False):
            sql = sql.replace("?", "%s")
        return cursor.execute(sql, params)

    def _fetchone(self, sql: str, params: tuple[Any, ...] = ()):
        self._execute(sql, params)
        return self.db.cursor.fetchone()

    def _commit(self) -> None:
        commit = getattr(self.db, "Commit", None)
        if callable(commit):
            commit()
            return
        connection = getattr(self.db, "connexion", None) or getattr(self.db, "conn", None)
        if connection is None:
            raise SessionActualHrPersistenceError("La connexion ne permet pas le commit")
        connection.commit()

    def _rollback(self) -> None:
        rollback = getattr(self.db, "Rollback", None)
        if callable(rollback):
            rollback()
            return
        connection = getattr(self.db, "connexion", None) or getattr(self.db, "conn", None)
        if connection is None:
            raise SessionActualHrPersistenceError("La connexion ne permet pas le rollback")
        connection.rollback()

    def _table_exists(self, table_name: str) -> bool:
        checker = getattr(self.db, "IsTableExists", None)
        if callable(checker):
            return bool(checker(table_name))
        if getattr(self.db, "isNetwork", False):
            row = self._fetchone("SHOW TABLES LIKE ?", (table_name,))
            return row is not None
        row = self._fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return row is not None

    @staticmethod
    def _schema_statements(network: bool) -> tuple[str, ...]:
        auto_id = "INTEGER PRIMARY KEY AUTO_INCREMENT" if network else "INTEGER PRIMARY KEY AUTOINCREMENT"
        return (
            f"""CREATE TABLE IF NOT EXISTS {MAPPING_TABLE} (
                IDmapping {auto_id},
                person_uid VARCHAR(100) NOT NULL UNIQUE,
                IDpersonne INTEGER NOT NULL UNIQUE,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_modification DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            f"""CREATE TABLE IF NOT EXISTS {INBOX_TABLE} (
                IDinbox {auto_id},
                idempotence_key VARCHAR(255) NOT NULL UNIQUE,
                revision_key VARCHAR(255) NOT NULL UNIQUE,
                source_domain VARCHAR(64) NOT NULL,
                contract_version VARCHAR(64) NOT NULL,
                event_type VARCHAR(64) NOT NULL,
                actual_uuid VARCHAR(64) NOT NULL,
                session_uid VARCHAR(128) NOT NULL,
                actual_revision INTEGER NOT NULL,
                payload_sha256 VARCHAR(64) NOT NULL,
                date_reception DATETIME NOT NULL
            )""",
            f"""CREATE TABLE IF NOT EXISTS {WORK_TABLE} (
                IDactual {auto_id},
                session_uid VARCHAR(128) NOT NULL UNIQUE,
                actual_uuid VARCHAR(64) NOT NULL UNIQUE,
                IDpersonne INTEGER,
                actual_staff_uid VARCHAR(100),
                assignment_date DATE NOT NULL,
                session_status VARCHAR(32) NOT NULL,
                actual_place_uid VARCHAR(128),
                actual_start_time VARCHAR(5),
                actual_end_time VARCHAR(5),
                actual_duration_minutes INTEGER,
                actual_comment TEXT,
                actual_revision INTEGER NOT NULL,
                validated_at VARCHAR(64) NOT NULL,
                source_domain VARCHAR(64) NOT NULL,
                payload_sha256 VARCHAR(64) NOT NULL,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_modification DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
        )

    def ensure_schema(self, apply: bool = False) -> tuple[str, ...]:
        """Vérifie ou crée explicitement les trois tables additives.

        Aucun schéma n'est créé au simple import ou à l'instanciation du dépôt.
        """
        missing = tuple(
            table_name
            for table_name in (MAPPING_TABLE, INBOX_TABLE, WORK_TABLE)
            if not self._table_exists(table_name)
        )
        if not missing or not apply:
            return missing

        try:
            for statement in self._schema_statements(bool(getattr(self.db, "isNetwork", False))):
                self._execute(statement)
            self._commit()
        except Exception:
            self._rollback()
            raise

        remaining = tuple(
            table_name
            for table_name in (MAPPING_TABLE, INBOX_TABLE, WORK_TABLE)
            if not self._table_exists(table_name)
        )
        if remaining:
            raise SessionActualHrPersistenceError(
                "Schéma du réalisé RH incomplet: %s" % ", ".join(remaining)
            )
        return ()

    def _require_schema(self) -> None:
        missing = self.ensure_schema(apply=False)
        if missing:
            raise SessionActualHrPersistenceError(
                "Tables du réalisé RH absentes: %s" % ", ".join(missing)
            )

    @staticmethod
    def _required_key(value: Any, field_name: str, maximum: int) -> str:
        if not isinstance(value, str) or not (normalized := value.strip()):
            raise SessionActualHrPersistenceError(f"{field_name} obligatoire")
        if len(normalized) > maximum or any(ord(character) < 32 for character in normalized):
            raise SessionActualHrPersistenceError(f"{field_name} invalide")
        return normalized

    def register_person_uid(self, person_uid: str, person_id: int) -> int:
        """Associe explicitement un UID RH stable à une personne Teamworks existante."""
        self._require_schema()
        person_uid = self._required_key(person_uid, "person_uid", 100)
        try:
            person_id = int(person_id)
        except (TypeError, ValueError) as error:
            raise SessionActualHrPersistenceError("IDpersonne invalide") from error
        if person_id < 1:
            raise SessionActualHrPersistenceError("IDpersonne invalide")

        person = self._fetchone("SELECT IDpersonne FROM personnes WHERE IDpersonne=?", (person_id,))
        if person is None:
            raise SessionActualHrPersistenceError("Personne Teamworks introuvable")

        by_uid = self._fetchone(
            f"SELECT IDpersonne, is_active FROM {MAPPING_TABLE} WHERE person_uid=?",
            (person_uid,),
        )
        if by_uid is not None:
            if int(by_uid[0]) != person_id:
                raise SessionActualHrPersistenceError("Cet UID RH est déjà associé à une autre personne")
            if int(by_uid[1]) == 1:
                return person_id
            self._execute(
                f"UPDATE {MAPPING_TABLE} SET is_active=1, date_modification=CURRENT_TIMESTAMP WHERE person_uid=?",
                (person_uid,),
            )
            self._commit()
            return person_id

        by_person = self._fetchone(
            f"SELECT person_uid FROM {MAPPING_TABLE} WHERE IDpersonne=?",
            (person_id,),
        )
        if by_person is not None:
            raise SessionActualHrPersistenceError("Cette personne possède déjà un UID RH stable")

        try:
            self._execute(
                f"INSERT INTO {MAPPING_TABLE} (person_uid, IDpersonne, is_active) VALUES (?, ?, 1)",
                (person_uid, person_id),
            )
            self._commit()
        except Exception:
            self._rollback()
            raise
        return person_id

    def resolve_person_uid(self, person_uid: str) -> Optional[int]:
        self._require_schema()
        person_uid = self._required_key(person_uid, "actual_staff_uid", 100)
        row = self._fetchone(
            f"SELECT IDpersonne FROM {MAPPING_TABLE} WHERE person_uid=? AND is_active=1",
            (person_uid,),
        )
        return int(row[0]) if row is not None else None

    def receive(
        self,
        payload: Mapping[str, Any],
        idempotence_key: str,
        source_domain: str = SOURCE_DOMAIN,
        received_at: Optional[datetime] = None,
    ) -> SessionActualReceiveResult:
        """Applique atomiquement un réalisé validé au journal RH.

        Le planning, les contrats et les données de paie ne sont jamais écrits.
        """
        self._require_schema()
        source_domain = self._required_key(source_domain, "source_domain", 64)
        if source_domain != SOURCE_DOMAIN:
            raise SessionActualHrPersistenceError("domaine source non supporté")
        idempotence_key = self._required_key(idempotence_key, "idempotence_key", 255)

        try:
            actual = SessionActual.from_payload(payload)
        except SessionActualContractError as error:
            raise SessionActualHrPersistenceError(str(error)) from error

        payload_hash = actual.payload_sha256()
        revision_key = f"{source_domain}|{actual.session_uid}|{actual.actual_revision}"
        if len(revision_key) > 255:
            raise SessionActualHrPersistenceError("revision_key invalide")
        received_at = received_at or datetime.now()
        if not isinstance(received_at, datetime):
            raise SessionActualHrPersistenceError("date_reception invalide")
        received_at_sql = received_at.strftime("%Y-%m-%d %H:%M:%S")

        # Un replay portant exactement la même clé de livraison reste un no-op
        # réussi, y compris si une révision plus récente a été appliquée depuis.
        inbox_by_key = self._fetchone(
            f"SELECT session_uid, actual_revision, payload_sha256 FROM {INBOX_TABLE} WHERE idempotence_key=?",
            (idempotence_key,),
        )
        if inbox_by_key is not None:
            if (
                inbox_by_key[0] == actual.session_uid
                and int(inbox_by_key[1]) == actual.actual_revision
                and inbox_by_key[2] == payload_hash
            ):
                current_person = self._fetchone(
                    f"SELECT IDpersonne FROM {WORK_TABLE} WHERE session_uid=?",
                    (actual.session_uid,),
                )
                return SessionActualReceiveResult(
                    "replayed",
                    actual.session_uid,
                    actual.actual_revision,
                    int(current_person[0])
                    if current_person is not None and current_person[0] is not None
                    else None,
                )
            raise SessionActualHrPersistenceError("clé d'idempotence déjà utilisée avec un autre payload")

        # Le journal courant arbitre ensuite la fraîcheur. Une ancienne révision
        # renvoyée sous une nouvelle clé n'est pas un replay : elle est obsolète.
        current = self._fetchone(
            f"SELECT actual_uuid, actual_revision, payload_sha256, IDpersonne FROM {WORK_TABLE} WHERE session_uid=?",
            (actual.session_uid,),
        )
        if current is not None:
            if current[0] != actual.actual_uuid:
                raise SessionActualHrPersistenceError("l'identité du réalisé ne peut pas changer pour une séance")
            current_revision = int(current[1])
            if actual.actual_revision < current_revision:
                raise SessionActualHrPersistenceError("révision du réalisé obsolète")
            if actual.actual_revision == current_revision:
                if current[2] == payload_hash:
                    return SessionActualReceiveResult(
                        "replayed",
                        actual.session_uid,
                        actual.actual_revision,
                        int(current[3]) if current[3] is not None else None,
                    )
                raise SessionActualHrPersistenceError("révision courante incompatible avec le payload reçu")

        # Pour une révision qui n'est pas obsolète, l'inbox protège aussi contre
        # une seconde livraison divergente de la même révision.
        inbox_by_revision = self._fetchone(
            f"SELECT payload_sha256 FROM {INBOX_TABLE} WHERE revision_key=?",
            (revision_key,),
        )
        if inbox_by_revision is not None:
            if inbox_by_revision[0] == payload_hash:
                current_person = self._fetchone(
                    f"SELECT IDpersonne FROM {WORK_TABLE} WHERE session_uid=?",
                    (actual.session_uid,),
                )
                return SessionActualReceiveResult(
                    "replayed",
                    actual.session_uid,
                    actual.actual_revision,
                    int(current_person[0])
                    if current_person is not None and current_person[0] is not None
                    else None,
                )
            raise SessionActualHrPersistenceError("révision déjà reçue avec un autre payload")

        person_id: Optional[int] = None
        if actual.session_status == "realisee":
            person_id = self.resolve_person_uid(actual.actual_staff_uid or "")
            if person_id is None:
                raise SessionActualHrPersistenceError("UID RH inconnu: aucun salarié n'est créé automatiquement")
        elif current is not None and current[3] is not None:
            person_id = int(current[3])

        work_values = (
            actual.actual_uuid,
            person_id,
            actual.actual_staff_uid,
            actual.assignment_date.isoformat(),
            actual.session_status,
            actual.actual_place_uid,
            actual.actual_start_time,
            actual.actual_end_time,
            actual.actual_duration_minutes,
            actual.actual_comment,
            actual.actual_revision,
            actual.validated_at,
            source_domain,
            payload_hash,
        )

        try:
            if current is None:
                self._execute(
                    f"""INSERT INTO {WORK_TABLE} (
                        session_uid, actual_uuid, IDpersonne, actual_staff_uid,
                        assignment_date, session_status, actual_place_uid,
                        actual_start_time, actual_end_time, actual_duration_minutes,
                        actual_comment, actual_revision, validated_at, source_domain,
                        payload_sha256
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (actual.session_uid,) + work_values,
                )
            else:
                self._execute(
                    f"""UPDATE {WORK_TABLE} SET
                        actual_uuid=?, IDpersonne=?, actual_staff_uid=?, assignment_date=?,
                        session_status=?, actual_place_uid=?, actual_start_time=?,
                        actual_end_time=?, actual_duration_minutes=?, actual_comment=?,
                        actual_revision=?, validated_at=?, source_domain=?, payload_sha256=?,
                        date_modification=CURRENT_TIMESTAMP
                    WHERE session_uid=?""",
                    work_values + (actual.session_uid,),
                )

            self._execute(
                f"""INSERT INTO {INBOX_TABLE} (
                    idempotence_key, revision_key, source_domain, contract_version,
                    event_type, actual_uuid, session_uid, actual_revision,
                    payload_sha256, date_reception
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    idempotence_key,
                    revision_key,
                    source_domain,
                    actual.contract_version,
                    actual.event_type,
                    actual.actual_uuid,
                    actual.session_uid,
                    actual.actual_revision,
                    payload_hash,
                    received_at_sql,
                ),
            )
            self._commit()
        except Exception:
            self._rollback()
            raise

        return SessionActualReceiveResult("applied", actual.session_uid, actual.actual_revision, person_id)
