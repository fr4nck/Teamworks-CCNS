"""Définition métier immutable d'une exigence de qualification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4

from .qualification import Qualification
from .requirement_level import RequirementLevel


@dataclass(frozen=True, slots=True)
class QualificationRequirement:
    """Qualification exigée par un besoin métier non encore rattaché.

    Cet objet décrit uniquement une exigence. Il ne représente ni une mission,
    ni un poste, ni une activité, ni la qualification détenue par un salarié.
    """

    qualification: Qualification
    level: RequirementLevel
    mandatory: bool = True
    active: bool = True
    observations: Optional[str] = None
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de l'exigence de qualification doit être un UUID.")
        if not isinstance(self.qualification, Qualification):
            raise ValueError("La qualification est obligatoire et doit être une Qualification.")
        if not isinstance(self.level, RequirementLevel):
            raise ValueError("Le niveau d'exigence de qualification est invalide.")
        if not isinstance(self.mandatory, bool):
            raise ValueError("Le caractère obligatoire de l'exigence doit être un booléen.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif de l'exigence doit être un booléen.")

        object.__setattr__(
            self,
            "observations",
            _normalized_optional_text(self.observations),
        )

    def is_required(self) -> bool:
        """Indique si le niveau d'exigence est requis."""

        return self.level is RequirementLevel.REQUIRED

    def is_recommended(self) -> bool:
        """Indique si le niveau d'exigence est recommandé."""

        return self.level is RequirementLevel.RECOMMENDED

    def is_optional(self) -> bool:
        """Indique si le niveau d'exigence est optionnel."""

        return self.level is RequirementLevel.OPTIONAL


def _normalized_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError("Le champ observations est invalide.")
    return normalized
