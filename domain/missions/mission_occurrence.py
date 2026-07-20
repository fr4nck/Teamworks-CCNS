"""Occurrence datée et horaire immutable d'une mission."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from domain.missions.mission import Mission


@dataclass(frozen=True, slots=True)
class MissionOccurrence:
    """Représente un créneau planifié concret d'une ``Mission``.

    Une occurrence porte uniquement les informations propres au créneau daté et
    horaire. Elle ne représente ni l'affectation d'un salarié, ni une récurrence,
    ni une décision d'éligibilité, ni une règle de temps de travail.
    """

    mission: Mission
    starts_at: datetime
    ends_at: datetime
    location: Optional[str] = None
    observations: Optional[str] = None
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de l'occurrence de mission doit être un UUID.")
        if not isinstance(self.mission, Mission):
            raise ValueError("La mission est obligatoire et doit être une Mission.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif de l'occurrence de mission doit être un booléen.")

        starts_at = _validated_datetime(self.starts_at, "début")
        ends_at = _validated_datetime(self.ends_at, "fin")
        if _is_aware(starts_at) != _is_aware(ends_at):
            raise ValueError(
                "Les dates et heures de début et de fin de l'occurrence de mission "
                "doivent être toutes les deux naïves ou toutes les deux avec fuseau horaire."
            )
        if ends_at <= starts_at:
            raise ValueError(
                "La date et heure de fin de l'occurrence de mission doit être strictement "
                "postérieure à sa date et heure de début."
            )

        object.__setattr__(self, "starts_at", starts_at)
        object.__setattr__(self, "ends_at", ends_at)
        object.__setattr__(self, "location", _normalized_optional_text(self.location, "lieu"))
        object.__setattr__(
            self,
            "observations",
            _normalized_optional_text(self.observations, "observations"),
        )

    def duration(self) -> timedelta:
        """Retourne la durée exacte de l'occurrence, sans arrondi."""

        return self.ends_at - self.starts_at

    def has_location(self) -> bool:
        """Indique si un lieu est renseigné pour l'occurrence."""

        return self.location is not None

    def is_active(self) -> bool:
        """Retourne strictement le statut actif déclaré, sans calcul calendaire."""

        return self.active

    def occurs_on(self, day: date) -> bool:
        """Indique si l'occurrence commence le jour civil fourni."""

        if isinstance(day, datetime) or not isinstance(day, date):
            raise ValueError("Le jour de l'occurrence de mission doit être une date.")
        return self.starts_at.date() == day


def _validated_datetime(value: datetime, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        raise ValueError(
            f"La date et heure de {field_name} de l'occurrence de mission doit être un datetime."
        )
    raise ValueError(
        f"La date et heure de {field_name} de l'occurrence de mission doit être un datetime."
    )


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _normalized_optional_text(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(f"Le champ {field_name} de l'occurrence de mission est invalide.")
    return normalized
