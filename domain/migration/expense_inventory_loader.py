"""Chargement des lignes du pilote Frais depuis un port d'inventaire.

Reste moteur-indépendant : ne connaît que LegacyDatabasePort.fetch_rows.
"""

from __future__ import annotations

from domain.migration.expense_inventory import RawReimbursementRow, RawTripRow
from domain.migration.inventory_port import LegacyDatabasePort

PERSON_COLUMNS: tuple[str, ...] = ("IDpersonne",)

TRIP_COLUMNS: tuple[str, ...] = (
    "IDdeplacement",
    "IDpersonne",
    "date",
    "cp_depart",
    "cp_arrivee",
    "distance",
    "tarif_km",
    "aller_retour",
    "IDremboursement",
)

REIMBURSEMENT_COLUMNS: tuple[str, ...] = (
    "IDremboursement",
    "IDpersonne",
    "date",
    "montant",
    "listeIDdeplacement",
)


def load_expense_pilot_person_ids(port: LegacyDatabasePort) -> tuple[object, ...]:
    return tuple(row[0] for row in port.fetch_rows("personnes", PERSON_COLUMNS))


def load_expense_pilot_trips(port: LegacyDatabasePort) -> tuple[RawTripRow, ...]:
    rows = port.fetch_rows("deplacements", TRIP_COLUMNS)
    return tuple(
        RawTripRow(
            trip_id=row[0],
            person_id=row[1],
            travel_date=row[2],
            departure_postcode=row[3],
            arrival_postcode=row[4],
            distance=row[5],
            tariff_per_km=row[6],
            round_trip=row[7],
            reimbursement_id=row[8],
        )
        for row in rows
    )


def load_expense_pilot_reimbursements(
    port: LegacyDatabasePort,
) -> tuple[RawReimbursementRow, ...]:
    rows = port.fetch_rows("remboursements", REIMBURSEMENT_COLUMNS)
    return tuple(
        RawReimbursementRow(
            reimbursement_id=row[0],
            person_id=row[1],
            payment_date=row[2],
            amount=row[3],
            legacy_trip_list=row[4],
        )
        for row in rows
    )
