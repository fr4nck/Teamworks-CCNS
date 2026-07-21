"""Statuts déclarés d'un planning."""

from enum import Enum


class PlanningStatus(str, Enum):
    """Représente uniquement l'état déclaré d'un planning."""

    DRAFT = "draft"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"
