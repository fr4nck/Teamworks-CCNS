"""Problème métier immutable de validation d'une affectation planifiée."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from domain.qualifications import QualificationEligibilityResult

from .assignment_validation_issue_type import AssignmentValidationIssueType
from .planning_conflict import PlanningConflict
from .unavailability_conflict import UnavailabilityConflict
from .weekly_availability_conflict import WeeklyAvailabilityConflict

_DETAIL_TYPES = {
    AssignmentValidationIssueType.QUALIFICATION: QualificationEligibilityResult,
    AssignmentValidationIssueType.PLANNING_CONFLICT: PlanningConflict,
    AssignmentValidationIssueType.UNAVAILABILITY: UnavailabilityConflict,
    AssignmentValidationIssueType.WEEKLY_AVAILABILITY: WeeklyAvailabilityConflict,
}


@dataclass(frozen=True, slots=True)
class AssignmentValidationIssue:
    """Décrit un problème détecté sans transformer l'objet métier d'origine."""

    issue_type: AssignmentValidationIssueType
    detail: object
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant du problème de validation doit être un UUID.")
        if not isinstance(self.issue_type, AssignmentValidationIssueType):
            raise ValueError("Le type de problème de validation est invalide.")
        if self.detail is None:
            raise ValueError("Le détail du problème de validation est obligatoire.")
        expected_type = _DETAIL_TYPES[self.issue_type]
        if not isinstance(self.detail, expected_type):
            raise ValueError(
                "Le détail du problème de validation ne correspond pas au type déclaré."
            )

    def is_qualification_issue(self) -> bool:
        """Indique si le problème concerne l'éligibilité par qualification."""

        return self.issue_type is AssignmentValidationIssueType.QUALIFICATION

    def is_planning_conflict(self) -> bool:
        """Indique si le problème concerne un conflit de planning."""

        return self.issue_type is AssignmentValidationIssueType.PLANNING_CONFLICT

    def is_unavailability_issue(self) -> bool:
        """Indique si le problème concerne une indisponibilité."""

        return self.issue_type is AssignmentValidationIssueType.UNAVAILABILITY

    def is_weekly_availability_issue(self) -> bool:
        """Indique si le problème concerne la disponibilité hebdomadaire."""

        return self.issue_type is AssignmentValidationIssueType.WEEKLY_AVAILABILITY
