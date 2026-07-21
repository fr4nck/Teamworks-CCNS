"""Conflit de couverture par disponibilité hebdomadaire."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from domain.missions import MissionOccurrence, MissionOccurrenceAssignment
from domain.people import Employee


@dataclass(frozen=True, slots=True)
class WeeklyAvailabilityConflict:
    """Décrit une affectation non couverte par les disponibilités hebdomadaires."""

    assignment: MissionOccurrenceAssignment
    employee: Employee
    occurrence: MissionOccurrence
    reason: str
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant du conflit de disponibilité hebdomadaire doit être un UUID.")
        if not isinstance(self.assignment, MissionOccurrenceAssignment):
            raise ValueError("L'affectation doit être une MissionOccurrenceAssignment.")
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié doit être un Employee.")
        if not isinstance(self.occurrence, MissionOccurrence):
            raise ValueError("L'occurrence doit être une MissionOccurrence.")
        if self.assignment.employee.id != self.employee.id:
            raise ValueError("Le conflit doit concerner le salarié de l'affectation.")
        if self.assignment.occurrence.id != self.occurrence.id:
            raise ValueError("Le conflit doit concerner l'occurrence de l'affectation.")
        if not isinstance(self.reason, str) or not (reason := self.reason.strip()):
            raise ValueError("La raison du conflit de disponibilité hebdomadaire est obligatoire.")
        object.__setattr__(self, "reason", reason)

    def has_reason(self) -> bool:
        """Indique si une raison exploitable est renseignée."""

        return bool(self.reason)
