from domain.migration.expense_inventory import RawReimbursementRow, RawTripRow
from domain.migration.expense_inventory_loader import (
    load_expense_pilot_person_ids,
    load_expense_pilot_reimbursements,
    load_expense_pilot_trips,
)


class _FakePort:
    def __init__(self, tables):
        self._tables = tables

    def fetch_rows(self, table, columns):
        rows = self._tables.get(table, [])
        for row in rows:
            yield tuple(row[c] for c in columns)


def test_load_person_ids():
    port = _FakePort({"personnes": [{"IDpersonne": 12}, {"IDpersonne": 13}]})

    assert load_expense_pilot_person_ids(port) == (12, 13)


def test_load_trips_maps_columns_in_order():
    port = _FakePort(
        {
            "deplacements": [
                {
                    "IDdeplacement": 7,
                    "IDpersonne": 12,
                    "date": "2026-09-10",
                    "cp_depart": "03510",
                    "cp_arrivee": "35000",
                    "distance": 20.0,
                    "tarif_km": 0.5,
                    "aller_retour": "0",
                    "IDremboursement": 3,
                }
            ]
        }
    )

    trips = load_expense_pilot_trips(port)

    assert trips == (
        RawTripRow(
            trip_id=7,
            person_id=12,
            travel_date="2026-09-10",
            departure_postcode="03510",
            arrival_postcode="35000",
            distance=20.0,
            tariff_per_km=0.5,
            round_trip="0",
            reimbursement_id=3,
        ),
    )


def test_load_reimbursements_maps_columns_in_order():
    port = _FakePort(
        {
            "remboursements": [
                {
                    "IDremboursement": 3,
                    "IDpersonne": 12,
                    "date": "2026-09-30",
                    "montant": 10.0,
                    "listeIDdeplacement": "7",
                }
            ]
        }
    )

    reimbursements = load_expense_pilot_reimbursements(port)

    assert reimbursements == (
        RawReimbursementRow(
            reimbursement_id=3,
            person_id=12,
            payment_date="2026-09-30",
            amount=10.0,
            legacy_trip_list="7",
        ),
    )


def test_load_from_empty_tables_returns_empty_tuples():
    port = _FakePort({})

    assert load_expense_pilot_person_ids(port) == ()
    assert load_expense_pilot_trips(port) == ()
    assert load_expense_pilot_reimbursements(port) == ()
