"""Parameterized employee-details writes using an injected GestionDB connection.

Own one connection per editor, on the calling UI thread. Do not reuse
the asynchronous person reader's SQLite connection in another thread.
Only six explicitly approved columns of personnes may be updated.
"""
from __future__ import annotations

from application.services.person_generalities_write import (
    PersonDetails,
    PersonDetailsSnapshot,
)


_COLUMNS = ("nom", "prenom", "adresse_resid", "cp_resid", "ville_resid", "memo")


class GestionDbPersonDetailsWriteAdapter:
    def __init__(self, db):
        if db is None or getattr(db, "echec", 0):
            raise RuntimeError("Connexion de la fiche indisponible.")
        if getattr(db, "cursor", None) is None or getattr(db, "connexion", None) is None:
            raise RuntimeError("Connexion de la fiche incomplète.")
        self.db = db

    @property
    def _p(self) -> str:
        return "%s" if getattr(self.db, "isNetwork", False) else "?"

    @staticmethod
    def _id(value) -> int:
        if type(value) is not int or value <= 0:
            raise ValueError("Identifiant salarié invalide.")
        return value

    def load(self, person_id: int) -> PersonDetailsSnapshot | None:
        person_id = self._id(person_id)
        self.db.cursor.execute(
            "SELECT nom, prenom, adresse_resid, cp_resid, ville_resid, memo "
            "FROM personnes WHERE IDpersonne=" + self._p,
            (person_id,),
        )
        row = self.db.cursor.fetchone()
        if row is None:
            return None
        details = PersonDetails(
            last_name=row[0] or "", first_name=row[1] or "",
            address=row[2], postcode=row[3], city=row[4], memo=row[5],
        )
        return PersonDetailsSnapshot(person_id=person_id, details=details)

    def update_if_unchanged(
        self, previous: PersonDetailsSnapshot, next_details: PersonDetails
    ) -> int:
        person_id = self._id(previous.person_id)
        p = self._p
        conditions = [
            ("%s <=> %s" if getattr(self.db, "isNetwork", False) else "%s IS %s") % (column, p)
            for column in _COLUMNS
        ]
        query = (
            "UPDATE personnes SET " +
            ", ".join("%s=%s" % (column, p) for column in _COLUMNS) +
            " WHERE IDpersonne=" + p + " AND " + " AND ".join(conditions)
        )
        def values(details: PersonDetails):
            return (details.last_name, details.first_name, details.address,
                    details.postcode, details.city, details.memo)
        self.db.cursor.execute(
            query,
            values(next_details) + (person_id,) + values(previous.details),
        )
        return int(self.db.cursor.rowcount)

    def commit(self) -> None:
        self.db.connexion.commit()

    def rollback(self) -> None:
        self.db.connexion.rollback()

    def close(self) -> None:
        self.db.Close()
