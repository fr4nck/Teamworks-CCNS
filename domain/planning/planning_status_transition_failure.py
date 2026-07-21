"""Échec métier immutable d'une transition de statut de planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .planning import Planning
from .planning_status import PlanningStatus
from .planning_status_transition_failure_reason import PlanningStatusTransitionFailureReason


@dataclass(frozen=True, slots=True)
class PlanningStatusTransitionFailure:
    """Décrit explicitement le refus métier d'une transition de statut."""

    planning: Planning
    requested_status: PlanningStatus
    reason: PlanningStatusTransitionFailureReason
    message: str
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de l'échec de transition doit être un UUID.")
        if not isinstance(self.planning, Planning):
            raise ValueError("Le planning de l'échec de transition doit être un Planning.")
        if not isinstance(self.requested_status, PlanningStatus):
            raise ValueError("Le statut demandé doit être un PlanningStatus.")
        if not isinstance(self.reason, PlanningStatusTransitionFailureReason):
            raise ValueError("La raison de refus doit être une PlanningStatusTransitionFailureReason.")
        if not isinstance(self.message, str) or not (message := self.message.strip()):
            raise ValueError("Le message de refus de transition est obligatoire.")
        object.__setattr__(self, "message", message)

    def has_message(self) -> bool:
        return bool(self.message)

    def is_same_status(self) -> bool:
        return self.reason is PlanningStatusTransitionFailureReason.SAME_STATUS

    def is_transition_not_allowed(self) -> bool:
        return self.reason is PlanningStatusTransitionFailureReason.TRANSITION_NOT_ALLOWED

    def is_validation_required(self) -> bool:
        return self.reason is PlanningStatusTransitionFailureReason.VALIDATION_REQUIRED

    def is_validation_failed(self) -> bool:
        return self.reason is PlanningStatusTransitionFailureReason.VALIDATION_FAILED

    def is_validation_mismatch(self) -> bool:
        return self.reason is PlanningStatusTransitionFailureReason.VALIDATION_MISMATCH
