"""Définition métier immutable d'une qualification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4

from .qualification_category import QualificationCategory


@dataclass(frozen=True, slots=True)
class Qualification:
    """Qualification disponible dans le référentiel de l'association.

    Cet objet définit une compétence, un diplôme, une certification, une
    habilitation ou une autorisation. Il ne porte pas l'attribution de cette
    qualification à un salarié.
    """

    code: str
    name: str
    category: QualificationCategory
    validity_duration_days: Optional[int] = None
    renewable: bool = False
    mandatory: bool = False
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de la qualification doit être un UUID.")
        if not isinstance(self.category, QualificationCategory):
            raise ValueError("La catégorie de la qualification est invalide.")
        if not isinstance(self.renewable, bool):
            raise ValueError("Le caractère renouvelable doit être un booléen.")
        if not isinstance(self.mandatory, bool):
            raise ValueError("Le caractère obligatoire doit être un booléen.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif doit être un booléen.")

        object.__setattr__(self, "code", _required_text(self.code, "code"))
        object.__setattr__(self, "name", _required_text(self.name, "nom"))
        object.__setattr__(
            self,
            "validity_duration_days",
            _validated_validity_duration(self.validity_duration_days),
        )

    def is_permanent(self) -> bool:
        """Indique si la qualification n'a pas de durée de validité."""

        return self.validity_duration_days is None

    def requires_renewal(self) -> bool:
        """Indique si la qualification doit être renouvelée."""

        return self.renewable

    def has_expiration(self) -> bool:
        """Indique si la qualification possède une durée de validité."""

        return self.validity_duration_days is not None


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(f"Le {field_name} de la qualification est obligatoire.")
    return normalized


def _validated_validity_duration(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("La durée de validité doit être un nombre entier de jours.")
    if value < 0:
        raise ValueError("La durée de validité ne peut pas être négative.")
    return value
