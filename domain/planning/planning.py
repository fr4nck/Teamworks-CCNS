"""Agrégat métier immutable représentant un planning borné."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.missions import MissionOccurrence, MissionOccurrenceAssignment
from domain.people import Employee
from domain.planning.planning_status import PlanningStatus


@dataclass(frozen=True, slots=True)
class Planning:
    """Planning métier identifié, nommé, borné et porteur d'affectations."""

    code: str
    name: str
    starts_on: date
    ends_on: date
    assignments: tuple[MissionOccurrenceAssignment, ...] = ()
    status: PlanningStatus = PlanningStatus.DRAFT
    observations: Optional[str] = None
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant du planning doit être un UUID.")
        if not isinstance(self.status, PlanningStatus):
            raise ValueError("Le statut du planning doit être un PlanningStatus.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif du planning doit être un booléen.")

        starts_on = _validated_date(self.starts_on, "début")
        ends_on = _validated_date(self.ends_on, "fin")
        if ends_on < starts_on:
            raise ValueError("La date de fin du planning doit être supérieure ou égale à sa date de début.")

        object.__setattr__(self, "code", _normalized_code(self.code))
        object.__setattr__(self, "name", _required_text(self.name, "nom"))
        object.__setattr__(self, "starts_on", starts_on)
        object.__setattr__(self, "ends_on", ends_on)
        object.__setattr__(self, "observations", _normalized_observations(self.observations))
        _validate_assignments(self.assignments, starts_on, ends_on)

    def is_active(self) -> bool:
        return self.active

    def is_draft(self) -> bool:
        return self.status is PlanningStatus.DRAFT

    def is_validated(self) -> bool:
        return self.status is PlanningStatus.VALIDATED

    def is_published(self) -> bool:
        return self.status is PlanningStatus.PUBLISHED

    def is_archived(self) -> bool:
        return self.status is PlanningStatus.ARCHIVED

    def has_observations(self) -> bool:
        return self.observations is not None

    def has_assignments(self) -> bool:
        return bool(self.assignments)

    def assignment_count(self) -> int:
        return len(self.assignments)

    def contains_day(self, day: date) -> bool:
        day = _validated_date(day, "jour")
        return self.starts_on <= day <= self.ends_on

    def contains_assignment(self, assignment: MissionOccurrenceAssignment) -> bool:
        _validate_assignment_type(assignment)
        return any(current.id == assignment.id for current in self.assignments)

    def assignment_by_id(self, assignment_id: UUID) -> MissionOccurrenceAssignment:
        if not isinstance(assignment_id, UUID):
            raise ValueError("L'identifiant d'affectation recherché doit être un UUID.")
        for assignment in self.assignments:
            if assignment.id == assignment_id:
                return assignment
        raise ValueError("Aucune affectation du planning ne porte cet identifiant.")

    def assignments_for_employee(self, employee: Employee) -> tuple[MissionOccurrenceAssignment, ...]:
        if not isinstance(employee, Employee):
            raise ValueError("Le salarié recherché doit être un Employee.")
        return tuple(assignment for assignment in self.assignments if assignment.employee.id == employee.id)

    def assignments_for_occurrence(self, occurrence: MissionOccurrence) -> tuple[MissionOccurrenceAssignment, ...]:
        if not isinstance(occurrence, MissionOccurrence):
            raise ValueError("L'occurrence recherchée doit être une MissionOccurrence.")
        return tuple(assignment for assignment in self.assignments if assignment.occurrence.id == occurrence.id)

    def with_assignment(self, assignment: MissionOccurrenceAssignment) -> Planning:
        _validate_assignment_type(assignment)
        _validate_assignment_in_period(assignment, self.starts_on, self.ends_on)
        if self.contains_assignment(assignment):
            raise ValueError("Une affectation portant le même identifiant existe déjà dans le planning.")
        return replace(self, assignments=self.assignments + (assignment,))

    def without_assignment(self, assignment: MissionOccurrenceAssignment) -> Planning:
        _validate_assignment_type(assignment)
        if not self.contains_assignment(assignment):
            raise ValueError("L'affectation à retirer n'est pas présente dans le planning.")
        return replace(
            self,
            assignments=tuple(current for current in self.assignments if current.id != assignment.id),
        )

    def replace_assignment(self, assignment: MissionOccurrenceAssignment) -> Planning:
        _validate_assignment_type(assignment)
        _validate_assignment_in_period(assignment, self.starts_on, self.ends_on)
        for index, current in enumerate(self.assignments):
            if current.id == assignment.id:
                updated = self.assignments[:index] + (assignment,) + self.assignments[index + 1 :]
                return replace(self, assignments=updated)
        raise ValueError("L'affectation à remplacer n'est pas présente dans le planning.")

    def with_status(self, status: PlanningStatus) -> Planning:
        if not isinstance(status, PlanningStatus):
            raise ValueError("Le statut du planning doit être un PlanningStatus.")
        return replace(self, status=status)


def _validated_date(value: date, field_name: str) -> date:
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValueError(f"La date de {field_name} du planning doit être une date stricte.")
    return value


def _normalized_code(value: str) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError("Le code du planning est obligatoire.")
    return normalized.upper()


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(f"Le {field_name} du planning est obligatoire.")
    return normalized


def _normalized_observations(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError("Les observations du planning sont invalides.")
    return normalized


def _validate_assignments(
    assignments: tuple[MissionOccurrenceAssignment, ...], starts_on: date, ends_on: date
) -> None:
    if not isinstance(assignments, tuple):
        raise ValueError("Les affectations du planning doivent être un tuple.")
    seen: set[UUID] = set()
    for assignment in assignments:
        _validate_assignment_type(assignment)
        _validate_assignment_in_period(assignment, starts_on, ends_on)
        if assignment.id in seen:
            raise ValueError("Un planning ne peut pas contenir deux affectations du même identifiant.")
        seen.add(assignment.id)


def _validate_assignment_type(assignment: MissionOccurrenceAssignment) -> None:
    if not isinstance(assignment, MissionOccurrenceAssignment):
        raise ValueError("Les affectations du planning doivent être des MissionOccurrenceAssignment.")


def _validate_assignment_in_period(
    assignment: MissionOccurrenceAssignment, starts_on: date, ends_on: date
) -> None:
    if assignment.occurrence.starts_at.date() < starts_on or assignment.occurrence.ends_at.date() > ends_on:
        raise ValueError("L'occurrence de l'affectation doit être entièrement comprise dans la période du planning.")
