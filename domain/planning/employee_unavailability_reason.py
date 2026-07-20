"""Motifs déclaratifs d'indisponibilité d'un salarié."""

from enum import Enum


class EmployeeUnavailabilityReason(str, Enum):
    """Motif métier déclaré d'une indisponibilité salarié.

    Cette énumération ne porte aucune règle automatique de paie, de contrat,
    de congé ou de temps de travail.
    """

    LEAVE = "LEAVE"
    SICKNESS = "SICKNESS"
    TRAINING = "TRAINING"
    PERSONAL = "PERSONAL"
    PROFESSIONAL = "PROFESSIONAL"
    OTHER = "OTHER"
