"""Définition métier immutable d'une mission réutilisable."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional
from uuid import UUID, uuid4

from domain.qualifications import QualificationRequirement


@dataclass(frozen=True, slots=True)
class Mission:
    """Définit une fonction ou intervention métier réutilisable.

    Une mission décrit son identité fonctionnelle et les exigences de
    qualification qui lui sont associées. Elle ne représente ni une occurrence
    planifiée, ni une affectation de salarié, ni une décision d'éligibilité.
    """

    code: str
    name: str
    description: Optional[str] = None
    qualification_requirements: tuple[QualificationRequirement, ...] = field(
        default_factory=tuple
    )
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de la mission doit être un UUID.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif de la mission doit être un booléen.")

        object.__setattr__(self, "code", _normalized_code(self.code))
        object.__setattr__(self, "name", _required_text(self.name, "nom"))
        object.__setattr__(self, "description", _normalized_optional_text(self.description))
        object.__setattr__(
            self,
            "qualification_requirements",
            _validated_qualification_requirements(self.qualification_requirements),
        )

    def has_qualification_requirements(self) -> bool:
        """Indique si la mission porte au moins une exigence de qualification."""

        return bool(self.qualification_requirements)

    def qualification_requirement_count(self) -> int:
        """Retourne le nombre d'exigences de qualification de la mission."""

        return len(self.qualification_requirements)

    def required_qualification_requirements(self) -> tuple[QualificationRequirement, ...]:
        """Retourne les exigences dont le niveau est requis."""

        return tuple(
            requirement
            for requirement in self.qualification_requirements
            if requirement.is_required()
        )

    def recommended_qualification_requirements(self) -> tuple[QualificationRequirement, ...]:
        """Retourne les exigences dont le niveau est recommandé."""

        return tuple(
            requirement
            for requirement in self.qualification_requirements
            if requirement.is_recommended()
        )

    def optional_qualification_requirements(self) -> tuple[QualificationRequirement, ...]:
        """Retourne les exigences dont le niveau est optionnel."""

        return tuple(
            requirement
            for requirement in self.qualification_requirements
            if requirement.is_optional()
        )


def _normalized_code(value: str) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError("Le code de la mission est obligatoire.")
    return normalized.upper()


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(f"Le {field_name} de la mission est obligatoire.")
    return normalized


def _normalized_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError("La description de la mission est invalide.")
    return normalized


def _validated_qualification_requirements(
    value: Iterable[QualificationRequirement],
) -> tuple[QualificationRequirement, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("Les exigences de qualification doivent être une collection.")
    try:
        requirements = tuple(value)
    except TypeError as error:
        raise ValueError("Les exigences de qualification doivent être une collection.") from error

    if any(not isinstance(requirement, QualificationRequirement) for requirement in requirements):
        raise ValueError(
            "Les exigences de qualification doivent contenir uniquement des QualificationRequirement."
        )
    if len({requirement.id for requirement in requirements}) != len(requirements):
        raise ValueError("Une mission ne peut pas contenir deux exigences du même identifiant.")
    return requirements
