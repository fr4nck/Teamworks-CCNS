"""Service métier pur de détection des conflits horaires de planning."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime

from domain.missions import MissionOccurrenceAssignment, MissionOccurrenceAssignmentStatus
from domain.people import Employee

from .planning_conflict import PlanningConflict
from .planning_conflict_result import PlanningConflictResult

_CONSIDERED_STATUSES = {
    MissionOccurrenceAssignmentStatus.PLANNED,
    MissionOccurrenceAssignmentStatus.CONFIRMED,
}


class PlanningConflictService:
    """Détecte les chevauchements directs entre affectations actives d'un salarié."""

    def evaluate(
        self,
        employee: Employee,
        assignments: Collection[MissionOccurrenceAssignment],
    ) -> PlanningConflictResult:
        """Évalue les conflits horaires directs dans la collection d'affectations fournie."""

        if not isinstance(employee, Employee):
            raise ValueError("Le salarié évalué doit être un Employee.")
        assignments_tuple = _validated_assignments(assignments)
        considered_assignments = _considered_assignments(employee, assignments_tuple)
        conflicts: list[PlanningConflict] = []
        for index, first_assignment in enumerate(considered_assignments):
            for second_assignment in considered_assignments[index + 1 :]:
                _ensure_compatible_datetimes(first_assignment, second_assignment)
                if _overlaps(first_assignment, second_assignment):
                    conflicts.append(
                        PlanningConflict(
                            first_assignment=first_assignment,
                            second_assignment=second_assignment,
                            overlap_start=max(
                                first_assignment.occurrence.starts_at,
                                second_assignment.occurrence.starts_at,
                            ),
                            overlap_end=min(
                                first_assignment.occurrence.ends_at,
                                second_assignment.occurrence.ends_at,
                            ),
                        )
                    )
        return PlanningConflictResult(
            employee=employee,
            considered_assignments=considered_assignments,
            conflicts=tuple(conflicts),
        )


def _validated_assignments(
    assignments: Collection[MissionOccurrenceAssignment],
) -> tuple[MissionOccurrenceAssignment, ...]:
    if isinstance(assignments, (str, bytes)) or not isinstance(assignments, Collection):
        raise ValueError("Les affectations à évaluer doivent être une collection.")
    assignments_tuple = tuple(assignments)
    if any(not isinstance(assignment, MissionOccurrenceAssignment) for assignment in assignments_tuple):
        raise ValueError(
            "Les affectations à évaluer doivent contenir uniquement des "
            "MissionOccurrenceAssignment."
        )
    return assignments_tuple


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


def _overlaps(
    first_assignment: MissionOccurrenceAssignment,
    second_assignment: MissionOccurrenceAssignment,
) -> bool:
    first = first_assignment.occurrence
    second = second_assignment.occurrence
    return first.starts_at < second.ends_at and second.starts_at < first.ends_at


def _ensure_compatible_datetimes(
    first_assignment: MissionOccurrenceAssignment,
    second_assignment: MissionOccurrenceAssignment,
) -> None:
    first = first_assignment.occurrence
    second = second_assignment.occurrence
    if _is_aware(first.starts_at) != _is_aware(second.starts_at):
        raise ValueError(
            "Les occurrences comparées doivent utiliser des datetime tous naïfs ou tous avec fuseau horaire."
        )


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None
