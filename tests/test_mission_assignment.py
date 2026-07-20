from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from domain.missions import Mission, MissionAssignment
from domain.people import Civility, Employee


@pytest.fixture
def employee():
    return Employee(civility=Civility.MADAME, first_name="Ada", last_name="Lovelace")


@pytest.fixture
def mission():
    return Mission(code="animation-alsh", name="Animation ALSH")


def test_mission_assignment_is_created_with_minimal_data(employee, mission):
    assignment = MissionAssignment(employee=employee, mission=mission)

    assert assignment.employee == employee
    assert assignment.mission == mission
    assert assignment.starts_on is None
    assert assignment.ends_on is None
    assert assignment.active is True
    assert assignment.observations is None


def test_mission_assignment_is_created_with_all_data(employee, mission):
    assignment_id = uuid4()
    assignment = MissionAssignment(
        id=assignment_id,
        employee=employee,
        mission=mission,
        starts_on=date(2026, 1, 1),
        ends_on=date(2026, 12, 31),
        active=False,
        observations="  Affectation saisonnière.  ",
    )

    assert assignment.id == assignment_id
    assert assignment.starts_on == date(2026, 1, 1)
    assert assignment.ends_on == date(2026, 12, 31)
    assert assignment.active is False
    assert assignment.observations == "Affectation saisonnière."


def test_mission_assignment_generates_an_identifier_automatically(employee, mission):
    assert isinstance(MissionAssignment(employee=employee, mission=mission).id, type(uuid4()))


def test_mission_assignment_accepts_an_explicit_uuid(employee, mission):
    assignment_id = uuid4()

    assert MissionAssignment(id=assignment_id, employee=employee, mission=mission).id == assignment_id


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"employee": None}, "Employee"),
        ({"employee": "invalid"}, "Employee"),
        ({"mission": None}, "Mission"),
        ({"mission": "invalid"}, "Mission"),
        ({"starts_on": "2026-01-01"}, "date de début"),
        ({"ends_on": "2026-01-31"}, "date de fin"),
        ({"starts_on": datetime(2026, 1, 1, 9, 0)}, "date de début"),
        ({"ends_on": datetime(2026, 1, 31, 18, 0)}, "date de fin"),
        ({"active": 1}, "booléen"),
        ({"observations": "  "}, "observations"),
        ({"observations": 42}, "observations"),
    ],
)
def test_mission_assignment_rejects_invalid_data(employee, mission, kwargs, message):
    data = {"employee": employee, "mission": mission}
    data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        MissionAssignment(**data)


def test_mission_assignment_rejects_end_date_before_start_date(employee, mission):
    with pytest.raises(ValueError, match="antérieure"):
        MissionAssignment(
            employee=employee,
            mission=mission,
            starts_on=date(2026, 2, 1),
            ends_on=date(2026, 1, 31),
        )


def test_mission_assignment_accepts_identical_start_and_end_dates(employee, mission):
    assignment = MissionAssignment(
        employee=employee,
        mission=mission,
        starts_on=date(2026, 2, 1),
        ends_on=date(2026, 2, 1),
    )

    assert assignment.starts_on == assignment.ends_on


def test_mission_assignment_is_immutable(employee, mission):
    assignment = MissionAssignment(employee=employee, mission=mission)

    with pytest.raises(FrozenInstanceError):
        assignment.active = False


def test_mission_assignment_date_helpers(employee, mission):
    assignment = MissionAssignment(
        employee=employee,
        mission=mission,
        starts_on=date(2026, 1, 1),
        ends_on=date(2026, 1, 31),
    )
    open_assignment = MissionAssignment(employee=employee, mission=mission)

    assert assignment.has_start_date()
    assert assignment.has_end_date()
    assert not assignment.is_open_ended()
    assert open_assignment.is_open_ended()


def test_mission_assignment_is_active_returns_declared_value_only(employee, mission):
    past_assignment = MissionAssignment(
        employee=employee,
        mission=mission,
        starts_on=date.today() - timedelta(days=30),
        ends_on=date.today() - timedelta(days=1),
        active=True,
    )
    open_inactive_assignment = MissionAssignment(employee=employee, mission=mission, active=False)

    assert past_assignment.is_active() is True
    assert open_inactive_assignment.is_active() is False
