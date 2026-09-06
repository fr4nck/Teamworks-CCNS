"""Contrats métier communs pour horaires et durées signées.

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


_CLOCK_TIME_RE = re.compile(r"^(\d{2}):(\d{2})$")
_SIGNED_DURATION_RE = re.compile(r"^([+-])(\d+):(\d{2})$")


def _error(code: str, message: str, field: str) -> DurationResult:
    return DurationResult(ok=False, error=BusinessError(code, message, field))


def parse_clock_time(value, field: str) -> DurationResult:
    """Valide un horaire de journée HH:MM et retourne sa valeur en minutes.

    Un horaire est borné à 00:00..23:59.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return _error("MISSING_TIME", "L'horaire est obligatoire.", field)
    if not isinstance(value, str):
        return _error("INVALID_TIME_TYPE", "L'horaire doit être une chaîne au format HH:MM.", field)

    match = _CLOCK_TIME_RE.fullmatch(value.strip())
    if match is None:
        return _error("INVALID_TIME_FORMAT", "L'horaire doit être au format HH:MM.", field)

    hour, minute = (int(part) for part in match.groups())
    if hour > 23 or minute > 59:
        return _error("INVALID_TIME_VALUE", "L'horaire doit être compris entre 00:00 et 23:59.", field)

    return DurationResult(ok=True, value_minutes=hour * 60 + minute)


# Alias conservé pour ne pas casser les premiers consommateurs du contrat.
parse_time = parse_clock_time


def parse_signed_duration(value, field: str) -> DurationResult:
    """Valide une durée cumulée signée de forme +H:MM ou -H:MM.

    Contrairement à un horaire de journée, le nombre d'heures n'est pas limité à 23.
    ``None`` vaut zéro afin de préserver le contrat historique wx d'OperationHeures.
    """
    if value is None:
        return DurationResult(ok=True, value_minutes=0)
    if not isinstance(value, str):
        return _error(
            "INVALID_DURATION_TYPE",
            "La durée doit être une chaîne signée au format +H:MM ou -H:MM.",
            field,
        )

    text = value.strip()
    match = _SIGNED_DURATION_RE.fullmatch(text)
    if match is None:
        return _error(
            "INVALID_DURATION_FORMAT",
            "La durée doit être au format +H:MM ou -H:MM.",
            field,
        )

    sign, hours_text, minutes_text = match.groups()
    minutes = int(minutes_text)
    if minutes > 59:
        return _error(
            "INVALID_DURATION_VALUE",
            "Les minutes d'une durée doivent être comprises entre 00 et 59.",
            field,
        )

    total = int(hours_text) * 60 + minutes
    if sign == "-":
        total = -total
    return DurationResult(ok=True, value_minutes=total)


def format_signed_duration(value_minutes: int) -> str:
    """Formate une durée métier signée, sans '+' explicite pour les positives."""
    sign = "-" if value_minutes < 0 else ""
    absolute = abs(value_minutes)
    hours, minutes = divmod(absolute, 60)
    return f"{sign}{hours}:{minutes:02d}"


def calculate_time_difference(debut, fin, *, allow_overnight: bool = False) -> DurationResult:
    """Calcule ``fin - debut`` à partir de deux horaires de journée.

    Une différence négative est valide par défaut. Le passage de minuit n'est appliqué
    que si le contexte appelant le demande explicitement.
    """
    start = parse_clock_time(debut, "debut")
    if not start.ok:
        return start
    end = parse_clock_time(fin, "fin")
    if not end.ok:
        return end

    value = end.value_minutes - start.value_minutes
    if allow_overnight and value < 0:
        value += 24 * 60

    return DurationResult(ok=True, value_minutes=value, display=format_signed_duration(value))


# Nom historique du premier contrat, conservé pour compatibilité.
calculate_signed_duration = calculate_time_difference


def operate_signed_durations(value_a, value_b, operation="addition") -> DurationResult:
    """Additionne ou soustrait deux durées cumulées signées.

    Les durées peuvent dépasser 23 heures. ``None`` est traité comme zéro, comme dans
    l'implémentation historique wx d'OperationHeures.
    """
    a = parse_signed_duration(value_a, "value_a")
    if not a.ok:
        return a
    b = parse_signed_duration(value_b, "value_b")
    if not b.ok:
        return b

    if operation == "addition":
        value = a.value_minutes + b.value_minutes
    elif operation == "soustraction":
        value = a.value_minutes - b.value_minutes
    else:
        return _error(
            "INVALID_DURATION_OPERATION",
            "L'opération doit être 'addition' ou 'soustraction'.",
            "operation",
        )

    return DurationResult(ok=True, value_minutes=value, display=format_signed_duration(value))
