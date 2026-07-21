"""Résultat global immutable de validation d'une affectation planifiée."""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.missions import MissionOccurrenceAssignment

from .assignment_validation_issue import AssignmentValidationIssue
from .assignment_validation_issue_type import AssignmentValidationIssueType


@dataclass(frozen=True, slots=True)
class AssignmentValidationResult:
    """Agrège tous les problèmes détectés par les services spécialisés."""

    assignment: MissionOccurrenceAssignment
    valid: bool
    issues: tuple[AssignmentValidationIssue, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.assignment, MissionOccurrenceAssignment):
            raise ValueError("L'affectation validée doit être une MissionOccurrenceAssignment.")
        if not isinstance(self.valid, bool):
            raise ValueError("La validité globale doit être un booléen.")
        if not isinstance(self.issues, tuple):
            raise ValueError("Les problèmes de validation doivent être un tuple.")
        if any(not isinstance(issue, AssignmentValidationIssue) for issue in self.issues):
            raise ValueError(
                "Les problèmes de validation doivent contenir uniquement des AssignmentValidationIssue."
            )
        if self.valid and self.issues:
            raise ValueError("Un résultat valide ne peut pas contenir de problème.")
        if not self.valid and not self.issues:
            raise ValueError("Un résultat invalide doit contenir au moins un problème.")
        if _has_exact_business_duplicate(self.issues):
            raise ValueError("Un résultat de validation ne peut pas contenir deux problèmes identiques.")

    def is_valid(self) -> bool:
        """Retourne la validité globale stricte."""

        return self.valid

    def has_issues(self) -> bool:
        """Indique si le résultat contient au moins un problème."""

        return bool(self.issues)

    def issue_count(self) -> int:
        """Retourne le nombre de problèmes conservés."""

        return len(self.issues)

    def has_issue_type(self, issue_type: AssignmentValidationIssueType) -> bool:
        """Indique si une catégorie de problème est présente."""

        _validate_issue_type(issue_type)
        return any(issue.issue_type is issue_type for issue in self.issues)

    def issues_of_type(
        self, issue_type: AssignmentValidationIssueType
    ) -> tuple[AssignmentValidationIssue, ...]:
        """Retourne les problèmes de la catégorie demandée dans leur ordre initial."""

        _validate_issue_type(issue_type)
        return tuple(issue for issue in self.issues if issue.issue_type is issue_type)


def _validate_issue_type(issue_type: AssignmentValidationIssueType) -> None:
    if not isinstance(issue_type, AssignmentValidationIssueType):
        raise ValueError("Le type de problème de validation est invalide.")


def _has_exact_business_duplicate(issues: tuple[AssignmentValidationIssue, ...]) -> bool:
    seen: list[AssignmentValidationIssue] = []
    for issue in issues:
        if any(
            issue.issue_type is previous.issue_type and issue.detail == previous.detail
            for previous in seen
        ):
            return True
        seen.append(issue)
    return False
