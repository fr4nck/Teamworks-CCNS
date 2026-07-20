"""Service métier pur d'éligibilité aux qualifications d'une mission."""

from __future__ import annotations

from collections.abc import Collection

from typing import TYPE_CHECKING

from domain.people import Employee

if TYPE_CHECKING:
    from domain.missions import Mission

from .employee_qualification import EmployeeQualification
from .qualification_eligibility_result import QualificationEligibilityResult
from .qualification_status import QualificationStatus
from .requirement_level import RequirementLevel


class QualificationEligibilityService:
    """Compare déclarativement les exigences REQUIRED d'une mission.

    La comparaison est volontairement stricte : seule l'identité UUID de la
    Qualification exigée est rapprochée des qualifications VALID et actives du
    salarié fourni. Le service ne consulte aucune date système et ne traite ni
    équivalence, ni passerelle, ni règle réglementaire implicite.
    """

    def evaluate(
        self,
        employee: Employee,
        mission: "Mission",
        employee_qualifications: Collection[EmployeeQualification],
    ) -> QualificationEligibilityResult:
        """Évalue les exigences REQUIRED actives satisfaites et manquantes."""

        from domain.missions import Mission

        if not isinstance(employee, Employee):
            raise ValueError("Le salarié à évaluer doit être un Employee.")
        if not isinstance(mission, Mission):
            raise ValueError("La mission à évaluer doit être une Mission.")
        if isinstance(employee_qualifications, (str, bytes)) or not isinstance(
            employee_qualifications,
            Collection,
        ):
            raise ValueError("Les qualifications du salarié doivent être une collection.")

        qualifications = tuple(employee_qualifications)
        if any(
            not isinstance(employee_qualification, EmployeeQualification)
            for employee_qualification in qualifications
        ):
            raise ValueError(
                "Les qualifications du salarié doivent contenir uniquement des EmployeeQualification."
            )

        required_requirements = tuple(
            requirement
            for requirement in mission.qualification_requirements
            if requirement.active and requirement.level is RequirementLevel.REQUIRED
        )
        held_qualification_ids = {
            employee_qualification.qualification.id
            for employee_qualification in qualifications
            if employee_qualification.employee.id == employee.id
            and employee_qualification.active
            and employee_qualification.status is QualificationStatus.VALID
        }

        satisfied_requirements = tuple(
            requirement
            for requirement in required_requirements
            if requirement.qualification.id in held_qualification_ids
        )
        missing_requirements = tuple(
            requirement
            for requirement in required_requirements
            if requirement.qualification.id not in held_qualification_ids
        )

        return QualificationEligibilityResult(
            employee=employee,
            mission=mission,
            satisfied_requirements=satisfied_requirements,
            missing_requirements=missing_requirements,
        )
