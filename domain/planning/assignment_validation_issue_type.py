"""Types stricts de problèmes de validation d'une affectation planifiée."""

from __future__ import annotations

from enum import Enum


class AssignmentValidationIssueType(str, Enum):
    """Catégories métier stables produites par la validation globale."""

    QUALIFICATION = "qualification"
    PLANNING_CONFLICT = "planning_conflict"
    UNAVAILABILITY = "unavailability"
    WEEKLY_AVAILABILITY = "weekly_availability"
