from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from domain.missions import (
    Mission,
    MissionOccurrence,
    MissionOccurrenceAssignment,
    MissionOccurrenceAssignmentStatus,
)
from domain.people import Civility, Employee
from domain.planning import (
    EmployeeUnavailability,
    EmployeeUnavailabilityReason,
    UnavailabilityConflict,
    UnavailabilityConflictResult,
    UnavailabilityConflictService,
)


@pytest.fixture
def employee():
    return Employee(civility=Civility.MADAME, first_name="Ada", last_name="Lovelace")


@pytest.fixture
def other_employee():
    return Employee(civility=Civility.MONSIEUR, first_name="Alan", last_name="Turing")


@pytest.fixture
def mission():
    return Mission(code="animation", name="Animation")


def occurrence(mission, start_hour, end_hour, *, active=True, tzinfo=None):
    return MissionOccurrence(
        mission=mission,
        starts_at=datetime(2026, 7, 20, start_hour, tzinfo=tzinfo),
        ends_at=datetime(2026, 7, 20, end_hour, tzinfo=tzinfo),
        active=active,
    )


def assignment(
    employee,
    occurrence,
    *,
    status=MissionOccurrenceAssignmentStatus.PLANNED,
    active=True,
    id=None
):
    kwargs = {
        "employee": employee,
        "occurrence": occurrence,
        "status": status,
        "active": active,
    }
    if id is not None:
        kwargs["id"] = id
    return MissionOccurrenceAssignment(**kwargs)


def unavailability(
    employee,
    start_hour,
    end_hour,
    *,
    reason=EmployeeUnavailabilityReason.LEAVE,
    active=True,
    id=None,
    tzinfo=None
):
    kwargs = {
        "employee": employee,
        "starts_at": datetime(2026, 7, 20, start_hour, tzinfo=tzinfo),
        "ends_at": datetime(2026, 7, 20, end_hour, tzinfo=tzinfo),
        "reason": reason,
        "active": active,
    }
    if id is not None:
        kwargs["id"] = id
    return EmployeeUnavailability(**kwargs)


def evaluate(employee, assignments, unavailabilities):
    return UnavailabilityConflictService().evaluate(
        employee, assignments, unavailabilities
    )


@pytest.mark.parametrize(
    "assignments,unavailabilities", [([], []), ([], ["u"]), (["a"], [])]
)
def test_empty_inputs_are_accepted(employee, mission, assignments, unavailabilities):
    actual_assignments = (
        [] if not assignments else [assignment(employee, occurrence(mission, 8, 10))]
    )
    actual_unavailabilities = (
        [] if not unavailabilities else [unavailability(employee, 9, 11)]
    )

    result = evaluate(employee, actual_assignments, actual_unavailabilities)

    assert result.considered_assignments == tuple(actual_assignments)
    assert result.considered_unavailabilities == tuple(actual_unavailabilities)
    assert result.conflicts == ()
    assert result.has_conflicts() is False
    assert result.conflict_count() == 0


def test_no_conflict_and_adjacent_periods(employee, mission):
    first = assignment(employee, occurrence(mission, 8, 10))
    before = unavailability(employee, 6, 8)
    after = unavailability(employee, 10, 12)

    assert evaluate(employee, [first], [before, after]).conflicts == ()


@pytest.mark.parametrize(
    ("assignment_hours", "unavailability_hours", "expected_hours"),
    [
        ((8, 11), (10, 12), (10, 11)),
        ((10, 11), (8, 12), (10, 11)),
        ((8, 12), (10, 11), (10, 11)),
        ((8, 10), (8, 10), (8, 10)),
    ],
)
def test_overlap_variants_have_exact_bounds(
    employee, mission, assignment_hours, unavailability_hours, expected_hours
):
    planned = assignment(employee, occurrence(mission, *assignment_hours))
    unavailable = unavailability(employee, *unavailability_hours)

    conflict = evaluate(employee, [planned], [unavailable]).conflicts[0]

    assert conflict.overlap_start == datetime(2026, 7, 20, expected_hours[0])
    assert conflict.overlap_end == datetime(2026, 7, 20, expected_hours[1])


def test_multiple_conflicts_for_one_assignment_and_one_unavailability(
    employee, mission
):
    planned = assignment(employee, occurrence(mission, 8, 14))
    first_unavailability = unavailability(employee, 9, 10)
    second_unavailability = unavailability(employee, 11, 12)
    other_assignment = assignment(employee, occurrence(mission, 9, 13))

    one_assignment = evaluate(
        employee, [planned], [first_unavailability, second_unavailability]
    )
    one_unavailability = evaluate(
        employee, [planned, other_assignment], [first_unavailability]
    )

    assert [c.unavailability for c in one_assignment.conflicts] == [
        first_unavailability,
        second_unavailability,
    ]
    assert [c.assignment for c in one_unavailability.conflicts] == [
        planned,
        other_assignment,
    ]


def test_conflict_order_and_deduplication_are_preserved(employee, mission):
    first_id = uuid4()
    unavailable_id = uuid4()
    first = assignment(employee, occurrence(mission, 8, 12), id=first_id)
    duplicate_assignment = assignment(employee, occurrence(mission, 9, 10), id=first_id)
    second = assignment(employee, occurrence(mission, 10, 14))
    unavailable = unavailability(employee, 9, 13, id=unavailable_id)
    duplicate_unavailable = unavailability(employee, 10, 11, id=unavailable_id)
    second_unavailable = unavailability(employee, 11, 15)

    result = evaluate(
        employee,
        [first, duplicate_assignment, second],
        [unavailable, duplicate_unavailable, second_unavailable],
    )

    assert result.considered_assignments == (first, second)
    assert result.considered_unavailabilities == (unavailable, second_unavailable)
    assert [(c.assignment, c.unavailability) for c in result.conflicts] == [
        (first, unavailable),
        (first, second_unavailable),
        (second, unavailable),
        (second, second_unavailable),
    ]


def test_filters_by_employee_active_occurrence_active_unavailability_active_and_status(
    employee, other_employee, mission
):
    planned = assignment(
        employee,
        occurrence(mission, 8, 10),
        status=MissionOccurrenceAssignmentStatus.PLANNED,
    )
    confirmed = assignment(
        employee,
        occurrence(mission, 8, 10),
        status=MissionOccurrenceAssignmentStatus.CONFIRMED,
    )
    considered_unavailability = unavailability(
        employee, 9, 11, reason=EmployeeUnavailabilityReason.SICKNESS
    )
    ignored_assignments = [
        assignment(other_employee, occurrence(mission, 8, 10)),
        assignment(employee, occurrence(mission, 8, 10), active=False),
        assignment(employee, occurrence(mission, 8, 10, active=False)),
        assignment(
            employee,
            occurrence(mission, 8, 10),
            status=MissionOccurrenceAssignmentStatus.CANCELLED,
        ),
        assignment(
            employee,
            occurrence(mission, 8, 10),
            status=MissionOccurrenceAssignmentStatus.COMPLETED,
        ),
        assignment(
            employee,
            occurrence(mission, 8, 10),
            status=MissionOccurrenceAssignmentStatus.ABSENT,
        ),
    ]
    ignored_unavailabilities = [
        unavailability(other_employee, 9, 11),
        unavailability(employee, 9, 11, active=False),
    ]

    result = evaluate(
        employee,
        [*ignored_assignments, planned, confirmed],
        [*ignored_unavailabilities, considered_unavailability],
    )

    assert result.considered_assignments == (planned, confirmed)
    assert result.considered_unavailabilities == (considered_unavailability,)
    assert result.conflict_count() == 2


def test_all_unavailability_reasons_are_considered(employee, mission):
    planned = assignment(employee, occurrence(mission, 8, 18))
    items = [
        unavailability(employee, 8 + index, 9 + index, reason=reason)
        for index, reason in enumerate(EmployeeUnavailabilityReason)
    ]

    assert evaluate(employee, [planned], items).conflict_count() == len(
        EmployeeUnavailabilityReason
    )


def test_methods_immutability_and_tuple_collections(employee, other_employee, mission):
    planned = assignment(employee, occurrence(mission, 8, 11))
    unavailable = unavailability(employee, 10, 12)
    unrelated_assignment = assignment(employee, occurrence(mission, 12, 13))
    unrelated_unavailability = unavailability(employee, 13, 14)

    result = evaluate(employee, [planned], [unavailable])
    conflict = result.conflicts[0]

    assert conflict.duration() == timedelta(hours=1)
    assert conflict.involves_assignment(planned) is True
    assert conflict.involves_assignment(unrelated_assignment) is False
    assert conflict.involves_assignment(object()) is False
    assert conflict.involves_unavailability(unavailable) is True
    assert conflict.involves_unavailability(unrelated_unavailability) is False
    assert conflict.involves_unavailability(object()) is False
    assert conflict.involves_employee(employee) is True
    assert conflict.involves_employee(other_employee) is False
    assert conflict.involves_employee(object()) is False
    assert isinstance(result.considered_assignments, tuple)
    assert isinstance(result.considered_unavailabilities, tuple)
    assert isinstance(result.conflicts, tuple)
    assert result.considered_assignment_count() == 1
    assert result.considered_unavailability_count() == 1
    with pytest.raises(FrozenInstanceError):
        conflict.overlap_end = datetime(2026, 7, 20, 10)
    with pytest.raises(FrozenInstanceError):
        result.conflicts = ()


def test_invalid_service_inputs_are_rejected(employee):
    with pytest.raises(ValueError, match="Employee"):
        evaluate("invalid", [], [])
    for invalid in ("invalid", b"invalid", object()):
        with pytest.raises(ValueError, match="collection"):
            evaluate(employee, invalid, [])
        with pytest.raises(ValueError, match="collection"):
            evaluate(employee, [], invalid)
    with pytest.raises(ValueError, match="MissionOccurrenceAssignment"):
        evaluate(employee, [object()], [])
    with pytest.raises(ValueError, match="EmployeeUnavailability"):
        evaluate(employee, [], [object()])


def test_conflict_validates_types_employee_bounds_and_overlap(
    employee, other_employee, mission
):
    planned = assignment(employee, occurrence(mission, 8, 10))
    unavailable = unavailability(employee, 9, 11)
    other_unavailable = unavailability(other_employee, 9, 11)
    with pytest.raises(ValueError, match="MissionOccurrenceAssignment"):
        UnavailabilityConflict(
            object(), unavailable, datetime(2026, 7, 20, 9), datetime(2026, 7, 20, 10)
        )
    with pytest.raises(ValueError, match="EmployeeUnavailability"):
        UnavailabilityConflict(
            planned, object(), datetime(2026, 7, 20, 9), datetime(2026, 7, 20, 10)
        )
    with pytest.raises(ValueError, match="même salarié"):
        UnavailabilityConflict(
            planned,
            other_unavailable,
            datetime(2026, 7, 20, 9),
            datetime(2026, 7, 20, 10),
        )
    with pytest.raises(ValueError, match="datetime"):
        UnavailabilityConflict(
            planned, unavailable, "invalid", datetime(2026, 7, 20, 10)
        )
    with pytest.raises(ValueError, match="début le plus tardif"):
        UnavailabilityConflict(
            planned, unavailable, datetime(2026, 7, 20, 8), datetime(2026, 7, 20, 10)
        )
    adjacent = unavailability(employee, 10, 12)
    with pytest.raises(ValueError, match="durée"):
        UnavailabilityConflict(
            planned, adjacent, datetime(2026, 7, 20, 10), datetime(2026, 7, 20, 10)
        )


def test_result_validates_content(employee, mission):
    planned = assignment(employee, occurrence(mission, 8, 10))
    unavailable = unavailability(employee, 9, 11)
    conflict = evaluate(employee, [planned], [unavailable]).conflicts[0]

    with pytest.raises(ValueError, match="Employee"):
        UnavailabilityConflictResult("invalid", (), (), ())
    with pytest.raises(ValueError, match="MissionOccurrenceAssignment"):
        UnavailabilityConflictResult(employee, (object(),), (), ())
    with pytest.raises(ValueError, match="EmployeeUnavailability"):
        UnavailabilityConflictResult(employee, (), (object(),), ())
    with pytest.raises(ValueError, match="UnavailabilityConflict"):
        UnavailabilityConflictResult(employee, (), (), (object(),))
    assert UnavailabilityConflictResult(
        employee, [planned], [unavailable], [conflict]
    ).conflicts == (conflict,)


def test_datetime_compatibility_rules(employee, mission):
    naive_assignment = assignment(employee, occurrence(mission, 8, 10))
    aware_unavailability = unavailability(employee, 9, 11, tzinfo=timezone.utc)
    aware_assignment = assignment(
        employee, occurrence(mission, 8, 10, tzinfo=timezone.utc)
    )
    paris_unavailability = unavailability(
        employee, 9, 11, tzinfo=ZoneInfo("Europe/Paris")
    )
    utc_unavailability = unavailability(employee, 9, 11, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="fuseau horaire"):
        evaluate(employee, [naive_assignment], [aware_unavailability])
    with pytest.raises(ValueError, match="fuseaux horaires compatibles"):
        evaluate(employee, [aware_assignment], [paris_unavailability])
    assert (
        evaluate(employee, [aware_assignment], [utc_unavailability]).conflict_count()
        == 1
    )


def test_service_does_not_consult_current_date(employee, mission, monkeypatch):
    import domain.planning.unavailability_conflict_service as service_module

    class ForbiddenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            raise AssertionError("date courante consultée")

        @classmethod
        def today(cls):
            raise AssertionError("date courante consultée")

    monkeypatch.setattr(service_module, "datetime", ForbiddenDatetime)
    planned = assignment(employee, occurrence(mission, 8, 10))
    unavailable = unavailability(employee, 9, 11)

    assert evaluate(employee, [planned], [unavailable]).conflict_count() == 1
