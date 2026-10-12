from __future__ import annotations

from typing import Callable
from uuid import uuid4


TEAMWORKS_STRUCTURE_IDENTITY_SCHEMA_VERSION = 1


class TeamworksStructureIdentityRepository:
    """Identité stable et non secrète de la structure portée par une base Teamworks.

    La référence n'est pas dérivée du chemin local, du nom de base réseau, de l'hôte
    ni des paramètres de connexion : ces valeurs peuvent varier entre postes et, dans
    le cas historique réseau, contenir des informations d'authentification. Un UUID
    métier opaque est donc créé une seule fois dans la base active puis réutilisé.
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
            _execute(
                db,
                """
                CREATE TABLE IF NOT EXISTS tw_hr_structure_identity (
                    singleton_id INTEGER NOT NULL PRIMARY KEY,
                    structure_ref VARCHAR(40) NOT NULL,
                    schema_version INTEGER NOT NULL
                )
                """,
            )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)

    def get_or_create_structure_ref(self) -> str:
        existing = self._read_existing()
        if existing is not None:
            return existing

        structure_ref = str(uuid4())
        db = self._db_factory()
        try:
            _execute(
                db,
                """
                INSERT INTO tw_hr_structure_identity(
                    singleton_id, structure_ref, schema_version
                ) VALUES (?, ?, ?)
                """,
                (1, structure_ref, TEAMWORKS_STRUCTURE_IDENTITY_SCHEMA_VERSION),
            )
            _commit(db)
            return structure_ref
        except Exception:
            # Deux postes peuvent initialiser la même base presque simultanément.
            # Si l'autre transaction a gagné, on relit l'identité créée plutôt que
            # de fabriquer une deuxième identité logique pour la même structure.
            _rollback(db)
        finally:
            _close(db)

        existing = self._read_existing()
        if existing is not None:
            return existing
        raise RuntimeError("L'identité de la structure Teamworks n'a pas pu être initialisée.")

    def _read_existing(self) -> str | None:
        db = self._db_factory()
        try:
            row = _fetchone(
                db,
                """
                SELECT structure_ref, schema_version
                FROM tw_hr_structure_identity
                WHERE singleton_id = ?
                """,
                (1,),
            )
        finally:
            _close(db)
        if row is None:
            return None
        version = int(row[1])
        if version != TEAMWORKS_STRUCTURE_IDENTITY_SCHEMA_VERSION:
            raise RuntimeError(
                "Version de schéma de l'identité de structure non prise en charge : "
                f"{version}."
            )
        structure_ref = str(row[0]).strip()
        if not structure_ref:
            raise RuntimeError("L'identité de structure Teamworks est vide.")
        return structure_ref


def _adapt_placeholders(db, statement: str) -> str:
    if bool(getattr(db, "isNetwork", False)):
        return statement.replace("?", "%s")
    return statement.replace("%s", "?")


def _execute(db, statement: str, params: tuple = ()):
    db.cursor.execute(_adapt_placeholders(db, statement), tuple(params))
    return db.cursor


def _fetchone(db, statement: str, params: tuple = ()):
    return _execute(db, statement, params).fetchone()


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
