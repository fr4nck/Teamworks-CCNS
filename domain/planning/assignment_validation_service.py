"""Service métier pur de validation globale d'une affectation planifiée."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from domain.missions import MissionOccurrenceAssignment
from domain.qualifications import (
    EmployeeQualification,
    QualificationEligibilityService,
    QualificationRequirement,
)

from .assignment_validation_issue import AssignmentValidationIssue
from .assignment_validation_issue_type import AssignmentValidationIssueType
from .assignment_validation_result import AssignmentValidationResult
from .employee_unavailability import EmployeeUnavailability
from .employee_weekly_availability import EmployeeWeeklyAvailability
from .planning_conflict_service import PlanningConflictService
from .unavailability_conflict_service import UnavailabilityConflictService
from .weekly_availability_service import WeeklyAvailabilityService


class AssignmentValidationService:
    """Orchestre les contrôles spécialisés sans porter leurs règles métier."""

    def __init__(
        self,
        qualification_service: QualificationEligibilityService,
        planning_conflict_service: PlanningConflictService,
        unavailability_conflict_service: UnavailabilityConflictService,
        weekly_availability_service: WeeklyAvailabilityService,
    ) -> None:
        if not isinstance(qualification_service, QualificationEligibilityService):
            raise ValueError("Le service de qualification injecté est invalide.")
        if not isinstance(planning_conflict_service, PlanningConflictService):
            raise ValueError("Le service de conflits de planning injecté est invalide.")
        if not isinstance(unavailability_conflict_service, UnavailabilityConflictService):
            raise ValueError("Le service de conflits d'indisponibilité injecté est invalide.")
        if not isinstance(weekly_availability_service, WeeklyAvailabilityService):
            raise ValueError("Le service de disponibilité hebdomadaire injecté est invalide.")
        self._qualification_service = qualification_service
        self._planning_conflict_service = planning_conflict_service
        self._unavailability_conflict_service = unavailability_conflict_service
        self._weekly_availability_service = weekly_availability_service

    def validate(
        self,
        assignment: MissionOccurrenceAssignment,
        qualification_requirements: Iterable[QualificationRequirement],
        employee_qualifications: Iterable[EmployeeQualification],
        existing_assignments: Iterable[MissionOccurrenceAssignment],
        unavailabilities: Iterable[EmployeeUnavailability],
        weekly_availabilities: Iterable[EmployeeWeeklyAvailability],
    ) -> AssignmentValidationResult:
        """Retourne tous les problèmes détectés, dans l'ordre métier stable."""

        if not isinstance(assignment, MissionOccurrenceAssignment):
            raise ValueError("L'affectation à valider doit être une MissionOccurrenceAssignment.")

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
        existing_assignments_tuple = _validated_iterable(
            existing_assignments,
            MissionOccurrenceAssignment,
            "affectations existantes",
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

        issues: list[AssignmentValidationIssue] = []

        mission = replace(
            assignment.occurrence.mission,
            qualification_requirements=requirements_tuple,
        )
        qualification_result = self._qualification_service.evaluate(
            assignment.employee,
            mission,
            employee_qualifications_tuple,
        )
        if not qualification_result.is_eligible():
            issues.append(
                AssignmentValidationIssue(
                    issue_type=AssignmentValidationIssueType.QUALIFICATION,
                    detail=qualification_result,
                )
            )

        assignments_to_evaluate = (assignment, *existing_assignments_tuple)
        planning_result = self._planning_conflict_service.evaluate(
            assignment.employee,
            assignments_to_evaluate,
        )
        issues.extend(
            AssignmentValidationIssue(
                issue_type=AssignmentValidationIssueType.PLANNING_CONFLICT,
                detail=conflict,
            )
            for conflict in planning_result.conflicts
            if assignment.id in {conflict.first_assignment.id, conflict.second_assignment.id}
        )

        unavailability_result = self._unavailability_conflict_service.evaluate(
            assignment.employee,
            (assignment,),
            unavailabilities_tuple,
        )
        issues.extend(
            AssignmentValidationIssue(
                issue_type=AssignmentValidationIssueType.UNAVAILABILITY,
                detail=conflict,
            )
            for conflict in unavailability_result.conflicts
        )

        weekly_result = self._weekly_availability_service.check(
            assignment,
            weekly_availabilities_tuple,
        )
        if not weekly_result.is_covered():
            issues.append(
                AssignmentValidationIssue(
                    issue_type=AssignmentValidationIssueType.WEEKLY_AVAILABILITY,
                    detail=weekly_result.conflict,
                )
            )

        unique_issues = _deduplicated_issues(tuple(issues))
        return AssignmentValidationResult(
            assignment=assignment,
            valid=not unique_issues,
            issues=unique_issues,
        )


def _validated_iterable(value: Iterable[object], expected_type: type, label: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(f"Les {label} doivent être un iterable.")
    items = tuple(value)
    if any(not isinstance(item, expected_type) for item in items):
        raise ValueError(f"Les {label} doivent contenir uniquement des {expected_type.__name__}.")
    return items


def _deduplicated_issues(
    issues: tuple[AssignmentValidationIssue, ...]
) -> tuple[AssignmentValidationIssue, ...]:
    unique: list[AssignmentValidationIssue] = []
    for issue in issues:
        if any(
            issue.issue_type is previous.issue_type and issue.detail == previous.detail
            for previous in unique
        ):
            continue
        unique.append(issue)
    return tuple(unique)
