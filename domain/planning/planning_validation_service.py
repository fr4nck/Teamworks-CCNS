"""Service métier pur de validation globale d'un planning."""

from __future__ import annotations

from collections.abc import Iterable

from domain.missions import MissionOccurrenceAssignment
from domain.qualifications import EmployeeQualification, QualificationRequirement

from .assignment_validation_result import AssignmentValidationResult
from .assignment_validation_service import AssignmentValidationService
from .employee_unavailability import EmployeeUnavailability
from .employee_weekly_availability import EmployeeWeeklyAvailability
from .planning_validation_result import PlanningValidationResult


class PlanningValidationService:
    """Valide un planning complet en orchestrant la validation individuelle."""

    def __init__(self, assignment_validation_service: AssignmentValidationService) -> None:
        if not isinstance(assignment_validation_service, AssignmentValidationService):
            raise ValueError("Le service de validation d'affectation injecté est invalide.")
        self._assignment_validation_service = assignment_validation_service

    def validate(
        self,
        assignments: Iterable[MissionOccurrenceAssignment],
        qualification_requirements: Iterable[QualificationRequirement],
        employee_qualifications: Iterable[EmployeeQualification],
        unavailabilities: Iterable[EmployeeUnavailability],
        weekly_availabilities: Iterable[EmployeeWeeklyAvailability],
    ) -> PlanningValidationResult:
        """Retourne le résultat global sans interrompre la validation au premier échec."""

        assignments_tuple = _validated_iterable(
            assignments,
            MissionOccurrenceAssignment,
            "affectations du planning",
            allow_empty=False,
        )
        _reject_duplicate_assignments(assignments_tuple)
        requirements_tuple = _validated_iterable(
            qualification_requirements,
            QualificationRequirement,
            "exigences de qualification",
        )
        employee_qualifications_tuple = _validated_iterable(
            employee_qualifications,
            EmployeeQualification,
            "qualifications du salarié",
        )
        unavailabilities_tuple = _validated_iterable(
            unavailabilities,
            EmployeeUnavailability,
            "indisponibilités",
        )
        weekly_availabilities_tuple = _validated_iterable(
            weekly_availabilities,
            EmployeeWeeklyAvailability,
            "disponibilités hebdomadaires",
        )

        results: list[AssignmentValidationResult] = []
        for assignment in assignments_tuple:
            existing_assignments = tuple(
                existing
                for existing in assignments_tuple
                if existing.id != assignment.id
            )
            results.append(
                self._assignment_validation_service.validate(
                    assignment,
                    requirements_tuple,
                    employee_qualifications_tuple,
                    existing_assignments,
                    unavailabilities_tuple,
                    weekly_availabilities_tuple,
                )
            )

        assignment_results = tuple(results)
        return PlanningValidationResult(
            assignment_results=assignment_results,
            valid=all(result.is_valid() for result in assignment_results),
        )


def _validated_iterable(
    value: Iterable[object],
    expected_type: type,
    label: str,
    *,
    allow_empty: bool = True,
) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(f"Les {label} doivent être un iterable métier.")
    items = tuple(value)
    if not allow_empty and not items:
        raise ValueError(f"Les {label} ne peuvent pas être vides.")
    if any(not isinstance(item, expected_type) for item in items):
        raise ValueError(f"Les {label} doivent contenir uniquement des {expected_type.__name__}.")
    return items


def _reject_duplicate_assignments(assignments: tuple[MissionOccurrenceAssignment, ...]) -> None:
    seen: set[object] = set()
    for assignment in assignments:
        if assignment.id in seen:
            raise ValueError(
                "Un planning ne peut pas contenir deux affectations avec le même identifiant métier."
            )
        seen.add(assignment.id)
