from dataclasses import FrozenInstanceError
from datetime import date, datetime, time, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from domain.missions import Mission, MissionOccurrence, MissionOccurrenceAssignment, MissionOccurrenceAssignmentStatus
from domain.people import Civility, Employee
from domain.planning import (
    EmployeeWeeklyAvailability,
    Weekday,
    WeeklyAvailabilityCheckResult,
    WeeklyAvailabilityConflict,
    WeeklyAvailabilityService,
)

REASON = "L’affectation n’est couverte par aucune disponibilité hebdomadaire active du salarié."


def employee(first="Ada"):
    return Employee(civility=Civility.MADAME, first_name=first, last_name="Lovelace")


def assignment(emp=None, starts=None, ends=None):
    emp = emp or employee()
    mission = Mission(code="accueil", name="Accueil")
    occurrence = MissionOccurrence(
        mission=mission,
        starts_at=starts or datetime(2026, 7, 20, 9),
        ends_at=ends or datetime(2026, 7, 20, 17),
    )
    return MissionOccurrenceAssignment(
        employee=emp,
        occurrence=occurrence,
        status=MissionOccurrenceAssignmentStatus.PLANNED,
    )


def availability(emp, **kwargs):
    data = {"employee": emp, "weekday": Weekday.MONDAY, "starts_at": time(9), "ends_at": time(17)}
    data.update(kwargs)
    return EmployeeWeeklyAvailability(**data)


def check(assign, availabilities):
    return WeeklyAvailabilityService().check(assign, availabilities)


@pytest.mark.parametrize(
    "avail_kwargs",
    [
        {},
        {"starts_at": time(8), "ends_at": time(18)},
        {"starts_at": time(9), "ends_at": time(18)},
    ],
)
def test_resultat_couvert_quand_disponibilite_unique_couvre_affectation(avail_kwargs):
    assign = assignment()

    result = check(assign, [availability(assign.employee, **avail_kwargs)])

    assert result.is_covered() is True
    assert result.has_conflict() is False
    assert result.conflict is None


def test_fin_affectation_egale_a_fin_disponibilite_acceptee():
    assign = assignment(starts=datetime(2026, 7, 20, 15), ends=datetime(2026, 7, 20, 17))

    assert check(assign, [availability(assign.employee, starts_at=time(9), ends_at=time(17))]).covered is True


@pytest.mark.parametrize(
    "items",
    [
        [],
        lambda assign: [availability(employee("Grace"))],
        lambda assign: [availability(assign.employee, active=False)],
        lambda assign: [availability(assign.employee, weekday=Weekday.TUESDAY)],
        lambda assign: [availability(assign.employee, starts_at=time(10), ends_at=time(17))],
        lambda assign: [availability(assign.employee, starts_at=time(9), ends_at=time(16))],
        lambda assign: [availability(assign.employee, starts_at=time(9), ends_at=time(12))],
        lambda assign: [
            availability(assign.employee, starts_at=time(9), ends_at=time(12)),
            availability(assign.employee, starts_at=time(12), ends_at=time(17)),
        ],
        lambda assign: [availability(assign.employee, effective_from=date(2026, 7, 21))],
    ],
)
def test_resultat_non_couvert_pour_cas_metier_attendus(items):
    assign = assignment()
    availabilities = items(assign) if callable(items) else items

    result = check(assign, availabilities)

    assert result.is_covered() is False
    assert result.has_conflict() is True
    assert result.conflict.reason == REASON
    assert result.conflict.assignment == assign
    assert result.conflict.employee == assign.employee
    assert result.conflict.occurrence == assign.occurrence


def test_affectation_sur_plusieurs_dates_refusee():
    assign = assignment(starts=datetime(2026, 7, 20, 22), ends=datetime(2026, 7, 21, 1))

    assert check(assign, [availability(assign.employee, starts_at=time(0), ends_at=time(23, 59))]).covered is False


@pytest.mark.parametrize("bad_collection", [None, "abc", b"abc", 42])
def test_collection_invalide_refusee(bad_collection):
    with pytest.raises(ValueError, match="iterable"):
        check(assignment(), bad_collection)


def test_element_invalide_refuse():
    with pytest.raises(ValueError, match="EmployeeWeeklyAvailability"):
        check(assignment(), [object()])


def test_iterable_est_materialise_une_seule_fois_sans_modifier_collection():
    assign = assignment()
    source = [availability(assign.employee)]
    generated = (item for item in source)

    assert check(assign, generated).covered is True
    assert len(source) == 1


def test_booleens_stricts_uuid_strict_immutabilite_et_coherence():
    assign = assignment()
    conflict = WeeklyAvailabilityConflict(
        assignment=assign,
        employee=assign.employee,
        occurrence=assign.occurrence,
        reason="  raison  ",
        id=uuid4(),
    )
    assert conflict.reason == "raison"
    assert conflict.has_reason() is True
    assert WeeklyAvailabilityCheckResult(assignment=assign, covered=False, conflict=conflict).has_conflict() is True
    with pytest.raises(ValueError, match="UUID"):
        WeeklyAvailabilityConflict(assignment=assign, employee=assign.employee, occurrence=assign.occurrence, reason="x", id="bad")
    with pytest.raises(ValueError, match="booléen"):
        WeeklyAvailabilityCheckResult(assignment=assign, covered=1)
    with pytest.raises(ValueError, match="conflit"):
        WeeklyAvailabilityCheckResult(assignment=assign, covered=True, conflict=conflict)
    other = assignment()
    with pytest.raises(ValueError, match="même affectation"):
        WeeklyAvailabilityCheckResult(assignment=other, covered=False, conflict=conflict)
    with pytest.raises(FrozenInstanceError):
        conflict.reason = "autre"


def test_compatibilite_timezone_utc_et_zoneinfo():
    utc_assign = assignment(starts=datetime(2026, 7, 20, 9, tzinfo=timezone.utc), ends=datetime(2026, 7, 20, 17, tzinfo=timezone.utc))
    assert check(utc_assign, [availability(utc_assign.employee, starts_at=time(9, tzinfo=timezone.utc), ends_at=time(17, tzinfo=timezone.utc))]).covered is True

    paris = ZoneInfo("Europe/Paris")
    paris_assign = assignment(starts=datetime(2026, 7, 20, 9, tzinfo=paris), ends=datetime(2026, 7, 20, 17, tzinfo=paris))
    assert check(paris_assign, [availability(paris_assign.employee, starts_at=time(9, tzinfo=paris), ends_at=time(17, tzinfo=paris))]).covered is True


def test_incompatibilites_de_fuseau_donnent_non_couvert_sans_conversion():
    paris = ZoneInfo("Europe/Paris")
    london = ZoneInfo("Europe/London")
    zoned_assign = assignment(starts=datetime(2026, 7, 20, 9, tzinfo=paris), ends=datetime(2026, 7, 20, 17, tzinfo=paris))
    assert check(zoned_assign, [availability(zoned_assign.employee)]).covered is False
    assert check(zoned_assign, [availability(zoned_assign.employee, starts_at=time(8, tzinfo=london), ends_at=time(16, tzinfo=london))]).covered is False
