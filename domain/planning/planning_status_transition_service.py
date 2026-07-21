"""Service métier pur de transition de statut d'un planning."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from .planning import Planning
from .planning_status import PlanningStatus
from .planning_status_transition_failure import PlanningStatusTransitionFailure
from .planning_status_transition_failure_reason import PlanningStatusTransitionFailureReason
from .planning_status_transition_result import PlanningStatusTransitionResult
from .planning_validation_result import PlanningValidationResult


_MESSAGES = {
    PlanningStatusTransitionFailureReason.SAME_STATUS: "Le planning possède déjà le statut demandé.",
    PlanningStatusTransitionFailureReason.TRANSITION_NOT_ALLOWED: "La transition de statut demandée n’est pas autorisée.",
    PlanningStatusTransitionFailureReason.VALIDATION_REQUIRED: "Un résultat de validation du planning est requis pour cette transition.",
    PlanningStatusTransitionFailureReason.VALIDATION_FAILED: "Le planning ne peut pas être validé car son résultat de validation contient des anomalies.",
    PlanningStatusTransitionFailureReason.VALIDATION_MISMATCH: "Le résultat de validation ne correspond pas exactement aux affectations du planning.",
}

_ALLOWED_TRANSITIONS = {
    (PlanningStatus.DRAFT, PlanningStatus.VALIDATED),
    (PlanningStatus.VALIDATED, PlanningStatus.DRAFT),
    (PlanningStatus.VALIDATED, PlanningStatus.PUBLISHED),
    (PlanningStatus.PUBLISHED, PlanningStatus.ARCHIVED),
    (PlanningStatus.ARCHIVED, PlanningStatus.DRAFT),
}


class PlanningStatusTransitionService:
    """Encadre les changements de statut sans état, persistance ni recalcul."""

    def transition(
        self,
        planning: Planning,
        requested_status: PlanningStatus,
        validation_result: Optional[PlanningValidationResult] = None,
    ) -> PlanningStatusTransitionResult:
        if not isinstance(planning, Planning):
            raise ValueError("Le planning à transitionner doit être un Planning.")
        if not isinstance(requested_status, PlanningStatus):
            raise ValueError("Le statut demandé doit être un PlanningStatus.")
        if validation_result is not None and not isinstance(validation_result, PlanningValidationResult):
            raise ValueError("Le résultat de validation doit être un PlanningValidationResult ou None.")

        if planning.status is requested_status:
            return self._failure(planning, requested_status, PlanningStatusTransitionFailureReason.SAME_STATUS)
        if (planning.status, requested_status) not in _ALLOWED_TRANSITIONS:
            return self._failure(planning, requested_status, PlanningStatusTransitionFailureReason.TRANSITION_NOT_ALLOWED)
        if planning.status is PlanningStatus.DRAFT and requested_status is PlanningStatus.VALIDATED:
            validation_failure = self._validation_failure_reason(planning, validation_result)
            if validation_failure is not None:
                return self._failure(planning, requested_status, validation_failure)

        updated = planning.with_status(requested_status)
        return PlanningStatusTransitionResult(planning, requested_status, True, updated_planning=updated)

    def _validation_failure_reason(
        self, planning: Planning, validation_result: Optional[PlanningValidationResult]
    ) -> Optional[PlanningStatusTransitionFailureReason]:
        if validation_result is None:
            return PlanningStatusTransitionFailureReason.VALIDATION_REQUIRED
        if not validation_result.is_valid():
            return PlanningStatusTransitionFailureReason.VALIDATION_FAILED
        planning_ids = tuple(assignment.id for assignment in planning.assignments)
        result_ids = tuple(result.assignment.id for result in validation_result.assignment_results)
        if self._has_duplicate_uuid(planning_ids) or self._has_duplicate_uuid(result_ids):
            return PlanningStatusTransitionFailureReason.VALIDATION_MISMATCH
        if set(planning_ids) != set(result_ids):
            return PlanningStatusTransitionFailureReason.VALIDATION_MISMATCH
        return None

    def _has_duplicate_uuid(self, values: tuple[UUID, ...]) -> bool:
        return len(set(values)) != len(values)

    def _failure(
        self,
        planning: Planning,
        requested_status: PlanningStatus,
        reason: PlanningStatusTransitionFailureReason,
    ) -> PlanningStatusTransitionResult:
        failure = PlanningStatusTransitionFailure(
            planning=planning,
            requested_status=requested_status,
            reason=reason,
            message=_MESSAGES[reason],
        )
        return PlanningStatusTransitionResult(planning, requested_status, False, failure=failure)
