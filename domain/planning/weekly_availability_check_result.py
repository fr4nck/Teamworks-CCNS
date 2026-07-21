"""Résultat du contrôle de couverture par disponibilité hebdomadaire."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.missions import MissionOccurrenceAssignment

from .weekly_availability_conflict import WeeklyAvailabilityConflict


@dataclass(frozen=True, slots=True)
class WeeklyAvailabilityCheckResult:
    """Résultat immutable et cohérent d'un contrôle de disponibilité hebdomadaire."""

    assignment: MissionOccurrenceAssignment
    covered: bool
    conflict: Optional[WeeklyAvailabilityConflict] = None

    def __post_init__(self) -> None:
        if not isinstance(self.assignment, MissionOccurrenceAssignment):
            raise ValueError("L'affectation contrôlée doit être une MissionOccurrenceAssignment.")
        if not isinstance(self.covered, bool):
            raise ValueError("Le statut de couverture doit être un booléen.")
        if self.covered and self.conflict is not None:
            raise ValueError("Un résultat couvert ne doit pas contenir de conflit.")
        if not self.covered:
            if not isinstance(self.conflict, WeeklyAvailabilityConflict):
                raise ValueError("Un résultat non couvert doit contenir un conflit de disponibilité hebdomadaire.")
            if self.conflict.assignment.id != self.assignment.id:
                raise ValueError("Le conflit doit concerner exactement la même affectation.")

    def is_covered(self) -> bool:
        """Retourne strictement le statut de couverture."""

        return self.covered

    def has_conflict(self) -> bool:
        """Indique si un conflit accompagne le résultat."""

        return self.conflict is not None
