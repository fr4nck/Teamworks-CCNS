"""Disponibilité hebdomadaire immutable déclarée pour un salarié."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional
from uuid import UUID, uuid4

from domain.people import Employee

from .weekday import Weekday

_DURATION_REFERENCE_DATE = date(2000, 1, 3)


@dataclass(frozen=True, slots=True)
class EmployeeWeeklyAvailability:
    """Créneau hebdomadaire déclaré pendant lequel un ``Employee`` est disponible.

    L'objet représente uniquement une disponibilité habituelle selon un jour de
    semaine. Il ne consulte pas la date courante, ne contrôle aucune affectation
    et ne porte aucune règle de paie, de contrat, de repos ou de priorité.
    """

    employee: Employee
    weekday: Weekday
    starts_at: time
    ends_at: time
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    label: Optional[str] = None
    observations: Optional[str] = None
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de la disponibilité hebdomadaire doit être un UUID.")
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié est obligatoire et doit être un Employee.")
        if not isinstance(self.weekday, Weekday):
            raise ValueError("Le jour de disponibilité hebdomadaire doit être un Weekday.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif de la disponibilité hebdomadaire doit être un booléen.")

        starts_at = _validated_time(self.starts_at, "début")
        ends_at = _validated_time(self.ends_at, "fin")
        _ensure_compatible_times(starts_at, ends_at)
        if ends_at <= starts_at:
            raise ValueError(
                "L'heure de fin de la disponibilité hebdomadaire doit être strictement "
                "postérieure à son heure de début, sans traverser minuit."
            )

        effective_from = _validated_optional_date(self.effective_from, "début d'application")
        effective_until = _validated_optional_date(self.effective_until, "fin d'application")
        if effective_from is not None and effective_until is not None and effective_until < effective_from:
            raise ValueError(
                "La date de fin d'application de la disponibilité hebdomadaire doit être "
                "supérieure ou égale à sa date de début."
            )

        object.__setattr__(self, "starts_at", starts_at)
        object.__setattr__(self, "ends_at", ends_at)
        object.__setattr__(self, "effective_from", effective_from)
        object.__setattr__(self, "effective_until", effective_until)
        object.__setattr__(self, "label", _normalized_optional_text(self.label, "libellé"))
        object.__setattr__(self, "observations", _normalized_optional_text(self.observations, "observations"))

    def duration(self) -> timedelta:
        """Retourne la durée exacte du créneau, sans arrondi ni date courante."""

        start = datetime.combine(_DURATION_REFERENCE_DATE, self.starts_at)
        end = datetime.combine(_DURATION_REFERENCE_DATE, self.ends_at)
        return end - start

    def is_active(self) -> bool:
        """Retourne strictement le statut actif déclaré."""

        return self.active

    def has_label(self) -> bool:
        """Indique si un libellé est renseigné."""

        return self.label is not None

    def has_observations(self) -> bool:
        """Indique si des observations sont renseignées."""

        return self.observations is not None

    def has_effective_start(self) -> bool:
        """Indique si une date de début d'application est renseignée."""

        return self.effective_from is not None

    def has_effective_end(self) -> bool:
        """Indique si une date de fin d'application est renseignée."""

        return self.effective_until is not None

    def applies_on(self, day: date) -> bool:
        """Indique si le créneau s'applique au jour civil fourni, hors statut actif."""

        day = _validated_date(day, "jour testé")
        return (
            day.isoweekday() == self.weekday.value
            and (self.effective_from is None or day >= self.effective_from)
            and (self.effective_until is None or day <= self.effective_until)
        )

    def contains(self, moment: datetime) -> bool:
        """Indique si le moment appartient à l'intervalle semi-ouvert du créneau."""

        moment = _validated_datetime(moment)
        moment_time = moment.timetz()
        _ensure_compatible_times(self.starts_at, moment_time)
        comparison_time = moment_time if _is_aware_time(self.starts_at) else moment.time()
        return self.applies_on(moment.date()) and self.starts_at <= comparison_time < self.ends_at


def _validated_time(value: time, field_name: str) -> time:
    if isinstance(value, datetime):
        raise ValueError(f"L'heure de {field_name} de la disponibilité hebdomadaire doit être un time.")
    if isinstance(value, time):
        return value
    raise ValueError(f"L'heure de {field_name} de la disponibilité hebdomadaire doit être un time.")


def _validated_datetime(value: datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        raise ValueError("Le moment testé de la disponibilité hebdomadaire doit être un datetime.")
    raise ValueError("Le moment testé de la disponibilité hebdomadaire doit être un datetime.")


def _validated_optional_date(value: Optional[date], field_name: str) -> Optional[date]:
    if value is None:
        return None
    return _validated_date(value, field_name)


def _validated_date(value: date, field_name: str) -> date:
    if isinstance(value, datetime):
        raise ValueError(f"La date de {field_name} de la disponibilité hebdomadaire doit être une date.")
    if isinstance(value, date):
        return value
    raise ValueError(f"La date de {field_name} de la disponibilité hebdomadaire doit être une date.")


def _ensure_compatible_times(first: time, second: time) -> None:
    if _is_aware_time(first) != _is_aware_time(second):
        raise ValueError(
            "Les heures de la disponibilité hebdomadaire doivent être toutes naïves ou toutes avec fuseau horaire."
        )
    if _is_aware_time(first) and first.tzinfo != second.tzinfo:
        raise ValueError(
            "Les heures de la disponibilité hebdomadaire doivent utiliser des fuseaux horaires compatibles."
        )


def _is_aware_time(value: time) -> bool:
    return value.tzinfo is not None


def _normalized_optional_text(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(f"Le champ {field_name} de la disponibilité hebdomadaire est invalide.")
    return normalized
