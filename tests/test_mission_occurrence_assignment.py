from dataclasses import FrozenInstanceError
from datetime import datetime
from uuid import uuid4

import pytest

from domain.missions import (
    Mission,
    MissionOccurrence,
    MissionOccurrenceAssignment,
    MissionOccurrenceAssignmentStatus,
)
from domain.people import Civility, Employee


@pytest.fixture
def employee():
    return Employee(civility=Civility.MADAME, first_name="Ada", last_name="Lovelace")


@pytest.fixture
def mission():
    return Mission(code="multisports", name="Séance multisports")


@pytest.fixture
def occurrence(mission):
    return MissionOccurrence(
        mission=mission,
        starts_at=datetime(2026, 7, 20, 14, 0),
        ends_at=datetime(2026, 7, 20, 16, 0),
    )


def test_mission_occurrence_assignment_is_created_with_minimal_data(employee, occurrence):
    assignment = MissionOccurrenceAssignment(
        employee=employee,
        occurrence=occurrence,
        status=MissionOccurrenceAssignmentStatus.PLANNED,
    )

    assert assignment.employee == employee
    assert assignment.occurrence == occurrence
    assert assignment.status is MissionOccurrenceAssignmentStatus.PLANNED
    assert assignment.observations is None
    assert assignment.active is True


def test_mission_occurrence_assignment_is_created_with_all_data(employee, occurrence):
    assignment_id = uuid4()
    assignment = MissionOccurrenceAssignment(
        id=assignment_id,
        employee=employee,
        occurrence=occurrence,
        status=MissionOccurrenceAssignmentStatus.CONFIRMED,
        observations="  Présence confirmée.  ",
        active=False,
    )

    assert assignment.id == assignment_id
    assert assignment.status is MissionOccurrenceAssignmentStatus.CONFIRMED
    assert assignment.observations == "Présence confirmée."
    assert assignment.active is False


def test_mission_occurrence_assignment_generates_an_identifier_automatically(employee, occurrence):
    assignment = MissionOccurrenceAssignment(
        employee=employee,
        occurrence=occurrence,
        status=MissionOccurrenceAssignmentStatus.PLANNED,
    )

    assert isinstance(assignment.id, type(uuid4()))


def test_mission_occurrence_assignment_accepts_an_explicit_uuid(employee, occurrence):
    assignment_id = uuid4()

    assignment = MissionOccurrenceAssignment(
        id=assignment_id,
        employee=employee,
        occurrence=occurrence,
        status=MissionOccurrenceAssignmentStatus.PLANNED,
    )

    assert assignment.id == assignment_id


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"employee": None}, "Employee"),
        ({"employee": "invalid"}, "Employee"),
        ({"occurrence": None}, "MissionOccurrence"),
        ({"occurrence": "invalid"}, "MissionOccurrence"),
        ({"status": None}, "MissionOccurrenceAssignmentStatus"),
        ({"status": "PLANNED"}, "MissionOccurrenceAssignmentStatus"),
        ({"active": 1}, "booléen"),
        ({"observations": "  "}, "observations"),
        ({"observations": 42}, "observations"),
    ],
)
def test_mission_occurrence_assignment_rejects_invalid_data(
    employee, occurrence, kwargs, message
):
    data = {
        "employee": employee,
        "occurrence": occurrence,
        "status": MissionOccurrenceAssignmentStatus.PLANNED,
    }
    data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        MissionOccurrenceAssignment(**data)


def test_mission_occurrence_assignment_normalizes_observations(employee, occurrence):
    assignment = MissionOccurrenceAssignment(
        employee=employee,
        occurrence=occurrence,
        status=MissionOccurrenceAssignmentStatus.PLANNED,
        observations="  Prévoir accueil anticipé.  ",
    )

    assert assignment.observations == "Prévoir accueil anticipé."


def test_mission_occurrence_assignment_is_immutable(employee, occurrence):
    assignment = MissionOccurrenceAssignment(
        employee=employee,
        occurrence=occurrence,
        status=MissionOccurrenceAssignmentStatus.PLANNED,
    )

    with pytest.raises(FrozenInstanceError):
        assignment.active = False


@pytest.mark.parametrize(
    ("status", "method_name"),
    [
        (MissionOccurrenceAssignmentStatus.PLANNED, "is_planned"),
        (MissionOccurrenceAssignmentStatus.CONFIRMED, "is_confirmed"),
        (MissionOccurrenceAssignmentStatus.CANCELLED, "is_cancelled"),
        (MissionOccurrenceAssignmentStatus.COMPLETED, "is_completed"),
        (MissionOccurrenceAssignmentStatus.ABSENT, "is_absent"),
    ],
)
def test_mission_occurrence_assignment_status_predicates(employee, occurrence, status, method_name):
    assignment = MissionOccurrenceAssignment(
        employee=employee,
        occurrence=occurrence,
        status=status,
    )

    assert getattr(assignment, method_name)() is True


@pytest.mark.parametrize("status", list(MissionOccurrenceAssignmentStatus))
def test_mission_occurrence_assignment_only_one_status_predicate_is_true(
    employee, occurrence, status
):
    assignment = MissionOccurrenceAssignment(
        employee=employee,
        occurrence=occurrence,
        status=status,
    )

    results = [
        assignment.is_planned(),
        assignment.is_confirmed(),
        assignment.is_cancelled(),
        assignment.is_completed(),
        assignment.is_absent(),
    ]

    assert results.count(True) == 1


def test_mission_occurrence_assignment_is_active_returns_declared_value_only(
    employee, mission
):
    past_occurrence = MissionOccurrence(
        mission=mission,
        starts_at=datetime(2026, 1, 1, 14, 0),
        ends_at=datetime(2026, 1, 1, 16, 0),
    )
    inactive_future_assignment = MissionOccurrenceAssignment(
        employee=employee,
        occurrence=past_occurrence,
        status=MissionOccurrenceAssignmentStatus.COMPLETED,
        active=False,
    )

    assert inactive_future_assignment.is_active() is False


def test_mission_occurrence_assignment_status_does_not_depend_on_occurrence_dates(
    employee, mission
):
    past_occurrence = MissionOccurrence(
        mission=mission,
        starts_at=datetime(2026, 1, 1, 14, 0),
        ends_at=datetime(2026, 1, 1, 16, 0),
    )
    planned_assignment = MissionOccurrenceAssignment(
        employee=employee,
        occurrence=past_occurrence,
        status=MissionOccurrenceAssignmentStatus.PLANNED,
    )

    assert planned_assignment.is_planned() is True
    assert planned_assignment.is_completed() is False
