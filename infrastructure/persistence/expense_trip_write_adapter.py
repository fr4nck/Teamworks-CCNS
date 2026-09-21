"""Adaptateur GestionDB pour les écritures de déplacements de frais."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from application.services.expense_trip_write import TripCommand, TripSnapshot


class GestionDbTripWriteAdapter:
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
    def _as_date(value) -> date:
        if isinstance(value, datetime):
            return value.date()
        if type(value) is date:
            return value
        return date.fromisoformat(str(value)[:10])

    @staticmethod
    def _postcode(value) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        return text.zfill(5) if text else ""

    @staticmethod
    def _reimbursement_id(value):
        if value in (None, 0, "", "0"):
            return None
        return int(value)

    def person_exists(self, person_id: int) -> bool:
        self.db.cursor.execute(
            "SELECT IDpersonne FROM personnes WHERE IDpersonne=%s" % self._placeholder,
            (person_id,),
        )
        return self.db.cursor.fetchone() is not None

    def read_trip(self, trip_id: int) -> TripSnapshot | None:
        self.db.cursor.execute(
            (
                "SELECT IDpersonne, date, objet, cp_depart, ville_depart, "
                "cp_arrivee, ville_arrivee, distance, aller_retour, tarif_km, "
                "IDremboursement FROM deplacements WHERE IDdeplacement=%s"
            )
            % self._placeholder,
            (trip_id,),
        )
        row = self.db.cursor.fetchone()
        if row is None:
            return None
        return TripSnapshot(
            trip_id=trip_id,
            person_id=int(row[0]),
            travel_date=self._as_date(row[1]),
            purpose=str(row[2] or "").strip(),
            departure_postcode=self._postcode(row[3]),
            departure_city=str(row[4] or "").strip(),
            arrival_postcode=self._postcode(row[5]),
            arrival_city=str(row[6] or "").strip(),
            distance=Decimal(str(row[7])),
            round_trip=(row[8] is True or str(row[8]) == "True"),
            tariff_per_km=Decimal(str(row[9])),
            reimbursement_id=self._reimbursement_id(row[10]),
        )

    @staticmethod
    def _data(command: TripCommand):
        return [
            ("date", command.travel_date.isoformat()),
            ("IDpersonne", command.person_id),
            ("objet", str(command.purpose or "").strip()),
            ("cp_depart", str(command.departure_postcode).strip()),
            ("ville_depart", str(command.departure_city).strip()),
            ("cp_arrivee", str(command.arrival_postcode).strip()),
            ("ville_arrivee", str(command.arrival_city).strip()),
            ("distance", float(command.distance)),
            ("aller_retour", str(command.round_trip)),
            ("tarif_km", float(command.tariff_per_km)),
        ]

    def insert_trip(self, command: TripCommand) -> int:
        data = self._data(command)
        data.append(("IDremboursement", 0))
        inserted = self.db.ReqInsert("deplacements", data, commit=False)
        if inserted is None:
            raise RuntimeError("La création du déplacement a échoué.")
        return int(inserted)

    def update_trip(self, command: TripCommand) -> int:
        if command.trip_id is None:
            raise RuntimeError("IDdeplacement obligatoire pour une modification.")
        assignments = ", ".join(
            "%s=%s" % (name, self._placeholder)
            for name, _value in self._data(command)
        )
        values = [value for _name, value in self._data(command)]
        values.extend((command.trip_id, command.person_id))
        self.db.cursor.execute(
            (
                "UPDATE deplacements SET %s WHERE IDdeplacement=%s AND IDpersonne=%s"
                % (assignments, self._placeholder, self._placeholder)
            ),
            tuple(values),
        )
        return int(self.db.cursor.rowcount)

    def delete_unassigned_trip(self, trip_id: int, person_id: int) -> int:
        self.db.cursor.execute(
            (
                "DELETE FROM deplacements WHERE IDdeplacement=%s AND IDpersonne=%s "
                "AND COALESCE(IDremboursement, 0)=0"
            )
            % (self._placeholder, self._placeholder),
            (trip_id, person_id),
        )
        return int(self.db.cursor.rowcount)

    def commit(self) -> None:
        self.db.Commit()

    def rollback(self) -> None:
        self.db.connexion.rollback()
