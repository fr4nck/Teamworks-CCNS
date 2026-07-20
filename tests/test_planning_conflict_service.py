from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from domain.missions import (
    Mission,
    MissionOccurrence,
    MissionOccurrenceAssignment,
    MissionOccurrenceAssignmentStatus,
)
from domain.people import Civility, Employee
from domain.planning import PlanningConflict, PlanningConflictResult, PlanningConflictService


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
        starts_at=datetime(2026, 7, 20, start_hour, 0, tzinfo=tzinfo),
        ends_at=datetime(2026, 7, 20, end_hour, 0, tzinfo=tzinfo),
        active=active,
    )


def assignment(employee, occurrence, *, status=MissionOccurrenceAssignmentStatus.PLANNED, active=True, id=None):
    kwargs = {"employee": employee, "occurrence": occurrence, "status": status, "active": active}
    if id is not None:
        kwargs["id"] = id
    return MissionOccurrenceAssignment(**kwargs)


def evaluate(employee, assignments):
    return PlanningConflictService().evaluate(employee, assignments)


def test_no_assignment_is_accepted(employee):
    result = evaluate(employee, [])

    assert result.considered_assignments == ()
    assert result.conflicts == ()
    assert result.has_conflicts() is False
    assert result.conflict_count() == 0
    assert result.considered_assignment_count() == 0


def test_single_assignment_has_no_conflict(employee, mission):
    first = assignment(employee, occurrence(mission, 8, 10))

    result = evaluate(employee, [first])

    assert result.considered_assignments == (first,)
    assert result.conflicts == ()


@pytest.mark.parametrize("hours", [((8, 10), (11, 12)), ((8, 10), (10, 12))])
def test_separate_or_adjacent_occurrences_have_no_conflict(employee, mission, hours):
    first = assignment(employee, occurrence(mission, *hours[0]))
    second = assignment(employee, occurrence(mission, *hours[1]))

    assert evaluate(employee, [first, second]).conflicts == ()


def test_partial_overlap_creates_conflict_with_exact_bounds(employee, mission):
    first = assignment(employee, occurrence(mission, 8, 11))
    second = assignment(employee, occurrence(mission, 10, 12))

    conflict = evaluate(employee, [first, second]).conflicts[0]

    assert conflict.overlap_start == datetime(2026, 7, 20, 10)
    assert conflict.overlap_end == datetime(2026, 7, 20, 11)


def test_contained_occurrence_overlap_matches_contained_occurrence(employee, mission):
    outer = assignment(employee, occurrence(mission, 8, 14))
    inner_occurrence = occurrence(mission, 10, 12)
    inner = assignment(employee, inner_occurrence)

    conflict = evaluate(employee, [outer, inner]).conflicts[0]

    assert conflict.overlap_start == inner_occurrence.starts_at
    assert conflict.overlap_end == inner_occurrence.ends_at


def test_identical_occurrences_and_distinct_assignments_to_same_occurrence_conflict(employee, mission):
    shared = occurrence(mission, 8, 10)
    first = assignment(employee, shared)
    second = assignment(employee, shared)

    conflict = evaluate(employee, [first, second]).conflicts[0]

    assert conflict.overlap_start == shared.starts_at
    assert conflict.overlap_end == shared.ends_at


def test_multiple_conflicts_and_pair_order_are_preserved(employee, mission):
    first = assignment(employee, occurrence(mission, 8, 12))
    second = assignment(employee, occurrence(mission, 9, 11))
    third = assignment(employee, occurrence(mission, 10, 13))

    conflicts = evaluate(employee, [first, second, third]).conflicts

    assert [(c.first_assignment, c.second_assignment) for c in conflicts] == [
        (first, second),
        (first, third),
        (second, third),
    ]


def test_each_pair_is_examined_once_and_repeated_assignment_is_deduplicated(employee, mission):
    assignment_id = uuid4()
    first = assignment(employee, occurrence(mission, 8, 12), id=assignment_id)
    duplicate_uuid = assignment(employee, occurrence(mission, 9, 11), id=assignment_id)
    second = assignment(employee, occurrence(mission, 10, 13))

    result = evaluate(employee, [first, first, duplicate_uuid, second])

    assert result.considered_assignments == (first, second)
    assert [(c.first_assignment, c.second_assignment) for c in result.conflicts] == [(first, second)]


def test_filters_assignments_by_employee_active_occurrence_active_and_status(employee, other_employee, mission):
    planned = assignment(employee, occurrence(mission, 8, 10), status=MissionOccurrenceAssignmentStatus.PLANNED)
    confirmed = assignment(employee, occurrence(mission, 8, 10), status=MissionOccurrenceAssignmentStatus.CONFIRMED)
    ignored = [
        assignment(other_employee, occurrence(mission, 8, 10)),
        assignment(employee, occurrence(mission, 8, 10), active=False),
        assignment(employee, occurrence(mission, 8, 10, active=False)),
        assignment(employee, occurrence(mission, 8, 10), status=MissionOccurrenceAssignmentStatus.CANCELLED),
        assignment(employee, occurrence(mission, 8, 10), status=MissionOccurrenceAssignmentStatus.COMPLETED),
        assignment(employee, occurrence(mission, 8, 10), status=MissionOccurrenceAssignmentStatus.ABSENT),
    ]

    result = evaluate(employee, [*ignored, planned, confirmed])

    assert result.considered_assignments == (planned, confirmed)
    assert result.conflict_count() == 1


def test_considered_assignment_order_is_preserved(employee, mission):
    first = assignment(employee, occurrence(mission, 8, 9))
    second = assignment(employee, occurrence(mission, 10, 11))

    assert evaluate(employee, (first, second)).considered_assignments == (first, second)


def test_conflict_methods(employee, other_employee, mission):
    first = assignment(employee, occurrence(mission, 8, 11))
    second = assignment(employee, occurrence(mission, 10, 12))
    unrelated = assignment(employee, occurrence(mission, 13, 14))

    conflict = evaluate(employee, [first, second, unrelated]).conflicts[0]

    assert conflict.duration() == timedelta(hours=1)
    assert conflict.involves(first) is True
    assert conflict.involves(second) is True
    assert conflict.involves(unrelated) is False
    assert conflict.involves_employee(employee) is True
    assert conflict.involves_employee(other_employee) is False


def test_result_and_conflict_are_immutable_and_collections_are_tuples(employee, mission):
    first = assignment(employee, occurrence(mission, 8, 11))
    second = assignment(employee, occurrence(mission, 10, 12))
    result = evaluate(employee, [first, second])

    assert isinstance(result.considered_assignments, tuple)
    assert isinstance(result.conflicts, tuple)
    with pytest.raises(FrozenInstanceError):
        result.conflicts = ()
    with pytest.raises(FrozenInstanceError):
        result.conflicts[0].overlap_end = datetime(2026, 7, 20, 10)


def test_invalid_employee_is_rejected():
    with pytest.raises(ValueError, match="Employee"):
        evaluate("invalid", [])
    with pytest.raises(ValueError, match="Employee"):
        evaluate(None, [])


@pytest.mark.parametrize("assignments_value", ["invalid", b"invalid", object()])
def test_invalid_collection_is_rejected(employee, assignments_value):
    with pytest.raises(ValueError, match="collection"):
        evaluate(employee, assignments_value)


def test_invalid_assignment_element_is_rejected(employee):
    with pytest.raises(ValueError, match="MissionOccurrenceAssignment"):
        evaluate(employee, [object()])


def test_mixed_naive_and_aware_datetimes_are_rejected(employee, mission):
    naive = assignment(employee, occurrence(mission, 8, 10))
    aware = assignment(employee, occurrence(mission, 9, 11, tzinfo=timezone.utc))

    with pytest.raises(ValueError, match="fuseau horaire"):
        evaluate(employee, [naive, aware])


def test_two_naive_and_two_aware_datetimes_are_accepted(employee, mission):
    naive_first = assignment(employee, occurrence(mission, 8, 10))
    naive_second = assignment(employee, occurrence(mission, 9, 11))
    aware_first = assignment(employee, occurrence(mission, 12, 14, tzinfo=timezone.utc))
    aware_second = assignment(employee, occurrence(mission, 13, 15, tzinfo=timezone.utc))

    assert evaluate(employee, [naive_first, naive_second]).conflict_count() == 1
    assert evaluate(employee, [aware_first, aware_second]).conflict_count() == 1


def test_planning_conflict_validates_assignments_employee_and_overlap(employee, other_employee, mission):
    first = assignment(employee, occurrence(mission, 8, 10))
    second = assignment(employee, occurrence(mission, 9, 11))
    same_employee_other = assignment(other_employee, occurrence(mission, 9, 11))

    with pytest.raises(ValueError, match="différentes"):
        PlanningConflict(first, first, datetime(2026, 7, 20, 8), datetime(2026, 7, 20, 10))
    with pytest.raises(ValueError, match="même salarié"):
        PlanningConflict(first, same_employee_other, datetime(2026, 7, 20, 9), datetime(2026, 7, 20, 10))
    with pytest.raises(ValueError, match="début le plus tardif"):
        PlanningConflict(first, second, datetime(2026, 7, 20, 8), datetime(2026, 7, 20, 10))
    adjacent = assignment(employee, occurrence(mission, 10, 12))
    with pytest.raises(ValueError, match="durée"):
        PlanningConflict(first, adjacent, datetime(2026, 7, 20, 10), datetime(2026, 7, 20, 10))


def test_planning_conflict_result_validates_content(employee, mission):
    first = assignment(employee, occurrence(mission, 8, 10))

    with pytest.raises(ValueError, match="MissionOccurrenceAssignment"):
        PlanningConflictResult(employee, [object()], [])
    with pytest.raises(ValueError, match="PlanningConflict"):
        PlanningConflictResult(employee, [first], [object()])


def test_service_does_not_consult_current_date(employee, mission, monkeypatch):
    import domain.planning.planning_conflict_service as module

    def forbidden(*args, **kwargs):
        raise AssertionError("date courante consultée")

    class ForbiddenDatetime:
        now = staticmethod(forbidden)
        today = staticmethod(forbidden)

    monkeypatch.setattr(module, "datetime", ForbiddenDatetime)

    first = assignment(employee, occurrence(mission, 8, 10))

    assert evaluate(employee, [first]).conflict_count() == 0
