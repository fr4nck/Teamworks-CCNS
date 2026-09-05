"""Objets métier du domaine emploi/RH."""

from .session_actual import (
    CONTRACT_VERSION,
    EVENT_TYPE,
    SOURCE_DOMAIN,
    SessionActual,
    SessionActualContractError,
)

__all__ = [
    "CONTRACT_VERSION",
    "EVENT_TYPE",
    "SOURCE_DOMAIN",
    "SessionActual",
    "SessionActualContractError",
]
