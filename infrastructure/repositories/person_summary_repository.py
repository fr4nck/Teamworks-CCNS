from __future__ import annotations

from typing import Callable

from application.services.person_summary import (
    PersonSummaryContract,
    PersonSummaryIdentity,
)


class GestionDBPersonSummaryRepository:
    """Lecture du résumé Personnes via GestionDB, sans dépendance wx."""

    def __init__(self, db_factory: Callable | None = None):
        if db_factory is None:
            import GestionDB
            db_factory = GestionDB.DB
        self._db_factory = db_factory

    def _fetchall(self, query: str, person_id: int):
        db = self._db_factory()
        try:
            placeholder = "%s" if db.isNetwork else "?"
            db.cursor.execute(query % placeholder, (person_id,))
            return db.cursor.fetchall()
        finally:
            db.Close()

    def get_identity(self, person_id: int):
        rows = self._fetchall(
            """SELECT civilite, nom, prenom, date_naiss, ville_naiss,
                      adresse_resid, cp_resid, ville_resid
               FROM personnes WHERE IDpersonne=%s""",
            person_id,
        )
        return PersonSummaryIdentity(*rows[0]) if rows else None

    def get_coordinates(self, person_id: int):
        rows = self._fetchall(
            """SELECT categorie, texte, intitule
               FROM coordonnees WHERE IDpersonne=%s""",
            person_id,
        )
        return [row[1] for row in rows]

    def get_contracts(self, person_id: int):
        rows = self._fetchall(
            """SELECT contrats_class.nom, contrats.date_debut, contrats.date_fin,
                      contrats.date_rupture, contrats_types.duree_indeterminee
               FROM contrats
               INNER JOIN contrats_class
                 ON contrats.IDclassification = contrats_class.IDclassification
               INNER JOIN contrats_types
                 ON contrats.IDtype = contrats_types.IDtype
               WHERE contrats.IDpersonne=%s
               ORDER BY contrats.date_fin""",
            person_id,
        )
        return [PersonSummaryContract(*row) for row in rows]
