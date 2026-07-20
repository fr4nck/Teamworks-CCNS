"""Service métier pur de détection des conflits avec les indisponibilités."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime

from domain.missions import (
    MissionOccurrenceAssignment,
    MissionOccurrenceAssignmentStatus,
)
from domain.people import Employee

from .employee_unavailability import EmployeeUnavailability
from .unavailability_conflict import UnavailabilityConflict
from .unavailability_conflict_result import UnavailabilityConflictResult

_CONSIDERED_STATUSES = {
    MissionOccurrenceAssignmentStatus.PLANNED,
    MissionOccurrenceAssignmentStatus.CONFIRMED,
}


class UnavailabilityConflictService:
    """Détecte les chevauchements directs entre affectations et indisponibilités."""

    def evaluate(
        self,
        employee: Employee,
        assignments: Collection[MissionOccurrenceAssignment],
        unavailabilities: Collection[EmployeeUnavailability],
    ) -> UnavailabilityConflictResult:
        """Évalue les conflits horaires directs pour le salarié fourni."""

        if not isinstance(employee, Employee):
            raise ValueError("Le salarié évalué doit être un Employee.")
        assignments_tuple = _validated_assignments(assignments)
        unavailabilities_tuple = _validated_unavailabilities(unavailabilities)
        considered_assignments = _considered_assignments(employee, assignments_tuple)
        considered_unavailabilities = _considered_unavailabilities(
            employee, unavailabilities_tuple
        )
        conflicts: list[UnavailabilityConflict] = []
        for assignment in considered_assignments:
            for unavailability in considered_unavailabilities:
                _ensure_compatible_datetimes(assignment, unavailability)
                if _overlaps(assignment, unavailability):
                    conflicts.append(
                        UnavailabilityConflict(
                            assignment=assignment,
                            unavailability=unavailability,
                            overlap_start=max(
                                assignment.occurrence.starts_at,
                                unavailability.starts_at,
                            ),
                            overlap_end=min(
                                assignment.occurrence.ends_at,
                                unavailability.ends_at,
                            ),
                        )
                    )
        return UnavailabilityConflictResult(
            employee=employee,
            considered_assignments=considered_assignments,
            considered_unavailabilities=considered_unavailabilities,
            conflicts=tuple(conflicts),
        )


def _validated_assignments(
    assignments: Collection[MissionOccurrenceAssignment],
) -> tuple[MissionOccurrenceAssignment, ...]:
    if isinstance(assignments, (str, bytes)) or not isinstance(assignments, Collection):
        raise ValueError("Les affectations à évaluer doivent être une collection.")
    assignments_tuple = tuple(assignments)
    if any(
        not isinstance(assignment, MissionOccurrenceAssignment)
        for assignment in assignments_tuple
    ):
        raise ValueError(
            "Les affectations à évaluer doivent contenir uniquement des "
            "MissionOccurrenceAssignment."
        )
    return assignments_tuple


def _validated_unavailabilities(
    unavailabilities: Collection[EmployeeUnavailability],
) -> tuple[EmployeeUnavailability, ...]:
    if isinstance(unavailabilities, (str, bytes)) or not isinstance(
        unavailabilities, Collection
    ):
        raise ValueError("Les indisponibilités à évaluer doivent être une collection.")
    unavailabilities_tuple = tuple(unavailabilities)
    if any(
        not isinstance(unavailability, EmployeeUnavailability)
        for unavailability in unavailabilities_tuple
    ):
        raise ValueError(
            "Les indisponibilités à évaluer doivent contenir uniquement des EmployeeUnavailability."
        )
    return unavailabilities_tuple


def _considered_assignments(
    employee: Employee,
    assignments: tuple[MissionOccurrenceAssignment, ...],
) -> tuple[MissionOccurrenceAssignment, ...]:
    seen_ids = set()
    considered = []
    for assignment in assignments:
        if assignment.id in seen_ids:
            continue
        seen_ids.add(assignment.id)
        if (
            assignment.employee.id == employee.id
            and assignment.is_active()
            and assignment.occurrence.is_active()
            and assignment.status in _CONSIDERED_STATUSES
        ):
            considered.append(assignment)
    return tuple(considered)


def _considered_unavailabilities(
    employee: Employee,
    unavailabilities: tuple[EmployeeUnavailability, ...],
) -> tuple[EmployeeUnavailability, ...]:
    seen_ids = set()
    considered = []
    for unavailability in unavailabilities:
        if unavailability.id in seen_ids:
            continue
        seen_ids.add(unavailability.id)
        if unavailability.employee.id == employee.id and unavailability.is_active():
            considered.append(unavailability)
    return tuple(considered)


def _overlaps(
    assignment: MissionOccurrenceAssignment, unavailability: EmployeeUnavailability
) -> bool:
    occurrence = assignment.occurrence
    return (
        occurrence.starts_at < unavailability.ends_at
        and unavailability.starts_at < occurrence.ends_at
    )


def _ensure_compatible_datetimes(
    assignment: MissionOccurrenceAssignment,
    unavailability: EmployeeUnavailability,
) -> None:
    occurrence = assignment.occurrence
    _ensure_pair_compatible(occurrence.starts_at, unavailability.starts_at)
    _ensure_pair_compatible(occurrence.starts_at, unavailability.ends_at)
    _ensure_pair_compatible(occurrence.ends_at, unavailability.starts_at)
    _ensure_pair_compatible(occurrence.ends_at, unavailability.ends_at)


def _ensure_pair_compatible(first: datetime, second: datetime) -> None:
    if _is_aware(first) != _is_aware(second):
        raise ValueError(
            "Les périodes comparées doivent utiliser des datetime tous naïfs ou tous avec fuseau horaire."
        )
    if _is_aware(first) and first.tzinfo != second.tzinfo:
        raise ValueError(
            "Les périodes comparées doivent utiliser des fuseaux horaires compatibles."
        )


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None
