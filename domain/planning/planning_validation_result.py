"""Résultat immutable de validation globale d'un planning."""

from __future__ import annotations

from dataclasses import dataclass

from domain.missions import MissionOccurrenceAssignment

from .assignment_validation_result import AssignmentValidationResult


@dataclass(frozen=True, slots=True)
class PlanningValidationResult:
    """Agrège les résultats individuels d'un ensemble d'affectations."""

    assignment_results: tuple[AssignmentValidationResult, ...]
    valid: bool

    def __post_init__(self) -> None:
        if not isinstance(self.assignment_results, tuple):
            raise ValueError("Les résultats de validation du planning doivent être un tuple.")
        if not self.assignment_results:
            raise ValueError("La validation d'un planning doit contenir au moins un résultat.")
        if any(
            not isinstance(result, AssignmentValidationResult)
            for result in self.assignment_results
        ):
            raise ValueError(
                "Les résultats du planning doivent contenir uniquement des AssignmentValidationResult."
            )
        if not isinstance(self.valid, bool):
            raise ValueError("La validité globale du planning doit être un booléen.")
        if _has_duplicate_assignment(self.assignment_results):
            raise ValueError("Une affectation ne peut apparaître qu'une seule fois dans un planning.")

        all_results_valid = all(result.is_valid() for result in self.assignment_results)
        if self.valid is not all_results_valid:
            raise ValueError(
                "La validité globale du planning doit être cohérente avec les résultats d'affectation."
            )

    def is_valid(self) -> bool:
        """Retourne la validité globale stricte du planning."""

        return self.valid

    def has_invalid_assignments(self) -> bool:
        """Indique si au moins une affectation du planning est invalide."""

        return not self.valid

    def assignment_count(self) -> int:
        """Retourne le nombre total d'affectations contrôlées."""

        return len(self.assignment_results)

    def valid_assignment_count(self) -> int:
        """Retourne le nombre d'affectations valides."""

        return len(self.valid_results())

    def invalid_assignment_count(self) -> int:
        """Retourne le nombre d'affectations invalides."""

        return len(self.invalid_results())

    def valid_results(self) -> tuple[AssignmentValidationResult, ...]:
        """Retourne les résultats valides dans l'ordre initial."""

        return tuple(result for result in self.assignment_results if result.is_valid())

    def invalid_results(self) -> tuple[AssignmentValidationResult, ...]:
        """Retourne les résultats invalides dans l'ordre initial."""

        return tuple(result for result in self.assignment_results if not result.is_valid())

    def result_for(
        self, assignment: MissionOccurrenceAssignment
    ) -> AssignmentValidationResult:
        """Retrouve le résultat associé à l'identité métier d'une affectation."""

        if not isinstance(assignment, MissionOccurrenceAssignment):
            raise ValueError("L'affectation recherchée doit être une MissionOccurrenceAssignment.")
        for result in self.assignment_results:
            if result.assignment.id == assignment.id:
                return result
        raise ValueError("L'affectation demandée n'est pas présente dans le planning validé.")


def _has_duplicate_assignment(
    results: tuple[AssignmentValidationResult, ...]
) -> bool:
    seen: set[object] = set()
    for result in results:
        assignment_id = result.assignment.id
        if assignment_id in seen:
            return True
        seen.add(assignment_id)
    return False
