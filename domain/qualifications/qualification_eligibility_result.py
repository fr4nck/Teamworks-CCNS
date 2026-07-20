"""Résultat métier immutable d'éligibilité par qualification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from typing import TYPE_CHECKING

from domain.people import Employee

if TYPE_CHECKING:
    from domain.missions import Mission

from .qualification_requirement import QualificationRequirement


@dataclass(frozen=True, slots=True)
class QualificationEligibilityResult:
    """Résultat déclaratif de comparaison entre salarié et mission.

    Le résultat conserve uniquement la répartition des exigences REQUIRED
    actives d'une mission selon les qualifications VALID et actives détenues
    par le salarié analysé. Il ne déduit aucune équivalence, expiration,
    disponibilité ou règle réglementaire implicite.
    """

    employee: Employee
    mission: "Mission"
    satisfied_requirements: tuple[QualificationRequirement, ...]
    missing_requirements: tuple[QualificationRequirement, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié du résultat d'éligibilité doit être un Employee.")
        from domain.missions import Mission

        if not isinstance(self.mission, Mission):
            raise ValueError("La mission du résultat d'éligibilité doit être une Mission.")

        object.__setattr__(
            self,
            "satisfied_requirements",
            _validated_requirements(
                self.satisfied_requirements,
                "satisfaites",
            ),
        )
        object.__setattr__(
            self,
            "missing_requirements",
            _validated_requirements(
                self.missing_requirements,
                "manquantes",
            ),
        )

    def is_eligible(self) -> bool:
        """Indique si aucune exigence REQUIRED active ne manque."""

        return not self.missing_requirements

    def has_missing_requirements(self) -> bool:
        """Indique si au moins une exigence REQUIRED active est manquante."""

        return bool(self.missing_requirements)

    def satisfied_count(self) -> int:
        """Retourne le nombre d'exigences REQUIRED actives satisfaites."""

        return len(self.satisfied_requirements)

    def missing_count(self) -> int:
        """Retourne le nombre d'exigences REQUIRED actives manquantes."""

        return len(self.missing_requirements)


def _validated_requirements(
    value: Iterable[QualificationRequirement],
    label: str,
) -> tuple[QualificationRequirement, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"Les exigences {label} doivent être une collection.")
    try:
        requirements = tuple(value)
    except TypeError as error:
        raise ValueError(f"Les exigences {label} doivent être une collection.") from error

    if any(not isinstance(requirement, QualificationRequirement) for requirement in requirements):
        raise ValueError(
            f"Les exigences {label} doivent contenir uniquement des QualificationRequirement."
        )
    return requirements
