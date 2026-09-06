"""Contrat métier commun pour les durées signées.

Ce module est volontairement indépendant de wx et Qt.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class BusinessError:
    code: str
    message: str
    field: str


@dataclass(frozen=True)
class DurationResult:
    ok: bool
    value_minutes: Optional[int] = None
    display: Optional[str] = None
    error: Optional[BusinessError] = None


_TIME_RE = re.compile(r"^(\d{2}):(\d{2})$")


def _error(code: str, message: str, field: str) -> DurationResult:
    return DurationResult(ok=False, error=BusinessError(code, message, field))


def parse_time(value, field: str) -> DurationResult:
    """Valide un horaire HH:MM et retourne sa valeur en minutes."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return _error("MISSING_TIME", "L'horaire est obligatoire.", field)
    if not isinstance(value, str):
        return _error("INVALID_TIME_TYPE", "L'horaire doit être une chaîne au format HH:MM.", field)

    match = _TIME_RE.fullmatch(value.strip())
    if match is None:
        return _error("INVALID_TIME_FORMAT", "L'horaire doit être au format HH:MM.", field)

    hour, minute = (int(part) for part in match.groups())
    if hour > 23 or minute > 59:
        return _error("INVALID_TIME_VALUE", "L'horaire doit être compris entre 00:00 et 23:59.", field)

    return DurationResult(ok=True, value_minutes=hour * 60 + minute)


def format_signed_duration(value_minutes: int) -> str:
    """Formate une durée signée sans perdre le signe pour les valeurs < 1 heure."""
    sign = "-" if value_minutes < 0 else ""
    absolute = abs(value_minutes)
    hours, minutes = divmod(absolute, 60)
    return f"{sign}{hours}:{minutes:02d}"


def calculate_signed_duration(debut, fin, *, allow_overnight: bool = False) -> DurationResult:
    """Calcule ``fin - debut`` et retourne toujours un résultat métier structuré.

    Une différence négative est valide par défaut. ``allow_overnight`` ne transforme
    donc jamais silencieusement une valeur négative en passage de minuit : le contexte
    appelant doit exprimer explicitement cette intention.
    """
    start = parse_time(debut, "debut")
    if not start.ok:
        return start
    end = parse_time(fin, "fin")
    if not end.ok:
        return end

    value = end.value_minutes - start.value_minutes
    if allow_overnight and value < 0:
        value += 24 * 60

    return DurationResult(ok=True, value_minutes=value, display=format_signed_duration(value))
