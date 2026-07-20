"""Conflit temporel direct entre deux affectations à des occurrences."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from domain.missions import MissionOccurrenceAssignment
from domain.people import Employee


@dataclass(frozen=True, slots=True)
class PlanningConflict:
    """Décrit le chevauchement horaire de deux affectations d'un même salarié."""

    first_assignment: MissionOccurrenceAssignment
    second_assignment: MissionOccurrenceAssignment
    overlap_start: datetime
    overlap_end: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.first_assignment, MissionOccurrenceAssignment):
            raise ValueError("La première affectation doit être une MissionOccurrenceAssignment.")
        if not isinstance(self.second_assignment, MissionOccurrenceAssignment):
            raise ValueError("La seconde affectation doit être une MissionOccurrenceAssignment.")
        if self.first_assignment.id == self.second_assignment.id:
            raise ValueError("Un conflit de planning doit concerner deux affectations différentes.")
        if self.first_assignment.employee.id != self.second_assignment.employee.id:
            raise ValueError("Un conflit de planning doit concerner un seul et même salarié.")
        if not isinstance(self.overlap_start, datetime):
            raise ValueError("Le début du chevauchement doit être un datetime.")
        if not isinstance(self.overlap_end, datetime):
            raise ValueError("La fin du chevauchement doit être un datetime.")

        expected_start = max(
            self.first_assignment.occurrence.starts_at,
            self.second_assignment.occurrence.starts_at,
        )
        expected_end = min(
            self.first_assignment.occurrence.ends_at,
            self.second_assignment.occurrence.ends_at,
        )
        if self.overlap_start != expected_start:
            raise ValueError("Le début du chevauchement doit correspondre au début le plus tardif.")
        if self.overlap_end != expected_end:
            raise ValueError("La fin du chevauchement doit correspondre à la fin la plus précoce.")
        if self.overlap_start >= self.overlap_end:
            raise ValueError("Le chevauchement doit avoir une durée strictement positive.")

    def duration(self) -> timedelta:
        """Retourne la durée exacte du chevauchement."""

        return self.overlap_end - self.overlap_start

    def involves(self, assignment: MissionOccurrenceAssignment) -> bool:
        """Indique si l'affectation fournie participe au conflit, par UUID."""

        return isinstance(assignment, MissionOccurrenceAssignment) and assignment.id in {
            self.first_assignment.id,
            self.second_assignment.id,
        }

    def involves_employee(self, employee: Employee) -> bool:
        """Indique si le salarié fourni est concerné par le conflit, par UUID."""

        return isinstance(employee, Employee) and employee.id == self.first_assignment.employee.id
