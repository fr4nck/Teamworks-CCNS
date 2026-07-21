"""Raisons métier de refus d'une transition de statut de planning."""

from enum import Enum


class PlanningStatusTransitionFailureReason(str, Enum):
    """Raison stricte et stable d'un refus de transition de statut."""

    SAME_STATUS = "same_status"
    TRANSITION_NOT_ALLOWED = "transition_not_allowed"
    VALIDATION_REQUIRED = "validation_required"
    VALIDATION_FAILED = "validation_failed"
    VALIDATION_MISMATCH = "validation_mismatch"
