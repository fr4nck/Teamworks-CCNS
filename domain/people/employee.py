"""Objet métier représentant l'identité d'un salarié."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from .civility import Civility


@dataclass(frozen=True, slots=True)
class Employee:
    """Identité autonome d'un salarié, sans compte ni contrat.

    Les liens éventuels vers un compte utilisateur ou un contrat appartiendront
    à de futurs objets métier et ne sont volontairement pas modélisés ici.
    """

    id: UUID = field(default_factory=uuid4, kw_only=True)
    civility: Civility
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    professional_email: Optional[str] = None
    professional_phone: Optional[str] = None
    active: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant du salarié doit être un UUID.")
        if not isinstance(self.civility, Civility):
            raise ValueError("La civilité du salarié est invalide.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif du salarié doit être un booléen.")

        first_name = _required_text(self.first_name, "prénom")
        last_name = _required_text(self.last_name, "nom")
        birth_date = _validated_birth_date(self.birth_date)
        professional_email = _normalized_email(self.professional_email)
        professional_phone = _normalized_phone(self.professional_phone)

        object.__setattr__(self, "first_name", first_name)
        object.__setattr__(self, "last_name", last_name)
        object.__setattr__(self, "birth_date", birth_date)
        object.__setattr__(self, "professional_email", professional_email)
        object.__setattr__(self, "professional_phone", professional_phone)


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(f"Le {field_name} du salarié est obligatoire.")
    return normalized


def _validated_birth_date(value: Optional[date]) -> Optional[date]:
    if value is None:
        return None
    if not isinstance(value, date):
        raise ValueError("La date de naissance du salarié doit être une date.")
    if value > date.today():
        raise ValueError("La date de naissance du salarié ne peut pas être future.")
    return value


def _normalized_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip().lower()):
        raise ValueError("L'email professionnel du salarié est invalide.")

    local_part, separator, domain = normalized.partition("@")
    if (
        separator != "@"
        or not local_part
        or not domain
        or domain.startswith(".")
        or domain.endswith(".")
        or "." not in domain
        or " " in normalized
    ):
        raise ValueError("L'email professionnel du salarié est invalide.")
    return normalized


def _normalized_phone(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError("Le téléphone professionnel du salarié est invalide.")
    return normalized
