"""Résultat métier immutable d'une transition de statut de planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .planning import Planning
from .planning_status import PlanningStatus
from .planning_status_transition_failure import PlanningStatusTransitionFailure


@dataclass(frozen=True, slots=True)
class PlanningStatusTransitionResult:
    """Porte le succès ou l'échec explicite d'une transition de statut."""

    original_planning: Planning
    requested_status: PlanningStatus
    successful: bool
    updated_planning: Optional[Planning] = None
    failure: Optional[PlanningStatusTransitionFailure] = None

    def __post_init__(self) -> None:
        if not isinstance(self.original_planning, Planning):
            raise ValueError("Le planning d'origine doit être un Planning.")
        if not isinstance(self.requested_status, PlanningStatus):
            raise ValueError("Le statut demandé doit être un PlanningStatus.")
        if not isinstance(self.successful, bool):
            raise ValueError("Le succès de transition doit être un booléen strict.")
        if self.successful:
            self._validate_success()
        else:
            self._validate_failure()

    def _validate_success(self) -> None:
        if not isinstance(self.updated_planning, Planning):
            raise ValueError("Le planning mis à jour est obligatoire en cas de succès.")
        if self.failure is not None:
            raise ValueError("Un succès de transition ne doit pas contenir d'échec.")
        if self.updated_planning.id != self.original_planning.id:
            raise ValueError("Le planning mis à jour doit conserver l'UUID du planning d'origine.")
        if self.updated_planning.status is not self.requested_status:
            raise ValueError("Le planning mis à jour doit porter le statut demandé.")
        if self.original_planning.status is self.requested_status:
            raise ValueError("Le statut d'origine doit différer du statut demandé en cas de succès.")

    def _validate_failure(self) -> None:
        if self.updated_planning is not None:
            raise ValueError("Un échec de transition ne doit pas contenir de planning mis à jour.")
        if not isinstance(self.failure, PlanningStatusTransitionFailure):
            raise ValueError("L'échec de transition est obligatoire en cas de refus.")
        if self.failure.planning.id != self.original_planning.id:
            raise ValueError("L'échec doit concerner le planning d'origine.")
        if self.failure.requested_status is not self.requested_status:
            raise ValueError("L'échec doit correspondre au statut demandé.")

    def is_successful(self) -> bool:
        return self.successful

    def has_updated_planning(self) -> bool:
        return self.updated_planning is not None

    def has_failure(self) -> bool:
        return self.failure is not None
