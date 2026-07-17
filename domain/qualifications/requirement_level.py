"""Niveaux métier possibles pour une exigence de qualification."""

from enum import Enum


class RequirementLevel(str, Enum):
    """Niveau d'exigence associé à une qualification requise."""

    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"
