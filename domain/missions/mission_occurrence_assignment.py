"""Affectation immutable d'un salarié à une occurrence de mission."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4

from domain.missions.mission_occurrence import MissionOccurrence
from domain.missions.mission_occurrence_assignment_status import (
    MissionOccurrenceAssignmentStatus,
)
from domain.people import Employee


@dataclass(frozen=True, slots=True)
class MissionOccurrenceAssignment:
    """Représente l'affectation déclarée d'un ``Employee`` à une occurrence.

    Cette relation porte uniquement le lien concret entre un salarié et une
    ``MissionOccurrence``. Elle ne recopie pas la mission, les dates, le lieu,
    les exigences de qualification ou les données contractuelles, et ne calcule
    aucun statut à partir du calendrier.
    """

    employee: Employee
    occurrence: MissionOccurrence
    status: MissionOccurrenceAssignmentStatus
    observations: Optional[str] = None
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError(
                "L'identifiant de l'affectation à une occurrence de mission doit être un UUID."
            )
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié est obligatoire et doit être un Employee.")
        if not isinstance(self.occurrence, MissionOccurrence):
            raise ValueError(
                "L'occurrence est obligatoire et doit être une MissionOccurrence."
            )
        if not isinstance(self.status, MissionOccurrenceAssignmentStatus):
            raise ValueError(
                "Le statut de l'affectation à une occurrence de mission doit être un "
                "MissionOccurrenceAssignmentStatus."
            )
        if not isinstance(self.active, bool):
            raise ValueError(
                "Le statut actif de l'affectation à une occurrence de mission doit être un booléen."
            )

        object.__setattr__(self, "observations", _normalized_observations(self.observations))

    def is_planned(self) -> bool:
        """Indique si le statut déclaré est ``PLANNED``."""

        return self.status is MissionOccurrenceAssignmentStatus.PLANNED

    def is_confirmed(self) -> bool:
        """Indique si le statut déclaré est ``CONFIRMED``."""

        return self.status is MissionOccurrenceAssignmentStatus.CONFIRMED

    def is_cancelled(self) -> bool:
        """Indique si le statut déclaré est ``CANCELLED``."""

        return self.status is MissionOccurrenceAssignmentStatus.CANCELLED

    def is_completed(self) -> bool:
        """Indique si le statut déclaré est ``COMPLETED``."""

        return self.status is MissionOccurrenceAssignmentStatus.COMPLETED

    def is_absent(self) -> bool:
        """Indique si le statut déclaré est ``ABSENT``."""

        return self.status is MissionOccurrenceAssignmentStatus.ABSENT

    def is_active(self) -> bool:
        """Retourne strictement le statut actif déclaré, sans calcul calendaire."""

        return self.active


def _normalized_observations(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(
            "Les observations de l'affectation à une occurrence de mission sont invalides."
        )
    return normalized
