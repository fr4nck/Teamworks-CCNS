"""Tests SQLite du contrat métier Frais / déplacements."""

from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal

from application.services.expense_trip_write import (
    TripCommand,
    TripDeleteCommand,
    TripSnapshot,
    delete_trip,
    save_trip,
)
from application.services.transactional_write import WriteCode
from infrastructure.persistence.expense_trip_write_adapter import (
    GestionDbTripWriteAdapter,
)


class SqliteGestionDbCompat:
    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.echec = 0
        self.isNetwork = False
        self.commit_count = 0
        self.cursor.executescript(
            """
            CREATE TABLE personnes (
                IDpersonne INTEGER PRIMARY KEY
            );
            CREATE TABLE deplacements (
                IDdeplacement INTEGER PRIMARY KEY AUTOINCREMENT,
                IDpersonne INTEGER,
                date TEXT,
                objet TEXT,
                cp_depart TEXT,
                ville_depart TEXT,
                cp_arrivee TEXT,
                ville_arrivee TEXT,
                distance REAL,
                aller_retour TEXT,
                tarif_km REAL,
                IDremboursement INTEGER
            );
            INSERT INTO personnes VALUES (1);
            INSERT INTO deplacements VALUES (
                7, 1, '2026-09-10', 'Réunion', '35170', 'BRUZ',
                '35000', 'RENNES', 20.0, 'False', 0.50, 0
            );
            INSERT INTO deplacements VALUES (
                8, 1, '2026-09-11', 'Formation', '35170', 'BRUZ',
                '35500', 'VITRE', 100.0, 'True', 0.40, 3
            );
            """
        )
        self.connexion.commit()

    def ReqInsert(self, table, values, commit=True):
        columns = [name for name, _value in values]
        payload = [value for _name, value in values]
        placeholders = ", ".join("?" for _value in payload)
        self.cursor.execute(
            "INSERT INTO %s (%s) VALUES (%s)"
            % (table, ", ".join(columns), placeholders),
            payload,
        )
        inserted = int(self.cursor.lastrowid)
        if commit:
            self.Commit()
        return inserted

    def Commit(self):
        self.commit_count += 1
        self.connexion.commit()


def _command(**changes):
    values = dict(
        person_id=1,
        travel_date=date(2026, 9, 20),
        purpose="Réunion équipe",
        departure_postcode="35170",
        departure_city="BRUZ",
        arrival_postcode="35240",
        arrival_city="RETIERS",
        distance=Decimal("42.5"),
        round_trip=False,
        tariff_per_km=Decimal("0.50"),
        trip_id=None,
        confirm_empty_purpose=False,
        confirm_zero_distance=False,
        confirm_zero_tariff=False,
    )
    values.update(changes)
    return TripCommand(**values)


def test_create_trip_starts_unassigned_and_is_read_back():
    db = SqliteGestionDbCompat()
    port = GestionDbTripWriteAdapter(db)

    result = save_trip(port, command=_command())

    assert result.ok is True
    assert result.code == WriteCode.OK
    assert result.committed is True
    assert result.target_id == 9
    assert result.value.reimbursement_id is None
    assert result.value.distance == Decimal("42.5")
    assert result.value.tariff_per_km == Decimal("0.5")
    assert db.commit_count == 1
    assert db.connexion.execute(
        """
        SELECT IDpersonne, date, objet, cp_depart, ville_depart,
               cp_arrivee, ville_arrivee, distance, aller_retour,
               tarif_km, IDremboursement
        FROM deplacements WHERE IDdeplacement=9
        """
    ).fetchone() == (
        1,
        "2026-09-20",
        "Réunion équipe",
        "35170",
        "BRUZ",
        "35240",
        "RETIERS",
        42.5,
        "False",
        0.5,
        0,
    )


def test_modify_attached_trip_preserves_reimbursement_assignment():
    db = SqliteGestionDbCompat()
    port = GestionDbTripWriteAdapter(db)

    result = save_trip(
        port,
        command=_command(
            trip_id=8,
            travel_date=date(2026, 9, 12),
            purpose="Formation modifiée",
            arrival_postcode="35000",
            arrival_city="RENNES",
            distance=Decimal("110"),
            round_trip=True,
            tariff_per_km=Decimal("0.45"),
        ),
    )

    assert result.ok is True
    assert result.value.reimbursement_id == 3
    assert db.commit_count == 1
    assert db.connexion.execute(
        "SELECT objet, distance, aller_retour, tarif_km, IDremboursement "
        "FROM deplacements WHERE IDdeplacement=8"
    ).fetchone() == ("Formation modifiée", 110.0, "True", 0.45, 3)


def test_empty_purpose_requires_explicit_confirmation():
    db = SqliteGestionDbCompat()
    port = GestionDbTripWriteAdapter(db)

    denied = save_trip(port, command=_command(purpose=""))
    allowed = save_trip(
        port,
        command=_command(purpose="", confirm_empty_purpose=True),
    )

    assert denied.code == WriteCode.VALIDATION_ERROR
    assert "sans objet" in denied.message
    assert allowed.ok is True


def test_zero_distance_and_zero_tariff_each_require_confirmation():
    db = SqliteGestionDbCompat()
    port = GestionDbTripWriteAdapter(db)

    distance_denied = save_trip(
        port,
        command=_command(distance=Decimal("0")),
    )
    tariff_denied = save_trip(
        port,
        command=_command(tariff_per_km=Decimal("0")),
    )
    allowed = save_trip(
        port,
        command=_command(
            distance=Decimal("0"),
            tariff_per_km=Decimal("0"),
            confirm_zero_distance=True,
            confirm_zero_tariff=True,
        ),
    )

    assert distance_denied.code == WriteCode.VALIDATION_ERROR
    assert "0 km" in distance_denied.message
    assert tariff_denied.code == WriteCode.VALIDATION_ERROR
    assert "0 €" in tariff_denied.message
    assert allowed.ok is True


def test_postcodes_and_non_negative_numbers_are_validated_in_business_layer():
    db = SqliteGestionDbCompat()
    port = GestionDbTripWriteAdapter(db)

    bad_postcode = save_trip(
        port,
        command=_command(departure_postcode="35A70"),
    )
    bad_distance = save_trip(
        port,
        command=_command(distance=Decimal("-1")),
    )
    bad_tariff = save_trip(
        port,
        command=_command(tariff_per_km=Decimal("-0.1")),
    )

    assert bad_postcode.code == WriteCode.VALIDATION_ERROR
    assert "code postal de départ" in bad_postcode.message
    assert bad_distance.code == WriteCode.VALIDATION_ERROR
    assert bad_tariff.code == WriteCode.VALIDATION_ERROR
    assert db.commit_count == 0


def test_delete_free_trip_requires_confirmation_then_confirms_absence():
    db = SqliteGestionDbCompat()
    port = GestionDbTripWriteAdapter(db)

    denied = delete_trip(
        port,
        command=TripDeleteCommand(person_id=1, trip_id=7, confirmed=False),
    )
    assert denied.code == WriteCode.VALIDATION_ERROR
    assert db.commit_count == 0

    result = delete_trip(
        port,
        command=TripDeleteCommand(person_id=1, trip_id=7, confirmed=True),
    )

    assert result.ok is True
    assert result.committed is True
    assert db.commit_count == 1
    assert db.connexion.execute(
        "SELECT IDdeplacement FROM deplacements WHERE IDdeplacement=7"
    ).fetchone() is None


def test_delete_attached_trip_is_refused_without_write():
    db = SqliteGestionDbCompat()
    port = GestionDbTripWriteAdapter(db)

    result = delete_trip(
        port,
        command=TripDeleteCommand(person_id=1, trip_id=8, confirmed=True),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "remboursement n°3" in result.message
    assert result.committed is False
    assert db.commit_count == 0
    assert db.connexion.execute(
        "SELECT IDremboursement FROM deplacements WHERE IDdeplacement=8"
    ).fetchone() == (3,)


class ConcurrentAssignmentAdapter(GestionDbTripWriteAdapter):
    def __init__(self, db):
        super().__init__(db)
        self.raced = False

    def delete_unassigned_trip(self, trip_id, person_id):
        self.raced = True
        return 0

    def read_trip(self, trip_id):
        snapshot = super().read_trip(trip_id)
        if self.raced and snapshot is not None:
            return TripSnapshot(
                trip_id=snapshot.trip_id,
                person_id=snapshot.person_id,
                travel_date=snapshot.travel_date,
                purpose=snapshot.purpose,
                departure_postcode=snapshot.departure_postcode,
                departure_city=snapshot.departure_city,
                arrival_postcode=snapshot.arrival_postcode,
                arrival_city=snapshot.arrival_city,
                distance=snapshot.distance,
                round_trip=snapshot.round_trip,
                tariff_per_km=snapshot.tariff_per_km,
                reimbursement_id=99,
            )
        return snapshot


def test_delete_refuses_concurrent_reimbursement_assignment():
    db = SqliteGestionDbCompat()
    port = ConcurrentAssignmentAdapter(db)

    result = delete_trip(
        port,
        command=TripDeleteCommand(person_id=1, trip_id=7, confirmed=True),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "entre-temps" in result.message
    assert result.committed is False
    assert db.commit_count == 0


class FailingUpdateAdapter(GestionDbTripWriteAdapter):
    def update_trip(self, command):
        super().update_trip(command)
        raise RuntimeError("panne injectée pendant UPDATE")


def test_update_failure_rolls_back_trip_and_keeps_reimbursement():
    db = SqliteGestionDbCompat()
    before = db.connexion.execute(
        "SELECT date, objet, distance, tarif_km, IDremboursement "
        "FROM deplacements WHERE IDdeplacement=8"
    ).fetchone()
    port = FailingUpdateAdapter(db)

    result = save_trip(
        port,
        command=_command(
            trip_id=8,
            purpose="Ne doit pas rester",
            distance=Decimal("999"),
        ),
    )

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert db.commit_count == 0
    assert db.connexion.execute(
        "SELECT date, objet, distance, tarif_km, IDremboursement "
        "FROM deplacements WHERE IDdeplacement=8"
    ).fetchone() == before


class BrokenReadbackAdapter(GestionDbTripWriteAdapter):
    def __init__(self, db):
        super().__init__(db)
        self.after_commit = False

    def commit(self):
        super().commit()
        self.after_commit = True

    def read_trip(self, trip_id):
        if self.after_commit:
            raise RuntimeError("readback déplacement cassé")
        return super().read_trip(trip_id)


def test_trip_readback_failure_is_distinguished_after_commit():
    db = SqliteGestionDbCompat()
    port = BrokenReadbackAdapter(db)

    result = save_trip(port, command=_command())

    assert result.code == WriteCode.READBACK_ERROR
    assert result.ok is False
    assert result.committed is True
    assert db.commit_count == 1


def test_common_trip_boundary_has_no_wx_or_qt_import():
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "application"
        / "services"
        / "expense_trip_write.py"
    ).read_text(encoding="utf-8")
    assert "import wx" not in source
    assert "from wx" not in source
    assert "PySide6" not in source
