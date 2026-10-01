from __future__ import annotations

from typing import Callable


class GestionDBPersonDeleteRepository:
    """Adaptateur legacy GestionDB pour le use case de suppression d'une personne.

    L'import de GestionDB est différé afin que la couche infrastructure reste
    importable et testable sans initialiser wx.
    """

    def __init__(self, db_factory: Callable | None = None):
        if db_factory is None:
            import GestionDB
            db_factory = GestionDB.DB
        self._db_factory = db_factory

    def _exists(self, table: str, id_column: str, person_id: int) -> bool:
        db = self._db_factory()
        try:
            query = "SELECT %s FROM %s WHERE IDpersonne=%%s" % (id_column, table)
            placeholder = "%s" if db.isNetwork else "?"
            db.cursor.execute(query % placeholder, (person_id,))
            return db.cursor.fetchone() is not None
        finally:
            db.Close()

    def has_contracts(self, person_id: int) -> bool:
        return self._exists("contrats", "IDcontrat", person_id)

    def has_presences(self, person_id: int) -> bool:
        return self._exists("presences", "IDpresence", person_id)

    def has_travel(self, person_id: int) -> bool:
        return self._exists("deplacements", "IDdeplacement", person_id)

    def has_reimbursements(self, person_id: int) -> bool:
        return self._exists("remboursements", "IDremboursement", person_id)

    def delete_person_with_dependents(self, person_id: int) -> None:
        db = self._db_factory()
        try:
            for table in ("coordonnees", "diplomes", "pieces", "personnes"):
                placeholder = "%s" if db.isNetwork else "?"
                db.cursor.execute(
                    "DELETE FROM %s WHERE IDpersonne=%s" % (table, placeholder),
                    (person_id,),
                )
            db.Commit()
        except Exception:
            try:
                db.connexion.rollback()
            except Exception:
                pass
            raise
        finally:
            db.Close()
