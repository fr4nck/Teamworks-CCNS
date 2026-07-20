"""Indisponibilité datée et horaire immutable d'un salarié."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from domain.people import Employee

from .employee_unavailability_reason import EmployeeUnavailabilityReason


@dataclass(frozen=True, slots=True)
class EmployeeUnavailability:
    """Période déclarée pendant laquelle un ``Employee`` est indisponible.

    L'objet représente uniquement une indisponibilité métier déclarative. Il ne
    consulte pas la date courante, ne contrôle aucune affectation et ne porte
    aucune règle de congé, de paie, de contrat, de récurrence ou de planning.
    """

    employee: Employee
    starts_at: datetime
    ends_at: datetime
    reason: EmployeeUnavailabilityReason
    label: Optional[str] = None
    observations: Optional[str] = None
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de l'indisponibilité salarié doit être un UUID.")
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié est obligatoire et doit être un Employee.")
        if not isinstance(self.reason, EmployeeUnavailabilityReason):
            raise ValueError(
                "Le motif de l'indisponibilité salarié doit être un EmployeeUnavailabilityReason."
            )
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif de l'indisponibilité salarié doit être un booléen.")

        starts_at = _validated_datetime(self.starts_at, "début")
        ends_at = _validated_datetime(self.ends_at, "fin")
        _ensure_compatible_datetimes(starts_at, ends_at)
        if ends_at <= starts_at:
            raise ValueError(
                "La date et heure de fin de l'indisponibilité salarié doit être strictement "
                "postérieure à sa date et heure de début."
            )

        object.__setattr__(self, "starts_at", starts_at)
        object.__setattr__(self, "ends_at", ends_at)
        object.__setattr__(self, "label", _normalized_optional_text(self.label, "libellé"))
        object.__setattr__(
            self,
            "observations",
            _normalized_optional_text(self.observations, "observations"),
        )

    def duration(self) -> timedelta:
        """Retourne la durée exacte de l'indisponibilité, sans arrondi."""

        return self.ends_at - self.starts_at

    def is_active(self) -> bool:
        """Retourne strictement le statut actif déclaré, sans calcul calendaire."""

        return self.active

    def has_label(self) -> bool:
        """Indique si un libellé est renseigné."""

        return self.label is not None

    def has_observations(self) -> bool:
        """Indique si des observations sont renseignées."""

        return self.observations is not None

    def overlaps(self, starts_at: datetime, ends_at: datetime) -> bool:
        """Indique si l'indisponibilité chevauche l'intervalle semi-ouvert fourni."""

        starts_at = _validated_datetime(starts_at, "début de l'intervalle")
        ends_at = _validated_datetime(ends_at, "fin de l'intervalle")
        _ensure_compatible_datetimes(starts_at, ends_at)
        _ensure_compatible_datetimes(self.starts_at, starts_at)
        if ends_at <= starts_at:
            raise ValueError("L'intervalle comparé doit avoir une durée strictement positive.")
        return self.starts_at < ends_at and starts_at < self.ends_at

    def contains(self, moment: datetime) -> bool:
        """Indique si le moment appartient à l'intervalle semi-ouvert de l'indisponibilité."""

        moment = _validated_datetime(moment, "moment")
        _ensure_compatible_datetimes(self.starts_at, moment)
        return self.starts_at <= moment < self.ends_at


def _validated_datetime(value: datetime, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        raise ValueError(
            f"La date et heure de {field_name} de l'indisponibilité salarié doit être un datetime."
        )
    raise ValueError(
        f"La date et heure de {field_name} de l'indisponibilité salarié doit être un datetime."
    )


def _ensure_compatible_datetimes(first: datetime, second: datetime) -> None:
    if _is_aware(first) != _is_aware(second):
        raise ValueError(
            "Les dates et heures de l'indisponibilité salarié doivent être toutes naïves "
            "ou toutes avec fuseau horaire."
        )
    if _is_aware(first) and first.tzinfo != second.tzinfo:
        raise ValueError(
            "Les dates et heures de l'indisponibilité salarié doivent utiliser des fuseaux horaires compatibles."
        )


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _normalized_optional_text(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(f"Le champ {field_name} de l'indisponibilité salarié est invalide.")
    return normalized
