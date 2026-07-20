from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from domain.people import Civility, Employee
from domain.planning import EmployeeUnavailability, EmployeeUnavailabilityReason


@pytest.fixture
def employee():
    return Employee(civility=Civility.MADAME, first_name="Ada", last_name="Lovelace")


def unavailability(employee_value=None, **kwargs):
    data = {
        "employee": employee_value,
        "starts_at": datetime(2026, 7, 20, 9),
        "ends_at": datetime(2026, 7, 20, 12),
        "reason": EmployeeUnavailabilityReason.LEAVE,
    }
    data.update(kwargs)
    return EmployeeUnavailability(**data)


def test_employee_unavailability_is_created_with_minimal_data(employee):
    item = unavailability(employee)

    assert item.employee == employee
    assert item.starts_at == datetime(2026, 7, 20, 9)
    assert item.ends_at == datetime(2026, 7, 20, 12)
    assert item.reason is EmployeeUnavailabilityReason.LEAVE
    assert item.label is None
    assert item.observations is None
    assert item.active is True


def test_employee_unavailability_is_created_with_all_data(employee):
    item_id = uuid4()
    item = unavailability(
        employee,
        id=item_id,
        reason=EmployeeUnavailabilityReason.TRAINING,
        label="  Formation PSC1  ",
        observations="  Prévenir l'équipe.  ",
        active=False,
    )

    assert item.id == item_id
    assert item.reason is EmployeeUnavailabilityReason.TRAINING
    assert item.label == "Formation PSC1"
    assert item.observations == "Prévenir l'équipe."
    assert item.active is False


def test_employee_unavailability_generates_an_identifier_automatically(employee):
    assert isinstance(unavailability(employee).id, UUID)


def test_employee_unavailability_accepts_an_explicit_uuid(employee):
    item_id = uuid4()

    assert unavailability(employee, id=item_id).id == item_id


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"employee": None}, "Employee"),
        ({"employee": "invalid"}, "Employee"),
        ({"starts_at": None}, "datetime"),
        ({"ends_at": None}, "datetime"),
        ({"starts_at": date(2026, 7, 20)}, "datetime"),
        ({"ends_at": date(2026, 7, 20)}, "datetime"),
        ({"starts_at": "invalid"}, "datetime"),
        ({"ends_at": object()}, "datetime"),
        ({"ends_at": datetime(2026, 7, 20, 8)}, "strictement postérieure"),
        ({"ends_at": datetime(2026, 7, 20, 9)}, "strictement postérieure"),
        ({"reason": None}, "EmployeeUnavailabilityReason"),
        ({"reason": "LEAVE"}, "EmployeeUnavailabilityReason"),
        ({"active": 1}, "booléen"),
        ({"label": "  "}, "libellé"),
        ({"label": 42}, "libellé"),
        ({"observations": "  "}, "observations"),
        ({"observations": 42}, "observations"),
    ],
)
def test_employee_unavailability_rejects_invalid_data(employee, kwargs, message):
    with pytest.raises(ValueError, match=message):
        unavailability(employee, **kwargs)


def test_employee_unavailability_accepts_positive_duration(employee):
    assert unavailability(employee, ends_at=datetime(2026, 7, 20, 9, 1)).duration() == timedelta(minutes=1)


def test_employee_unavailability_accepts_two_naive_datetimes(employee):
    item = unavailability(employee)

    assert item.starts_at.tzinfo is None


def test_employee_unavailability_accepts_two_aware_datetimes(employee):
    item = unavailability(
        employee,
        starts_at=datetime(2026, 7, 20, 9, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 20, 12, tzinfo=timezone.utc),
    )

    assert item.starts_at.tzinfo is timezone.utc


def test_employee_unavailability_rejects_mixed_naive_and_aware_datetimes(employee):
    with pytest.raises(ValueError, match="fuseau horaire"):
        unavailability(employee, ends_at=datetime(2026, 7, 20, 12, tzinfo=timezone.utc))


def test_employee_unavailability_is_immutable(employee):
    item = unavailability(employee)

    with pytest.raises(FrozenInstanceError):
        item.active = False


def test_employee_unavailability_methods_return_declared_values(employee):
    item = unavailability(employee, label="  Absence  ", observations="  Note  ", active=False)

    assert item.duration() == timedelta(hours=3)
    assert item.is_active() is False
    assert item.has_label() is True
    assert item.has_observations() is True


def test_employee_unavailability_has_label_and_observations_are_false_when_missing(employee):
    item = unavailability(employee)

    assert item.has_label() is False
    assert item.has_observations() is False


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (datetime(2026, 7, 20, 8), datetime(2026, 7, 20, 10)),
        (datetime(2026, 7, 20, 10), datetime(2026, 7, 20, 11)),
        (datetime(2026, 7, 20, 9), datetime(2026, 7, 20, 12)),
    ],
)
def test_employee_unavailability_overlaps_when_periods_intersect(employee, start, end):
    assert unavailability(employee).overlaps(start, end) is True


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (datetime(2026, 7, 20, 7), datetime(2026, 7, 20, 9)),
        (datetime(2026, 7, 20, 12), datetime(2026, 7, 20, 13)),
        (datetime(2026, 7, 20, 13), datetime(2026, 7, 20, 14)),
    ],
)
def test_employee_unavailability_does_not_overlap_separate_or_adjacent_periods(employee, start, end):
    assert unavailability(employee).overlaps(start, end) is False


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        (date(2026, 7, 20), datetime(2026, 7, 20, 10), "datetime"),
        (datetime(2026, 7, 20, 10), datetime(2026, 7, 20, 10), "durée"),
        (datetime(2026, 7, 20, 11), datetime(2026, 7, 20, 10), "durée"),
        (datetime(2026, 7, 20, 10, tzinfo=timezone.utc), datetime(2026, 7, 20, 11, tzinfo=timezone.utc), "fuseau"),
    ],
)
def test_employee_unavailability_overlaps_rejects_invalid_intervals(employee, start, end, message):
    with pytest.raises(ValueError, match=message):
        unavailability(employee).overlaps(start, end)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 7, 20, 9), True),
        (datetime(2026, 7, 20, 10), True),
        (datetime(2026, 7, 20, 12), False),
        (datetime(2026, 7, 20, 8), False),
    ],
)
def test_employee_unavailability_contains_uses_semi_open_interval(employee, moment, expected):
    assert unavailability(employee).contains(moment) is expected


@pytest.mark.parametrize("moment", [date(2026, 7, 20), "invalid", datetime(2026, 7, 20, 10, tzinfo=timezone.utc)])
def test_employee_unavailability_contains_rejects_invalid_values(employee, moment):
    with pytest.raises(ValueError):
        unavailability(employee).contains(moment)


def test_employee_unavailability_does_not_consult_current_date(employee):
    import inspect
    import domain.planning.employee_unavailability as module

    source = inspect.getsource(module)

    assert ".now(" not in source
    assert ".today(" not in source
    item = unavailability(employee)
    assert item.is_active() is True
    assert item.overlaps(datetime(2026, 7, 20, 10), datetime(2026, 7, 20, 11)) is True
    assert item.contains(datetime(2026, 7, 20, 10)) is True
