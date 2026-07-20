"""Affectation métier immutable d'un salarié à une mission."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.missions.mission import Mission
from domain.people import Employee


@dataclass(frozen=True, slots=True)
class MissionAssignment:
    """Représente l'affectation générale d'un salarié à une mission.

    Cette affectation relie un ``Employee`` à une ``Mission`` sur une période
    métier éventuellement délimitée. Elle ne représente ni une occurrence
    planifiée, ni un créneau horaire, ni une décision d'éligibilité.
    """

    employee: Employee
    mission: Mission
    starts_on: Optional[date] = None
    ends_on: Optional[date] = None
    active: bool = True
    observations: Optional[str] = None
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de l'affectation de mission doit être un UUID.")
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié est obligatoire et doit être un Employee.")
        if not isinstance(self.mission, Mission):
            raise ValueError("La mission est obligatoire et doit être une Mission.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif de l'affectation de mission doit être un booléen.")

        starts_on = _validated_optional_date(self.starts_on, "début")
        ends_on = _validated_optional_date(self.ends_on, "fin")
        if starts_on is not None and ends_on is not None and ends_on < starts_on:
            raise ValueError(
                "La date de fin de l'affectation de mission ne peut pas être antérieure "
                "à sa date de début."
            )

        object.__setattr__(self, "starts_on", starts_on)
        object.__setattr__(self, "ends_on", ends_on)
        object.__setattr__(self, "observations", _normalized_observations(self.observations))

    def has_start_date(self) -> bool:
        """Indique si l'affectation possède une date de début déclarée."""

        return self.starts_on is not None

    def has_end_date(self) -> bool:
        """Indique si l'affectation possède une date de fin déclarée."""

        return self.ends_on is not None

    def is_open_ended(self) -> bool:
        """Indique si l'affectation n'a pas de date de fin déclarée."""

        return self.ends_on is None

    def is_active(self) -> bool:
        """Retourne strictement le statut actif déclaré, sans calcul calendaire."""

        return self.active


def _validated_optional_date(value: Optional[date], field_name: str) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValueError(
            f"La date de {field_name} de l'affectation de mission doit être une date."
        )
    return value


def _normalized_observations(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError("Les observations de l'affectation de mission sont invalides.")
    return normalized
