"""Résultat immutable d'une évaluation de conflits de planning."""

from __future__ import annotations

from dataclasses import dataclass

from domain.missions import MissionOccurrenceAssignment
from domain.people import Employee

from .planning_conflict import PlanningConflict


@dataclass(frozen=True, slots=True)
class PlanningConflictResult:
    """Regroupe les affectations retenues et les conflits détectés."""

    employee: Employee
    considered_assignments: tuple[MissionOccurrenceAssignment, ...]
    conflicts: tuple[PlanningConflict, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié évalué doit être un Employee.")
        considered_assignments = tuple(self.considered_assignments)
        conflicts = tuple(self.conflicts)
        if any(not isinstance(a, MissionOccurrenceAssignment) for a in considered_assignments):
            raise ValueError("Les affectations retenues doivent être des MissionOccurrenceAssignment.")
        if any(a.employee.id != self.employee.id for a in considered_assignments):
            raise ValueError("Les affectations retenues doivent concerner le salarié évalué.")
        if any(not isinstance(conflict, PlanningConflict) for conflict in conflicts):
            raise ValueError("Les conflits doivent être des PlanningConflict.")
        if any(not conflict.involves_employee(self.employee) for conflict in conflicts):
            raise ValueError("Les conflits doivent concerner le salarié évalué.")
        object.__setattr__(self, "considered_assignments", considered_assignments)
        object.__setattr__(self, "conflicts", conflicts)

    def has_conflicts(self) -> bool:
        """Retourne ``True`` lorsqu'au moins un conflit est détecté."""

        return bool(self.conflicts)

    def conflict_count(self) -> int:
        """Retourne le nombre de conflits détectés."""

        return len(self.conflicts)

    def considered_assignment_count(self) -> int:
        """Retourne le nombre d'affectations retenues après filtrage."""

        return len(self.considered_assignments)
