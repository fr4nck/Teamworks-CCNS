"""Statuts métier possibles pour une qualification détenue par un salarié."""

from enum import Enum


class QualificationStatus(str, Enum):
    """État déclaré de la détention d'une qualification."""

    VALID = "valid"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING = "pending"
    REVOKED = "revoked"
