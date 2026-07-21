from dataclasses import FrozenInstanceError
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from domain.people import Civility, Employee
from domain.planning import EmployeeWeeklyAvailability, Weekday


@pytest.fixture
def employee():
    return Employee(civility=Civility.MONSIEUR, first_name="Alan", last_name="Turing")


def availability(employee_value=None, **kwargs):
    data = {
        "employee": employee_value,
        "weekday": Weekday.MONDAY,
        "starts_at": time(9),
        "ends_at": time(17),
    }
    data.update(kwargs)
    return EmployeeWeeklyAvailability(**data)


def test_weekday_values_and_iso_numbers_are_defined():
    assert list(Weekday) == [
        Weekday.MONDAY,
        Weekday.TUESDAY,
        Weekday.WEDNESDAY,
        Weekday.THURSDAY,
        Weekday.FRIDAY,
        Weekday.SATURDAY,
        Weekday.SUNDAY,
    ]
    assert [day.value for day in Weekday] == [1, 2, 3, 4, 5, 6, 7]


@pytest.mark.parametrize("number", range(1, 8))
def test_weekday_from_iso_weekday_returns_matching_day(number):
    assert Weekday.from_iso_weekday(number) is Weekday(number)


@pytest.mark.parametrize("value", [0, 8, -1, "1", True, False])
def test_weekday_from_iso_weekday_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        Weekday.from_iso_weekday(value)


def test_employee_weekly_availability_is_created_with_minimal_data(employee):
    item = availability(employee)

    assert isinstance(item.id, UUID)
    assert item.employee == employee
    assert item.weekday is Weekday.MONDAY
    assert item.starts_at == time(9)
    assert item.ends_at == time(17)
    assert item.effective_from is None
    assert item.effective_until is None
    assert item.label is None
    assert item.observations is None
    assert item.active is True


def test_employee_weekly_availability_is_created_with_all_data(employee):
    item_id = uuid4()
    item = availability(
        employee,
        id=item_id,
        weekday=Weekday.SATURDAY,
        starts_at=time(10, tzinfo=timezone.utc),
        ends_at=time(18, tzinfo=timezone.utc),
        effective_from=date(2026, 7, 1),
        effective_until=date(2026, 7, 31),
        label="  Samedi  ",
        observations="  Accueil public.  ",
        active=False,
    )

    assert item.id == item_id
    assert item.weekday is Weekday.SATURDAY
    assert item.starts_at == time(10, tzinfo=timezone.utc)
    assert item.ends_at == time(18, tzinfo=timezone.utc)
    assert item.effective_from == date(2026, 7, 1)
    assert item.effective_until == date(2026, 7, 31)
    assert item.label == "Samedi"
    assert item.observations == "Accueil public."
    assert item.active is False


def test_employee_weekly_availability_accepts_an_explicit_uuid(employee):
    item_id = uuid4()

    assert availability(employee, id=item_id).id == item_id


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"employee": None}, "Employee"),
        ({"employee": "invalid"}, "Employee"),
        ({"weekday": None}, "Weekday"),
        ({"weekday": 1}, "Weekday"),
        ({"starts_at": None}, "time"),
        ({"ends_at": None}, "time"),
        ({"starts_at": datetime(2026, 7, 20, 9)}, "time"),
        ({"ends_at": datetime(2026, 7, 20, 17)}, "time"),
        ({"starts_at": "invalid"}, "time"),
        ({"ends_at": object()}, "time"),
        ({"ends_at": time(8)}, "strictement postérieure"),
        ({"ends_at": time(9)}, "strictement postérieure"),
        ({"starts_at": time(22), "ends_at": time(6)}, "minuit"),
        ({"ends_at": time(17, tzinfo=timezone.utc)}, "fuseau horaire"),
        ({"starts_at": time(9, tzinfo=timezone.utc), "ends_at": time(17, tzinfo=timezone(timedelta(hours=1)))}, "fuseaux horaires compatibles"),
        ({"effective_from": datetime(2026, 7, 1)}, "date"),
        ({"effective_until": datetime(2026, 7, 31)}, "date"),
        ({"effective_from": "invalid"}, "date"),
        ({"effective_until": date(2026, 6, 30), "effective_from": date(2026, 7, 1)}, "supérieure ou égale"),
        ({"active": 1}, "booléen"),
        ({"label": "  "}, "libellé"),
        ({"label": 42}, "libellé"),
        ({"observations": "  "}, "observations"),
        ({"observations": 42}, "observations"),
    ],
)
def test_employee_weekly_availability_rejects_invalid_data(employee, kwargs, message):
    with pytest.raises(ValueError, match=message):
        availability(employee, **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ends_at": time(9, 1)},
        {"starts_at": time(9), "ends_at": time(17)},
        {"starts_at": time(9, tzinfo=timezone.utc), "ends_at": time(17, tzinfo=timezone.utc)},
        {"effective_from": date(2026, 7, 1)},
        {"effective_until": date(2026, 7, 31)},
        {"effective_from": date(2026, 7, 20), "effective_until": date(2026, 7, 20)},
    ],
)
def test_employee_weekly_availability_accepts_valid_variants(employee, kwargs):
    assert availability(employee, **kwargs).duration() > timedelta(0)


def test_employee_weekly_availability_accepts_same_zoneinfo(employee):
    paris = ZoneInfo("Europe/Paris")
    item = availability(
        employee,
        starts_at=time(9, tzinfo=paris),
        ends_at=time(17, tzinfo=paris),
    )

    assert item.duration() == timedelta(hours=8)
    assert item.contains(datetime(2026, 7, 20, 10, tzinfo=paris)) is True


def test_employee_weekly_availability_rejects_naive_and_zoneinfo_times(employee):
    with pytest.raises(ValueError, match="fuseau horaire"):
        availability(
            employee,
            starts_at=time(9),
            ends_at=time(17, tzinfo=ZoneInfo("Europe/Paris")),
        )


def test_employee_weekly_availability_rejects_different_zoneinfo_times(employee):
    with pytest.raises(ValueError, match="fuseaux horaires compatibles"):
        availability(
            employee,
            starts_at=time(9, tzinfo=ZoneInfo("Europe/Paris")),
            ends_at=time(17, tzinfo=ZoneInfo("Europe/London")),
        )


def test_employee_weekly_availability_is_immutable(employee):
    item = availability(employee)

    with pytest.raises(FrozenInstanceError):
        item.active = False


def test_employee_weekly_availability_methods_return_declared_values(employee):
    item = availability(
        employee,
        label="  Bureau  ",
        observations="  Note  ",
        effective_from=date(2026, 7, 1),
        effective_until=date(2026, 7, 31),
        active=False,
    )

    assert item.duration() == timedelta(hours=8)
    assert item.is_active() is False
    assert item.has_label() is True
    assert item.has_observations() is True
    assert item.has_effective_start() is True
    assert item.has_effective_end() is True


def test_employee_weekly_availability_presence_methods_are_false_when_missing(employee):
    item = availability(employee)

    assert item.has_label() is False
    assert item.has_observations() is False
    assert item.has_effective_start() is False
    assert item.has_effective_end() is False


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 7, 20), True),
        (date(2026, 7, 21), False),
        (date(2026, 7, 13), False),
        (date(2026, 7, 20), True),
        (date(2026, 7, 27), True),
        (date(2026, 8, 3), False),
    ],
)
def test_employee_weekly_availability_applies_on_with_effective_period(employee, day, expected):
    item = availability(employee, effective_from=date(2026, 7, 20), effective_until=date(2026, 7, 27), active=False)

    assert item.applies_on(day) is expected


def test_employee_weekly_availability_applies_on_without_limits(employee):
    assert availability(employee).applies_on(date(2026, 7, 20)) is True


def test_employee_weekly_availability_applies_on_rejects_datetime(employee):
    with pytest.raises(ValueError, match="date"):
        availability(employee).applies_on(datetime(2026, 7, 20, 10))


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 7, 20, 9), True),
        (datetime(2026, 7, 20, 12), True),
        (datetime(2026, 7, 20, 17), False),
        (datetime(2026, 7, 20, 8, 59), False),
        (datetime(2026, 7, 20, 18), False),
        (datetime(2026, 7, 21, 10), False),
    ],
)
def test_employee_weekly_availability_contains_uses_semi_open_interval(employee, moment, expected):
    assert availability(employee).contains(moment) is expected


def test_employee_weekly_availability_contains_returns_false_outside_effective_period(employee):
    item = availability(employee, effective_from=date(2026, 7, 27))

    assert item.contains(datetime(2026, 7, 20, 10)) is False


def test_employee_weekly_availability_contains_accepts_aware_compatible_datetime(employee):
    item = availability(employee, starts_at=time(9, tzinfo=timezone.utc), ends_at=time(17, tzinfo=timezone.utc))

    assert item.contains(datetime(2026, 7, 20, 10, tzinfo=timezone.utc)) is True


@pytest.mark.parametrize(
    "moment",
    [
        date(2026, 7, 20),
        "invalid",
        datetime(2026, 7, 20, 10, tzinfo=timezone.utc),
    ],
)
def test_employee_weekly_availability_contains_rejects_invalid_or_incompatible_values(employee, moment):
    with pytest.raises(ValueError):
        availability(employee).contains(moment)


def test_employee_weekly_availability_contains_rejects_incompatible_timezone(employee):
    item = availability(employee, starts_at=time(9, tzinfo=timezone.utc), ends_at=time(17, tzinfo=timezone.utc))

    with pytest.raises(ValueError, match="fuseaux horaires compatibles"):
        item.contains(datetime(2026, 7, 20, 10, tzinfo=timezone(timedelta(hours=1))))


def test_employee_weekly_availability_contains_rejects_naive_datetime_for_zoneinfo(employee):
    paris = ZoneInfo("Europe/Paris")
    item = availability(employee, starts_at=time(9, tzinfo=paris), ends_at=time(17, tzinfo=paris))

    with pytest.raises(ValueError, match="fuseau horaire"):
        item.contains(datetime(2026, 7, 20, 10))


def test_employee_weekly_availability_contains_rejects_zoneinfo_datetime_for_naive_times(employee):
    with pytest.raises(ValueError, match="fuseau horaire"):
        availability(employee).contains(
            datetime(2026, 7, 20, 10, tzinfo=ZoneInfo("Europe/Paris"))
        )


def test_employee_weekly_availability_contains_rejects_different_zoneinfo(employee):
    paris = ZoneInfo("Europe/Paris")
    item = availability(employee, starts_at=time(9, tzinfo=paris), ends_at=time(17, tzinfo=paris))

    with pytest.raises(ValueError, match="fuseaux horaires compatibles"):
        item.contains(datetime(2026, 7, 20, 10, tzinfo=ZoneInfo("Europe/London")))


def test_employee_weekly_availability_does_not_convert_zoneinfo_wall_time(employee):
    paris = ZoneInfo("Europe/Paris")
    item = availability(employee, starts_at=time(9, tzinfo=paris), ends_at=time(17, tzinfo=paris))

    assert item.contains(datetime(2026, 7, 20, 9, tzinfo=paris)) is True
    assert item.contains(datetime(2026, 7, 20, 17, tzinfo=paris)) is False


def test_employee_weekly_availability_does_not_consult_current_date_or_time(employee):
    import inspect
    import domain.planning.employee_weekly_availability as module

    source = inspect.getsource(module)

    assert ".now(" not in source
    assert ".today(" not in source
    item = availability(employee, active=False)
    assert item.is_active() is False
    assert item.applies_on(date(2026, 7, 20)) is True
    assert item.contains(datetime(2026, 7, 20, 10)) is True
