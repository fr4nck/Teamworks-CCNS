"""Adaptateur GestionDB pour les remboursements de frais."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from application.services.expense_reimbursement_write import (
    ReimbursementSnapshot,
)


class GestionDbReimbursementWriteAdapter:
    def __init__(self, db):
        if db is None:
            raise RuntimeError("Connexion GestionDB absente.")
        if getattr(db, "echec", 0):
            raise RuntimeError("Connexion GestionDB indisponible.")
        if getattr(db, "cursor", None) is None or getattr(db, "connexion", None) is None:
            raise RuntimeError("Connexion GestionDB incomplète.")
        self.db = db

    @property
    def _placeholder(self) -> str:
        return "%s" if getattr(self.db, "isNetwork", False) else "?"

    @staticmethod
    def _as_date(value):
        if isinstance(value, datetime):
            return value.date()
        if type(value) is date:
            return value
        return date.fromisoformat(str(value)[:10])

    def person_exists(self, person_id: int) -> bool:
        self.db.cursor.execute(
            "SELECT IDpersonne FROM personnes WHERE IDpersonne=%s" % self._placeholder,
            (person_id,),
        )
        return self.db.cursor.fetchone() is not None

    def reimbursement_exists(self, reimbursement_id: int) -> bool:
        self.db.cursor.execute(
            "SELECT IDremboursement FROM remboursements "
            "WHERE IDremboursement=%s" % self._placeholder,
            (reimbursement_id,),
        )
        return self.db.cursor.fetchone() is not None

    def insert_reimbursement(
        self, person_id: int, payment_date: date, amount: Decimal
    ) -> int:
        inserted = self.db.ReqInsert(
            "remboursements",
            [
                ("date", payment_date.isoformat()),
                ("IDpersonne", person_id),
                ("montant", float(amount)),
                ("listeIDdeplacement", ""),
            ],
            commit=False,
        )
        if inserted is None:
            raise RuntimeError("La création du remboursement a échoué.")
        return int(inserted)

    def update_reimbursement(
        self,
        reimbursement_id: int,
        person_id: int,
        payment_date: date,
        amount: Decimal,
    ) -> int:
        self.db.cursor.execute(
            "UPDATE remboursements SET date=%s, IDpersonne=%s, montant=%s "
            "WHERE IDremboursement=%s"
            % (
                self._placeholder,
                self._placeholder,
                self._placeholder,
                self._placeholder,
            ),
            (
                payment_date.isoformat(),
                person_id,
                float(amount),
                reimbursement_id,
            ),
        )
        return int(self.db.cursor.rowcount)

    def read_trip_assignment(
        self, trip_id: int, person_id: int
    ) -> tuple[bool, int | None]:
        self.db.cursor.execute(
            "SELECT IDremboursement FROM deplacements "
            "WHERE IDdeplacement=%s AND IDpersonne=%s"
            % (self._placeholder, self._placeholder),
            (trip_id, person_id),
        )
        row = self.db.cursor.fetchone()
        if row is None:
            return False, None
        return True, row[0]

    def assign_trip(self, trip_id: int, reimbursement_id: int) -> int:
        self.db.cursor.execute(
            "UPDATE deplacements SET IDremboursement=%s WHERE IDdeplacement=%s"
            % (self._placeholder, self._placeholder),
            (reimbursement_id, trip_id),
        )
        return int(self.db.cursor.rowcount)

    def detach_trip_if_owned(self, trip_id: int, reimbursement_id: int) -> int:
        self.db.cursor.execute(
            "UPDATE deplacements SET IDremboursement=0 "
            "WHERE IDdeplacement=%s AND IDremboursement=%s"
            % (self._placeholder, self._placeholder),
            (trip_id, reimbursement_id),
        )
        return int(self.db.cursor.rowcount)

    def list_trip_ids(
        self, person_id: int, reimbursement_id: int
    ) -> tuple[int, ...]:
        self.db.cursor.execute(
            "SELECT IDdeplacement FROM deplacements "
            "WHERE IDpersonne=%s AND IDremboursement=%s ORDER BY IDdeplacement"
            % (self._placeholder, self._placeholder),
            (person_id, reimbursement_id),
        )
        return tuple(int(row[0]) for row in self.db.cursor.fetchall())

    def update_legacy_trip_list(
        self, reimbursement_id: int, trip_ids_text: str
    ) -> int:
        self.db.cursor.execute(
            "UPDATE remboursements SET listeIDdeplacement=%s "
            "WHERE IDremboursement=%s"
            % (self._placeholder, self._placeholder),
            (trip_ids_text, reimbursement_id),
        )
        return int(self.db.cursor.rowcount)

    def read_reimbursement(
        self, reimbursement_id: int
    ) -> ReimbursementSnapshot | None:
        self.db.cursor.execute(
            "SELECT IDpersonne, date, montant FROM remboursements "
            "WHERE IDremboursement=%s" % self._placeholder,
            (reimbursement_id,),
        )
        row = self.db.cursor.fetchone()
        if row is None:
            return None
        person_id = int(row[0])
        return ReimbursementSnapshot(
            reimbursement_id=reimbursement_id,
            person_id=person_id,
            payment_date=self._as_date(row[1]),
            amount=Decimal(str(row[2])),
            trip_ids=self.list_trip_ids(person_id, reimbursement_id),
        )

    def commit(self) -> None:
        self.db.Commit()

    def rollback(self) -> None:
        self.db.connexion.rollback()
