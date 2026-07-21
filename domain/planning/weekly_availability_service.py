"""Service métier pur de contrôle des disponibilités hebdomadaires."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, time

from domain.missions import MissionOccurrenceAssignment

from .employee_weekly_availability import EmployeeWeeklyAvailability
from .weekly_availability_check_result import WeeklyAvailabilityCheckResult
from .weekly_availability_conflict import WeeklyAvailabilityConflict

_UNCOVERED_REASON = "L’affectation n’est couverte par aucune disponibilité hebdomadaire active du salarié."


class WeeklyAvailabilityService:
    """Contrôle qu'une disponibilité hebdomadaire unique couvre toute l'affectation."""

    def check(
        self,
        assignment: MissionOccurrenceAssignment,
        availabilities: Iterable[EmployeeWeeklyAvailability],
    ) -> WeeklyAvailabilityCheckResult:
        """Retourne un résultat métier sans exception pour une simple absence de couverture."""

        if not isinstance(assignment, MissionOccurrenceAssignment):
            raise ValueError("L'affectation contrôlée doit être une MissionOccurrenceAssignment.")
        availabilities_tuple = _validated_availabilities(availabilities)
        if any(_covers_assignment(assignment, availability) for availability in availabilities_tuple):
            return WeeklyAvailabilityCheckResult(assignment=assignment, covered=True)
        return WeeklyAvailabilityCheckResult(
            assignment=assignment,
            covered=False,
            conflict=WeeklyAvailabilityConflict(
                assignment=assignment,
                employee=assignment.employee,
                occurrence=assignment.occurrence,
                reason=_UNCOVERED_REASON,
            ),
        )


def _validated_availabilities(
    availabilities: Iterable[EmployeeWeeklyAvailability],
) -> tuple[EmployeeWeeklyAvailability, ...]:
    if isinstance(availabilities, (str, bytes)) or not isinstance(availabilities, Iterable):
        raise ValueError("Les disponibilités hebdomadaires à contrôler doivent être un iterable.")
    availabilities_tuple = tuple(availabilities)
    if any(not isinstance(item, EmployeeWeeklyAvailability) for item in availabilities_tuple):
        raise ValueError(
            "Les disponibilités hebdomadaires à contrôler doivent contenir uniquement des EmployeeWeeklyAvailability."
        )
    return availabilities_tuple


def _covers_assignment(
    assignment: MissionOccurrenceAssignment,
    availability: EmployeeWeeklyAvailability,
) -> bool:
    occurrence = assignment.occurrence
    if occurrence.starts_at.date() != occurrence.ends_at.date():
        return False
    if availability.employee.id != assignment.employee.id or not availability.is_active():
        return False
    if not availability.applies_on(occurrence.starts_at.date()):
        return False
    if not _has_compatible_time(availability.starts_at, occurrence.starts_at):
        return False
    if not _has_compatible_time(availability.ends_at, occurrence.ends_at):
        return False
    start_time = _comparison_time(occurrence.starts_at, availability.starts_at)
    end_time = _comparison_time(occurrence.ends_at, availability.ends_at)
    return availability.starts_at <= start_time and end_time <= availability.ends_at


def _has_compatible_time(availability_time: time, occurrence_datetime: datetime) -> bool:
    occurrence_is_aware = _is_aware_datetime(occurrence_datetime)
    availability_is_aware = _is_aware_time(availability_time)
    if availability_is_aware != occurrence_is_aware:
        return False
    if availability_is_aware and availability_time.tzinfo != occurrence_datetime.tzinfo:
        return False
    return True


def _comparison_time(occurrence_datetime: datetime, availability_time: time) -> time:
    if _is_aware_time(availability_time):
        return occurrence_datetime.timetz()
    return occurrence_datetime.time()


def _is_aware_datetime(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _is_aware_time(value: time) -> bool:
    return value.tzinfo is not None
