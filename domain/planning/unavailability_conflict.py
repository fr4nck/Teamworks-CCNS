"""Conflit temporel direct entre une affectation et une indisponibilité."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from domain.missions import MissionOccurrenceAssignment
from domain.people import Employee

from .employee_unavailability import EmployeeUnavailability


@dataclass(frozen=True, slots=True)
class UnavailabilityConflict:
    """Décrit le chevauchement horaire d'une affectation avec une indisponibilité."""

    assignment: MissionOccurrenceAssignment
    unavailability: EmployeeUnavailability
    overlap_start: datetime
    overlap_end: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.assignment, MissionOccurrenceAssignment):
            raise ValueError("L'affectation doit être une MissionOccurrenceAssignment.")
        if not isinstance(self.unavailability, EmployeeUnavailability):
            raise ValueError("L'indisponibilité doit être une EmployeeUnavailability.")
        if self.assignment.employee.id != self.unavailability.employee.id:
            raise ValueError(
                "Un conflit d'indisponibilité doit concerner un seul et même salarié."
            )
        if not isinstance(self.overlap_start, datetime):
            raise ValueError("Le début du chevauchement doit être un datetime.")
        if not isinstance(self.overlap_end, datetime):
            raise ValueError("La fin du chevauchement doit être un datetime.")

        expected_start = max(
            self.assignment.occurrence.starts_at, self.unavailability.starts_at
        )
        expected_end = min(
            self.assignment.occurrence.ends_at, self.unavailability.ends_at
        )
        if self.overlap_start != expected_start:
            raise ValueError(
                "Le début du chevauchement doit correspondre au début le plus tardif."
            )
        if self.overlap_end != expected_end:
            raise ValueError(
                "La fin du chevauchement doit correspondre à la fin la plus précoce."
            )
        if self.overlap_start >= self.overlap_end:
            raise ValueError(
                "Le chevauchement doit avoir une durée strictement positive."
            )

    def duration(self) -> timedelta:
        """Retourne la durée exacte du chevauchement."""

        return self.overlap_end - self.overlap_start

    def involves_assignment(self, assignment: MissionOccurrenceAssignment) -> bool:
        """Indique si l'affectation fournie participe au conflit, par UUID."""

        return (
            isinstance(assignment, MissionOccurrenceAssignment)
            and assignment.id == self.assignment.id
        )

    def involves_unavailability(self, unavailability: EmployeeUnavailability) -> bool:
        """Indique si l'indisponibilité fournie participe au conflit, par UUID."""

        return (
            isinstance(unavailability, EmployeeUnavailability)
            and unavailability.id == self.unavailability.id
        )

    def involves_employee(self, employee: Employee) -> bool:
        """Indique si le salarié fourni est concerné par le conflit, par UUID."""

        return (
            isinstance(employee, Employee)
            and employee.id == self.assignment.employee.id
        )
