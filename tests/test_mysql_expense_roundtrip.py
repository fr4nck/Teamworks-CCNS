from __future__ import annotations

import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

if os.environ.get("TEAMWORKS_MYSQL_INTEGRATION") != "1":
    pytest.skip("Recette MySQL activée uniquement dans le gate Windows dédié.", allow_module_level=True)

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TEAMWORKS) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS))

import mysql.connector  # noqa: E402
import GestionDB  # noqa: E402

from application.services.expense_reimbursement_write import (  # noqa: E402
    ReimbursementCommand,
    ReimbursementDeleteCommand,
    delete_reimbursement,
    save_reimbursement,
)
from application.services.expense_trip_write import (  # noqa: E402
    TripCommand,
    TripDeleteCommand,
    delete_trip,
    save_trip,
)
from application.services.transactional_write import WriteCode  # noqa: E402
from infrastructure.persistence.expense_reimbursement_write_adapter import (  # noqa: E402
    GestionDbReimbursementWriteAdapter,
)
from infrastructure.persistence.expense_trip_write_adapter import (  # noqa: E402
    GestionDbTripWriteAdapter,
)


HOST = os.environ.get("TEAMWORKS_MYSQL_HOST", "127.0.0.1")
PORT = int(os.environ.get("TEAMWORKS_MYSQL_PORT", "3307"))
USER = os.environ.get("TEAMWORKS_MYSQL_USER", "root")
PASSWORD = os.environ.get("TEAMWORKS_MYSQL_PASSWORD", "")
DB_NAME = "teamworks_frais_ci"


def _admin_connection():
    return mysql.connector.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        use_pure=True,
        ssl_disabled=True,
        connection_timeout=10,
    )


def _network_db():
    encoded = f"{PORT};{HOST};{USER};{PASSWORD}[RESEAU]{DB_NAME}"
    db = GestionDB.DB(nomFichier=encoded, suffixe=None)
    assert db.echec == 0, getattr(db, "erreur", None)
    assert db.isNetwork is True
    return db


@pytest.fixture()
def db():
    admin = _admin_connection()
    cursor = admin.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS \`{DB_NAME}\`")
    cursor.execute(
        f"CREATE DATABASE \`{DB_NAME}\` CHARACTER SET utf8 COLLATE utf8_unicode_ci"
    )
    cursor.close()
    admin.close()

    database = _network_db()
    database.cursor.execute(
        """
        CREATE TABLE personnes (
            IDpersonne INTEGER PRIMARY KEY
        )
        """
    )
    database.cursor.execute(
        """
        CREATE TABLE remboursements (
            IDremboursement INTEGER PRIMARY KEY AUTO_INCREMENT,
            IDpersonne INTEGER,
            date VARCHAR(10),
            montant REAL,
            listeIDdeplacement VARCHAR(300)
        )
        """
    )
    database.cursor.execute(
        """
        CREATE TABLE deplacements (
            IDdeplacement INTEGER PRIMARY KEY AUTO_INCREMENT,
            IDpersonne INTEGER,
            date VARCHAR(10),
            objet VARCHAR(100),
            cp_depart VARCHAR(5),
            ville_depart VARCHAR(200),
            cp_arrivee VARCHAR(5),
            ville_arrivee VARCHAR(200),
            distance REAL,
            aller_retour VARCHAR(5),
            tarif_km REAL,
            IDremboursement INTEGER NULL
        )
        """
    )
    database.cursor.execute("INSERT INTO personnes (IDpersonne) VALUES (12)")
    database.cursor.execute(
        """
        INSERT INTO deplacements (
            IDdeplacement, IDpersonne, date, objet,
            cp_depart, ville_depart, cp_arrivee, ville_arrivee,
            distance, aller_retour, tarif_km, IDremboursement
        ) VALUES
            (7, 12, '2026-09-10', 'Réunion', '03510', 'BRUZ', '35000', 'RENNES',
             20.0, 'False', 0.50, 0),
            (8, 12, '2026-09-11', 'Formation', '35170', 'BRUZ', '35500', 'VITRE',
             50.0, 'False', 0.40, NULL)
        """
    )
    database.Commit()

    try:
        yield database
    finally:
        database.Close()
        admin = _admin_connection()
        cursor = admin.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS \`{DB_NAME}\`")
        cursor.close()
        admin.close()


def _trip_command(**changes):
    values = dict(
        person_id=12,
        travel_date=date(2026, 9, 21),
        purpose="Réunion MySQL",
        departure_postcode="03510",
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


def _reimbursement_command(**changes):
    values = dict(
        person_id=12,
        payment_date=date(2026, 9, 30),
        amount=Decimal("30.00"),
        checked_trip_ids=(7, 8),
        unchecked_trip_ids=(),
        reimbursement_id=None,
        confirm_zero_amount=False,
    )
    values.update(changes)
    return ReimbursementCommand(**values)


def test_real_mysql_roundtrip_uses_gestiondb_network_mode(db):
    trip_port = GestionDbTripWriteAdapter(db)
    reimbursement_port = GestionDbReimbursementWriteAdapter(db)

    created_trip = save_trip(trip_port, command=_trip_command())
    assert created_trip.ok is True
    assert created_trip.value.departure_postcode == "03510"
    assert created_trip.value.reimbursement_id is None

    reimbursement = save_reimbursement(
        reimbursement_port,
        command=_reimbursement_command(),
    )
    assert reimbursement.ok is True
    reimbursement_id = reimbursement.target_id
    assert reimbursement.value.trip_ids == (7, 8)

    rows = db.connexion.cursor()
    rows.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements "
        "WHERE IDdeplacement IN (%s, %s) ORDER BY IDdeplacement",
        (7, 8),
    )
    assert rows.fetchall() == [(7, reimbursement_id), (8, reimbursement_id)]
    rows.close()

    modified_attached_trip = save_trip(
        trip_port,
        command=_trip_command(
            trip_id=7,
            purpose="Réunion MySQL modifiée",
            distance=Decimal("25"),
        ),
    )
    assert modified_attached_trip.ok is True
    assert modified_attached_trip.value.reimbursement_id == reimbursement_id

    refused_delete = delete_trip(
        trip_port,
        command=TripDeleteCommand(
            person_id=12,
            trip_id=7,
            confirmed=True,
        ),
    )
    assert refused_delete.code == WriteCode.VALIDATION_ERROR
    assert "remboursement" in refused_delete.message

    deleted_reimbursement = delete_reimbursement(
        reimbursement_port,
        command=ReimbursementDeleteCommand(
            person_id=12,
            reimbursement_id=reimbursement_id,
            confirmed=True,
            confirm_attached_trips=True,
        ),
    )
    assert deleted_reimbursement.ok is True

    rows = db.connexion.cursor()
    rows.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements "
        "WHERE IDdeplacement IN (%s, %s) ORDER BY IDdeplacement",
        (7, 8),
    )
    assert rows.fetchall() == [(7, 0), (8, 0)]
    rows.close()

    deleted_trip = delete_trip(
        trip_port,
        command=TripDeleteCommand(
            person_id=12,
            trip_id=7,
            confirmed=True,
        ),
    )
    assert deleted_trip.ok is True


def test_real_mysql_refuses_steal_and_rolls_back_parent(db):
    port = GestionDbReimbursementWriteAdapter(db)

    first = save_reimbursement(
        port,
        command=_reimbursement_command(
            amount=Decimal("10.00"),
            checked_trip_ids=(7,),
        ),
    )
    assert first.ok is True

    before = db.cursor.execute(
        "SELECT COUNT(*) FROM remboursements"
    )
    before_count = db.cursor.fetchone()[0]

    stolen = save_reimbursement(
        port,
        command=_reimbursement_command(
            amount=Decimal("20.00"),
            checked_trip_ids=(7,),
        ),
    )

    assert stolen.code == WriteCode.DATABASE_ERROR
    assert stolen.committed is False
    db.cursor.execute("SELECT COUNT(*) FROM remboursements")
    assert db.cursor.fetchone()[0] == before_count
    db.cursor.execute(
        "SELECT IDremboursement FROM deplacements WHERE IDdeplacement=%s",
        (7,),
    )
    assert db.cursor.fetchone()[0] == first.target_id


class FailingDeleteAfterDetach(GestionDbReimbursementWriteAdapter):
    def delete_reimbursement(self, reimbursement_id, person_id):
        raise RuntimeError("panne injectée après détachement MySQL")


def test_real_mysql_rolls_back_detachments_when_parent_delete_fails(db):
    base_port = GestionDbReimbursementWriteAdapter(db)
    created = save_reimbursement(
        base_port,
        command=_reimbursement_command(
            amount=Decimal("15.00"),
            checked_trip_ids=(7, 8),
        ),
    )
    assert created.ok is True

    failing = FailingDeleteAfterDetach(db)
    result = delete_reimbursement(
        failing,
        command=ReimbursementDeleteCommand(
            person_id=12,
            reimbursement_id=created.target_id,
            confirmed=True,
            confirm_attached_trips=True,
        ),
    )

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    db.cursor.execute(
        "SELECT IDremboursement FROM remboursements WHERE IDremboursement=%s",
        (created.target_id,),
    )
    assert db.cursor.fetchone() == (created.target_id,)
    db.cursor.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements "
        "WHERE IDdeplacement IN (%s, %s) ORDER BY IDdeplacement",
        (7, 8),
    )
    assert db.cursor.fetchall() == [
        (7, created.target_id),
        (8, created.target_id),
    ]
