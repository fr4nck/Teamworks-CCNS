"""Types de contrats portés par le domaine des personnes."""

from enum import Enum


class ContractType(str, Enum):
    """Nature juridique d'un engagement entre un salarié et l'association."""

    CDI = "CDI"
    CDD = "CDD"
    CEE = "CEE"
    APPRENTICESHIP = "APPRENTICESHIP"
    INTERNSHIP = "INTERNSHIP"
    CIVIC_SERVICE = "CIVIC_SERVICE"
