from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from domain.missions import Mission, MissionOccurrence


@pytest.fixture
def mission():
    return Mission(code="animation-alsh", name="Animation ALSH")


@pytest.fixture
def starts_at():
    return datetime(2026, 7, 20, 8, 0)


@pytest.fixture
def ends_at():
    return datetime(2026, 7, 20, 18, 0)


def test_mission_occurrence_is_created_with_minimal_data(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)

    assert occurrence.mission == mission
    assert occurrence.starts_at == starts_at
    assert occurrence.ends_at == ends_at
    assert occurrence.location is None
    assert occurrence.observations is None
    assert occurrence.active is True


def test_mission_occurrence_is_created_with_all_data(mission, starts_at, ends_at):
    occurrence_id = uuid4()
    occurrence = MissionOccurrence(
        id=occurrence_id,
        mission=mission,
        starts_at=starts_at,
        ends_at=ends_at,
        location="  Gymnase municipal  ",
        observations="  Séance multisports.  ",
        active=False,
    )

    assert occurrence.id == occurrence_id
    assert occurrence.location == "Gymnase municipal"
    assert occurrence.observations == "Séance multisports."
    assert occurrence.active is False


def test_mission_occurrence_generates_an_identifier_automatically(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)

    assert isinstance(occurrence.id, type(uuid4()))


def test_mission_occurrence_accepts_an_explicit_uuid(mission, starts_at, ends_at):
    occurrence_id = uuid4()

    occurrence = MissionOccurrence(
        id=occurrence_id, mission=mission, starts_at=starts_at, ends_at=ends_at
    )

    assert occurrence.id == occurrence_id


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"mission": None}, "Mission"),
        ({"mission": "invalid"}, "Mission"),
        ({"starts_at": None}, "début"),
        ({"ends_at": None}, "fin"),
        ({"starts_at": date(2026, 7, 20)}, "début"),
        ({"ends_at": date(2026, 7, 20)}, "fin"),
        ({"starts_at": "2026-07-20T08:00:00"}, "début"),
        ({"ends_at": "2026-07-20T18:00:00"}, "fin"),
        ({"active": 1}, "booléen"),
        ({"location": "  "}, "lieu"),
        ({"location": 42}, "lieu"),
        ({"observations": "  "}, "observations"),
        ({"observations": 42}, "observations"),
    ],
)
def test_mission_occurrence_rejects_invalid_data(mission, starts_at, ends_at, kwargs, message):
    data = {"mission": mission, "starts_at": starts_at, "ends_at": ends_at}
    data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        MissionOccurrence(**data)


def test_mission_occurrence_rejects_end_before_start(mission):
    with pytest.raises(ValueError, match="postérieure"):
        MissionOccurrence(
            mission=mission,
            starts_at=datetime(2026, 7, 20, 18, 0),
            ends_at=datetime(2026, 7, 20, 8, 0),
        )


def test_mission_occurrence_rejects_identical_start_and_end(mission, starts_at):
    with pytest.raises(ValueError, match="postérieure"):
        MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=starts_at)


def test_mission_occurrence_accepts_end_after_start(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)

    assert occurrence.ends_at > occurrence.starts_at


def test_mission_occurrence_rejects_mixed_naive_and_aware_datetimes(mission):
    with pytest.raises(ValueError, match="fuseau horaire"):
        MissionOccurrence(
            mission=mission,
            starts_at=datetime(2026, 7, 20, 8, 0),
            ends_at=datetime(2026, 7, 20, 18, 0, tzinfo=timezone.utc),
        )


def test_mission_occurrence_accepts_two_naive_datetimes(mission):
    occurrence = MissionOccurrence(
        mission=mission,
        starts_at=datetime(2026, 7, 20, 8, 0),
        ends_at=datetime(2026, 7, 20, 18, 0),
    )

    assert occurrence.starts_at.tzinfo is None
    assert occurrence.ends_at.tzinfo is None


def test_mission_occurrence_accepts_two_aware_datetimes(mission):
    occurrence = MissionOccurrence(
        mission=mission,
        starts_at=datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 20, 18, 0, tzinfo=timezone.utc),
    )

    assert occurrence.starts_at.tzinfo == timezone.utc
    assert occurrence.ends_at.tzinfo == timezone.utc


def test_mission_occurrence_normalizes_location(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(
        mission=mission, starts_at=starts_at, ends_at=ends_at, location="  Salle 1  "
    )

    assert occurrence.location == "Salle 1"


def test_mission_occurrence_normalizes_observations(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(
        mission=mission,
        starts_at=starts_at,
        ends_at=ends_at,
        observations="  Prévoir matériel.  ",
    )

    assert occurrence.observations == "Prévoir matériel."


def test_mission_occurrence_is_immutable(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)

    with pytest.raises(FrozenInstanceError):
        occurrence.active = False


def test_mission_occurrence_duration(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)

    assert occurrence.duration() == timedelta(hours=10)


def test_mission_occurrence_has_location(mission, starts_at, ends_at):
    without_location = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)
    with_location = MissionOccurrence(
        mission=mission, starts_at=starts_at, ends_at=ends_at, location="Gymnase"
    )

    assert without_location.has_location() is False
    assert with_location.has_location() is True


def test_mission_occurrence_is_active_returns_declared_value_only(mission):
    past_active = MissionOccurrence(
        mission=mission,
        starts_at=datetime(2026, 1, 1, 8, 0),
        ends_at=datetime(2026, 1, 1, 18, 0),
        active=True,
    )
    current_inactive = MissionOccurrence(
        mission=mission,
        starts_at=datetime(2026, 7, 20, 8, 0),
        ends_at=datetime(2026, 7, 20, 18, 0),
        active=False,
    )

    assert past_active.is_active() is True
    assert current_inactive.is_active() is False


def test_mission_occurrence_occurs_on_matching_day(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)

    assert occurrence.occurs_on(date(2026, 7, 20)) is True


def test_mission_occurrence_does_not_occur_on_another_day(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)

    assert occurrence.occurs_on(date(2026, 7, 21)) is False


def test_mission_occurrence_occurs_on_rejects_datetime(mission, starts_at, ends_at):
    occurrence = MissionOccurrence(mission=mission, starts_at=starts_at, ends_at=ends_at)

    with pytest.raises(ValueError, match="date"):
        occurrence.occurs_on(datetime(2026, 7, 20, 0, 0))
