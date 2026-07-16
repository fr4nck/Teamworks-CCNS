"""Civilités portées par l'identité d'un salarié."""

from enum import Enum


class Civility(str, Enum):
    """Civilité déclarée pour un salarié."""

    MADAME = "madame"
    MONSIEUR = "monsieur"
