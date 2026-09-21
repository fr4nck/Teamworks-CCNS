from datetime import date
from decimal import Decimal

from domain.migration.expense_pilot import (
    CanonicalReimbursement,
    CanonicalTrip,
    LegacyReimbursement,
    LegacyTrip,
    normalize_reimbursement_id,
    parse_legacy_trip_list,
    reconcile_expenses,
)


def _source_trip(trip_id=7, reimbursement_id=3, **changes):
    values = dict(
        trip_id=trip_id,
        person_id=12,
        travel_date=date(2026, 9, 10),
        purpose="Réunion",
        departure_postcode="03510",
        departure_city="BRUZ",
        arrival_postcode="35000",
        arrival_city="RENNES",
        distance=Decimal("20.0"),
        round_trip=False,
        tariff_per_km=Decimal("0.50"),
        reimbursement_id=reimbursement_id,
    )
    values.update(changes)
    return LegacyTrip(**values)


def _dest_trip(source=None, **changes):
    source = source or _source_trip()
    values = dict(
        source_trip_id=source.trip_id,
        destination_id=f"trip-{source.trip_id}",
        person_id=source.person_id,
        travel_date=source.travel_date,
        purpose=source.purpose,
        departure_postcode=source.departure_postcode,
        departure_city=source.departure_city,
        arrival_postcode=source.arrival_postcode,
        arrival_city=source.arrival_city,
        distance=source.distance,
        round_trip=source.round_trip,
        tariff_per_km=source.tariff_per_km,
        source_reimbursement_id=normalize_reimbursement_id(source.reimbursement_id),
    )
    values.update(changes)
    return CanonicalTrip(**values)


def _source_reimbursement(reimbursement_id=3, legacy_trip_list="7", **changes):
    values = dict(
        reimbursement_id=reimbursement_id,
        person_id=12,
        payment_date=date(2026, 9, 30),
        amount=Decimal("10.00"),
        legacy_trip_list=legacy_trip_list,
    )
    values.update(changes)
    return LegacyReimbursement(**values)


def _dest_reimbursement(source=None, source_trip_ids=(7,), **changes):
    source = source or _source_reimbursement()
    values = dict(
        source_reimbursement_id=source.reimbursement_id,
        destination_id=f"reimbursement-{source.reimbursement_id}",
        person_id=source.person_id,
        payment_date=source.payment_date,
        amount=source.amount,
        source_trip_ids=tuple(source_trip_ids),
    )
    values.update(changes)
    return CanonicalReimbursement(**values)


def test_zero_and_null_reimbursement_both_mean_free_trip():
    assert normalize_reimbursement_id(0) is None
    assert normalize_reimbursement_id("0") is None
    assert normalize_reimbursement_id(None) is None


def test_legacy_trip_list_parser_reports_invalid_tokens():
    ids, invalid = parse_legacy_trip_list("7-8-BOGUS-0")
    assert ids == (7, 8)
    assert invalid == ("BOGUS", "0")


def test_clean_frais_dataset_reconciles_exactly():
    source_trip = _source_trip()
    source_reimbursement = _source_reimbursement()
    result = reconcile_expenses(
        source_people_ids=[12],
        source_trips=[source_trip],
        source_reimbursements=[source_reimbursement],
        destination_trips=[_dest_trip(source_trip)],
        destination_reimbursements=[
            _dest_reimbursement(source_reimbursement)
        ],
    )

    assert result.is_valid is True
    assert result.report.blocking_reasons() == ()
    assert result.mirror_audits[0].matches is True


def test_zero_pseudo_null_is_explicitly_transformed_not_silently_migrated():
    source_trip = _source_trip(reimbursement_id=0)
    result = reconcile_expenses(
        source_people_ids=[12],
        source_trips=[source_trip],
        source_reimbursements=[],
        destination_trips=[_dest_trip(source_trip)],
        destination_reimbursements=[],
    )

    assert result.is_valid is True
    entry = result.report.entries[0]
    assert entry.disposition.value == "TRANSFORMED"
    assert entry.reason_code == "ZERO_REIMBURSEMENT_NORMALIZED_TO_NULL"


def test_leading_zero_postcode_must_survive_migration():
    source_trip = _source_trip(reimbursement_id=None)
    broken = _dest_trip(source_trip, departure_postcode="3510")
    result = reconcile_expenses(
        source_people_ids=[12],
        source_trips=[source_trip],
        source_reimbursements=[],
        destination_trips=[broken],
        destination_reimbursements=[],
    )

    assert result.is_valid is False
    assert result.report.entries[0].reason_code == "TRIP_VALUE_MISMATCH"


def test_divergent_legacy_mirror_is_transformed_from_canonical_assignments():
    trip7 = _source_trip(7, 3)
    trip8 = _source_trip(8, 3)
    reimbursement = _source_reimbursement(3, legacy_trip_list="7")
    result = reconcile_expenses(
        source_people_ids=[12],
        source_trips=[trip7, trip8],
        source_reimbursements=[reimbursement],
        destination_trips=[_dest_trip(trip7), _dest_trip(trip8)],
        destination_reimbursements=[
            _dest_reimbursement(reimbursement, source_trip_ids=(7, 8))
        ],
    )

    assert result.is_valid is True
    audit = result.mirror_audits[0]
    assert audit.canonical_only_trip_ids == (8,)
    reimbursement_entry = result.report.entries[-1]
    assert reimbursement_entry.disposition.value == "TRANSFORMED"
    assert (
        reimbursement_entry.reason_code
        == "LEGACY_TRIP_LIST_REBUILT_FROM_CANONICAL_ASSIGNMENTS"
    )


def test_unparsable_legacy_mirror_blocks_migration():
    trip = _source_trip()
    reimbursement = _source_reimbursement(legacy_trip_list="7-XYZ")
    result = reconcile_expenses(
        source_people_ids=[12],
        source_trips=[trip],
        source_reimbursements=[reimbursement],
        destination_trips=[_dest_trip(trip)],
        destination_reimbursements=[_dest_reimbursement(reimbursement)],
    )

    assert result.is_valid is False
    assert result.report.entries[-1].reason_code == "LEGACY_TRIP_LIST_UNPARSABLE"


def test_trip_pointing_to_missing_reimbursement_is_rejected():
    trip = _source_trip(reimbursement_id=99)
    result = reconcile_expenses(
        source_people_ids=[12],
        source_trips=[trip],
        source_reimbursements=[],
        destination_trips=[_dest_trip(trip)],
        destination_reimbursements=[],
    )

    assert result.is_valid is False
    assert result.report.entries[0].reason_code == "TRIP_REIMBURSEMENT_NOT_FOUND"


def test_person_conflict_between_trip_and_reimbursement_is_rejected():
    trip = _source_trip(person_id=12)
    reimbursement = _source_reimbursement(person_id=13)
    result = reconcile_expenses(
        source_people_ids=[12, 13],
        source_trips=[trip],
        source_reimbursements=[reimbursement],
        destination_trips=[_dest_trip(trip)],
        destination_reimbursements=[_dest_reimbursement(reimbursement)],
    )

    assert result.is_valid is False
    assert (
        result.report.entries[0].reason_code
        == "TRIP_REIMBURSEMENT_PERSON_MISMATCH"
    )


def test_one_cent_difference_blocks_migration():
    reimbursement = _source_reimbursement(amount=Decimal("10.00"), legacy_trip_list="")
    result = reconcile_expenses(
        source_people_ids=[12],
        source_trips=[],
        source_reimbursements=[reimbursement],
        destination_trips=[],
        destination_reimbursements=[
            _dest_reimbursement(
                reimbursement,
                source_trip_ids=(),
                amount=Decimal("9.99"),
            )
        ],
    )

    assert result.is_valid is False
    mismatches = {metric.code for metric in result.report.blocking_metric_mismatches}
    assert "REIMBURSEMENT_TOTAL_CENTS" in mismatches


def test_duplicate_source_ids_block_validation():
    first = _source_trip(trip_id=7, reimbursement_id=None)
    duplicate = _source_trip(trip_id=7, reimbursement_id=None)
    result = reconcile_expenses(
        source_people_ids=[12],
        source_trips=[first, duplicate],
        source_reimbursements=[],
        destination_trips=[_dest_trip(first)],
        destination_reimbursements=[],
    )

    assert result.is_valid is False
    assert result.report.duplicated_sources == (
        ("noethys_teamworks_legacy", "deplacements", "7"),
    )