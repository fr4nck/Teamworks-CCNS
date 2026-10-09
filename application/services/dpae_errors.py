"""Erreurs DPAE stables pour les services et la future UI opérateur.

Les codes sont internes à Teamworks : ils ne décrivent aucun protocole externe.
"""
from typing import Optional


class DpaeError(Exception):
    """Erreur DPAE identifiable sans analyser son message humain."""

    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        *,
        field: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ):
        self.code = code
        self.field = field
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(message or code)


class DpaeConfigurationError(DpaeError, RuntimeError):
    """Configuration applicative DPAE absente ou incohérente."""


class DpaeDataError(DpaeError, ValueError):
    """Donnée interne incohérente avant persistance d'une opération."""


class DpaeTransitionError(DpaeError):
    """État métier incompatible avec l'opération demandée."""


class DpaeIdempotencyConflict(DpaeError):
    """Même identifiant idempotent avec un contenu différent."""


class DpaeIntegrityError(DpaeError, ValueError):
    """Conflit d'intégrité sur une donnée DPAE durable."""
