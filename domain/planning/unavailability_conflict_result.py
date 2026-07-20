"""Résultat immutable d'une évaluation de conflits d'indisponibilité."""

from __future__ import annotations

from dataclasses import dataclass

from domain.missions import MissionOccurrenceAssignment
from domain.people import Employee

from .employee_unavailability import EmployeeUnavailability
from .unavailability_conflict import UnavailabilityConflict


@dataclass(frozen=True, slots=True)
class UnavailabilityConflictResult:
    """Regroupe les éléments retenus et les conflits d'indisponibilité détectés."""

    employee: Employee
    considered_assignments: tuple[MissionOccurrenceAssignment, ...]
    considered_unavailabilities: tuple[EmployeeUnavailability, ...]
    conflicts: tuple[UnavailabilityConflict, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié évalué doit être un Employee.")
        considered_assignments = tuple(self.considered_assignments)
        considered_unavailabilities = tuple(self.considered_unavailabilities)
        conflicts = tuple(self.conflicts)
        if any(
            not isinstance(a, MissionOccurrenceAssignment)
            for a in considered_assignments
        ):
            raise ValueError(
                "Les affectations retenues doivent être des MissionOccurrenceAssignment."
            )
        if any(a.employee.id != self.employee.id for a in considered_assignments):
            raise ValueError(
                "Les affectations retenues doivent concerner le salarié évalué."
            )
        if any(
            not isinstance(u, EmployeeUnavailability)
            for u in considered_unavailabilities
        ):
            raise ValueError(
                "Les indisponibilités retenues doivent être des EmployeeUnavailability."
            )
        if any(u.employee.id != self.employee.id for u in considered_unavailabilities):
            raise ValueError(
                "Les indisponibilités retenues doivent concerner le salarié évalué."
            )
        if any(
            not isinstance(conflict, UnavailabilityConflict) for conflict in conflicts
        ):
            raise ValueError("Les conflits doivent être des UnavailabilityConflict.")
        if any(not conflict.involves_employee(self.employee) for conflict in conflicts):
            raise ValueError("Les conflits doivent concerner le salarié évalué.")
        object.__setattr__(self, "considered_assignments", considered_assignments)
        object.__setattr__(
            self, "considered_unavailabilities", considered_unavailabilities
        )
        object.__setattr__(self, "conflicts", conflicts)

    def has_conflicts(self) -> bool:
        """Retourne ``True`` lorsqu'au moins un conflit est détecté."""

        return bool(self.conflicts)

    def conflict_count(self) -> int:
        """Retourne le nombre de conflits détectés."""

        return len(self.conflicts)

    def considered_assignment_count(self) -> int:
        """Retourne le nombre d'affectations retenues après filtrage et déduplication."""

        return len(self.considered_assignments)

    def considered_unavailability_count(self) -> int:
        """Retourne le nombre d'indisponibilités retenues après filtrage et déduplication."""

        return len(self.considered_unavailabilities)
