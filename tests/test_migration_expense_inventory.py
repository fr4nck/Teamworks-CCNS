from decimal import Decimal

from domain.migration.expense_inventory import (
    RawReimbursementRow,
    RawTripRow,
    analyze_expense_pilot_source,
)
from domain.migration.severity import Severity


def _trip(trip_id=7, reimbursement_id=3, **changes):
    values = dict(
        trip_id=trip_id,
        person_id=12,
        travel_date="2026-09-10",
        departure_postcode="03510",
        arrival_postcode="35000",
        distance=Decimal("20.0"),
        tariff_per_km=Decimal("0.50"),
        round_trip=0,
        reimbursement_id=reimbursement_id,
    )
    values.update(changes)
    return RawTripRow(**values)


def _reimbursement(reimbursement_id=3, legacy_trip_list="7", **changes):
    values = dict(
        reimbursement_id=reimbursement_id,
        person_id=12,
        payment_date="2026-09-30",
        amount=Decimal("10.00"),
        legacy_trip_list=legacy_trip_list,
    )
    values.update(changes)
    return RawReimbursementRow(**values)


def test_empty_source_produces_empty_summary_and_no_findings():
    result = analyze_expense_pilot_source(
        source_people_ids=[], trips=[], reimbursements=[]
    )

    assert result.summary.trip_count == 0
    assert result.summary.reimbursement_count == 0
    assert result.findings == ()
    assert result.mirror_audits == ()


def test_clean_dataset_has_no_blocking_finding():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip()],
        reimbursements=[_reimbursement()],
    )

    assert result.blocking_findings == ()
    assert result.summary.attached_trip_count == 1
    assert result.summary.free_trip_count == 0
    assert result.mirror_audits[0].matches is True


def test_free_trip_with_null_reimbursement_is_not_an_anomaly():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None)],
        reimbursements=[],
    )

    assert result.blocking_findings == ()
    assert result.summary.free_trip_count == 1
    codes = {f.code for f in result.findings}
    assert "ZERO_REIMBURSEMENT_NORMALIZED_TO_NULL" not in codes


def test_zero_reimbursement_is_flagged_as_info_transformation():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=0)],
        reimbursements=[],
    )

    finding = next(
        f for f in result.findings if f.code == "ZERO_REIMBURSEMENT_NORMALIZED_TO_NULL"
    )
    assert finding.severity is Severity.INFO
    assert result.summary.free_trip_count == 1


def test_negative_reimbursement_id_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=-1)],
        reimbursements=[],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "TRIP_REIMBURSEMENT_ID_INVALID" in codes


def test_trip_person_not_found_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[], trips=[_trip(reimbursement_id=None)], reimbursements=[]
    )

    codes = {f.code for f in result.blocking_findings}
    assert "TRIP_PERSON_NOT_FOUND" in codes


def test_reimbursement_person_not_found_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[],
        trips=[],
        reimbursements=[_reimbursement(legacy_trip_list="")],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "REIMBURSEMENT_PERSON_NOT_FOUND" in codes


def test_trip_referencing_missing_reimbursement_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12], trips=[_trip(reimbursement_id=99)], reimbursements=[]
    )

    codes = {f.code for f in result.blocking_findings}
    assert "TRIP_REIMBURSEMENT_NOT_FOUND" in codes


def test_person_conflict_between_trip_and_reimbursement_is_blocking():
    trip = _trip(person_id=12)
    reimbursement = _reimbursement(person_id=13)
    result = analyze_expense_pilot_source(
        source_people_ids=[12, 13], trips=[trip], reimbursements=[reimbursement]
    )

    codes = {f.code for f in result.blocking_findings}
    assert "TRIP_REIMBURSEMENT_PERSON_MISMATCH" in codes


def test_duplicate_trip_id_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None), _trip(reimbursement_id=None)],
        reimbursements=[],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "TRIP_ID_DUPLICATED" in codes


def test_duplicate_reimbursement_id_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[],
        reimbursements=[
            _reimbursement(legacy_trip_list=""),
            _reimbursement(legacy_trip_list=""),
        ],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "REIMBURSEMENT_ID_DUPLICATED" in codes


def test_leading_zero_postcode_is_informational_only():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None, departure_postcode="03510")],
        reimbursements=[],
    )

    finding = next(f for f in result.findings if f.code == "TRIP_POSTCODE_LEADING_ZERO")
    assert finding.severity is Severity.INFO
    assert result.blocking_findings == ()


def test_postcode_wrong_length_is_review():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None, departure_postcode="351")],
        reimbursements=[],
    )

    finding = next(f for f in result.findings if f.code == "TRIP_POSTCODE_LENGTH_INVALID")
    assert finding.severity is Severity.REVIEW


def test_postcode_non_numeric_is_review():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None, departure_postcode="AB510")],
        reimbursements=[],
    )

    finding = next(f for f in result.findings if f.code == "TRIP_POSTCODE_NOT_NUMERIC")
    assert finding.severity is Severity.REVIEW


def test_negative_distance_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None, distance=Decimal("-1"))],
        reimbursements=[],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "TRIP_DISTANCE_NEGATIVE" in codes


def test_negative_tariff_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None, tariff_per_km=Decimal("-0.5"))],
        reimbursements=[],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "TRIP_TARIFF_NEGATIVE" in codes


def test_unparsable_trip_date_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None, travel_date="not-a-date")],
        reimbursements=[],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "TRIP_DATE_UNPARSABLE" in codes


def test_unusual_round_trip_value_is_review():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[_trip(reimbursement_id=None, round_trip="maybe")],
        reimbursements=[],
    )

    finding = next(f for f in result.findings if f.code == "TRIP_ROUND_TRIP_VALUE_UNUSUAL")
    assert finding.severity is Severity.REVIEW


def test_zero_amount_is_review():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[],
        reimbursements=[_reimbursement(legacy_trip_list="", amount=Decimal("0"))],
    )

    finding = next(f for f in result.findings if f.code == "REIMBURSEMENT_AMOUNT_ZERO")
    assert finding.severity is Severity.REVIEW


def test_negative_amount_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[],
        reimbursements=[_reimbursement(legacy_trip_list="", amount=Decimal("-5"))],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "REIMBURSEMENT_AMOUNT_NEGATIVE" in codes


def test_unparsable_amount_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[],
        reimbursements=[_reimbursement(legacy_trip_list="", amount="NaN-ish")],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "REIMBURSEMENT_AMOUNT_UNPARSABLE" in codes


def test_unparsable_reimbursement_date_is_blocking():
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[],
        reimbursements=[_reimbursement(legacy_trip_list="", payment_date="???")],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "REIMBURSEMENT_DATE_UNPARSABLE" in codes


def test_mirror_consistent_with_canonical_matches():
    trip = _trip(7, 3)
    reimbursement = _reimbursement(3, legacy_trip_list="7")
    result = analyze_expense_pilot_source(
        source_people_ids=[12], trips=[trip], reimbursements=[reimbursement]
    )

    assert result.mirror_audits[0].matches is True
    assert result.blocking_findings == ()


def test_mirror_incomplete_but_reconstructible_is_review():
    trip7 = _trip(7, 3)
    trip8 = _trip(8, 3)
    reimbursement = _reimbursement(3, legacy_trip_list="7")
    result = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[trip7, trip8],
        reimbursements=[reimbursement],
    )

    audit = result.mirror_audits[0]
    assert audit.canonical_only_trip_ids == (8,)
    finding = next(
        f
        for f in result.findings
        if f.code == "LEGACY_TRIP_LIST_REBUILT_FROM_CANONICAL_ASSIGNMENTS"
    )
    assert finding.severity is Severity.REVIEW
    assert result.blocking_findings == ()


def test_mirror_with_invalid_token_is_blocking():
    reimbursement = _reimbursement(3, legacy_trip_list="7-XYZ")
    result = analyze_expense_pilot_source(
        source_people_ids=[12], trips=[_trip(7, 3)], reimbursements=[reimbursement]
    )

    codes = {f.code for f in result.blocking_findings}
    assert "LEGACY_TRIP_LIST_UNPARSABLE" in codes


def test_mirror_referencing_unknown_trip_is_blocking():
    reimbursement = _reimbursement(3, legacy_trip_list="7-999")
    result = analyze_expense_pilot_source(
        source_people_ids=[12], trips=[_trip(7, 3)], reimbursements=[reimbursement]
    )

    codes = {f.code for f in result.blocking_findings}
    assert "LEGACY_TRIP_LIST_REFERENCES_UNKNOWN_TRIP" in codes


def test_mirror_referencing_trip_of_another_person_is_blocking():
    trip7 = _trip(7, 3, person_id=12)
    trip8 = _trip(8, None, person_id=13)
    reimbursement = _reimbursement(3, legacy_trip_list="7-8", person_id=12)
    result = analyze_expense_pilot_source(
        source_people_ids=[12, 13],
        trips=[trip7, trip8],
        reimbursements=[reimbursement],
    )

    codes = {f.code for f in result.blocking_findings}
    assert "LEGACY_TRIP_LIST_PERSON_MISMATCH" in codes


def test_mirror_conflicting_with_canonical_assignment_is_blocking():
    trip7 = _trip(7, 3)
    trip8 = _trip(8, None)
    reimbursement = _reimbursement(3, legacy_trip_list="7-8")
    result = analyze_expense_pilot_source(
        source_people_ids=[12], trips=[trip7, trip8], reimbursements=[reimbursement]
    )

    codes = {f.code for f in result.blocking_findings}
    assert "LEGACY_TRIP_LIST_CONFLICTS_WITH_CANONICAL_ASSIGNMENT" in codes


def test_result_is_deterministic_for_same_input():
    trips = [_trip(7, 3), _trip(8, None)]
    reimbursements = [_reimbursement(3, legacy_trip_list="7")]

    first = analyze_expense_pilot_source(
        source_people_ids=[12], trips=trips, reimbursements=reimbursements
    )
    second = analyze_expense_pilot_source(
        source_people_ids=[12], trips=trips, reimbursements=reimbursements
    )

    assert first == second
