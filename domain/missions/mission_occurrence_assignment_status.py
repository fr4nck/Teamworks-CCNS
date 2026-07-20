"""Statuts déclarés d'une affectation à une occurrence de mission."""

from enum import Enum


class MissionOccurrenceAssignmentStatus(str, Enum):
    """État métier déclaré de l'affectation d'un salarié à une occurrence."""

    PLANNED = "PLANNED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    ABSENT = "ABSENT"
