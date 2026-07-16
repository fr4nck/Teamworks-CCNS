"""États de cycle de vie d'un contrat."""

from enum import Enum


class ContractStatus(str, Enum):
    """Statut métier d'un contrat."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"
