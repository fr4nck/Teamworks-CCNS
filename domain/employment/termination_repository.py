"""Contrat de persistance des sorties salarié (SORTIE-002).

Règles de version (optimistic locking) :

- ``ContractTermination.version`` est la révision persistée ; 0 signifie
  « jamais enregistrée » ;
- ``add`` enregistre une sortie neuve en révision 1 ;
- ``save`` n'écrit que si la révision en base est encore celle portée par
  l'objet, puis l'avance d'exactement +1, quelle que soit la quantité de
  mutations effectuées en mémoire depuis la lecture ;
- un écrivain en retard reçoit ``TerminationVersionConflict`` et rien de ce
  qu'il portait n'est écrit ; il doit relire avant de recommencer.

Un contrat porte au plus une sortie active (non clôturée). Aucune sortie n'est
jamais déduite d'une date de fin de contrat.
"""
from __future__ import annotations

from typing import Optional, Protocol

from domain.employment.termination import ContractTermination


class TerminationPersistenceError(RuntimeError):
    """Refus déterministe de persistance, identifié par un code stable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class TerminationVersionConflict(TerminationPersistenceError):
    def __init__(self, termination_id: str, expected_version: int) -> None:
        super().__init__(
            "TERMINATION_VERSION_CONFLICT",
            f"termination {termination_id} changed since version {expected_version}",
        )
        self.termination_id = termination_id
        self.expected_version = expected_version


class TerminationNotFound(TerminationPersistenceError):
    def __init__(self, termination_id: str) -> None:
        super().__init__("TERMINATION_NOT_FOUND", f"termination {termination_id} does not exist")
        self.termination_id = termination_id


class ActiveTerminationExists(TerminationPersistenceError):
    def __init__(self, contract_id: str) -> None:
        super().__init__(
            "ACTIVE_TERMINATION_EXISTS",
            f"contract {contract_id} already has an active termination",
        )
        self.contract_id = contract_id


class TerminationAlreadyExists(TerminationPersistenceError):
    def __init__(self, termination_id: str) -> None:
        super().__init__("TERMINATION_ALREADY_EXISTS", f"termination {termination_id} already exists")
        self.termination_id = termination_id


class ContractTerminationRepository(Protocol):
    def add(self, termination: ContractTermination) -> None: ...

    def get(self, termination_id: str) -> Optional[ContractTermination]: ...

    def get_active_for_contract(self, contract_id: str) -> Optional[ContractTermination]: ...

    def save(self, termination: ContractTermination) -> None: ...


class CommandIdempotencyConflict(TerminationPersistenceError):
    """Même command_id rejoué avec une opération ou un contenu différent."""

    def __init__(self, command_id: str) -> None:
        super().__init__(
            "COMMAND_IDEMPOTENCY_CONFLICT",
            f"command {command_id} was already used for a different operation",
        )
        self.command_id = command_id


class TransmissionRetryExhausted(TerminationPersistenceError):
    """Interblocages InnoDB répétés : rien n'a été enregistré."""

    def __init__(self, attempts: int) -> None:
        super().__init__(
            "TRANSMISSION_DEADLOCK_RETRY_EXHAUSTED",
            f"transaction rolled back by deadlock {attempts} times; nothing was recorded",
        )
        self.attempts = attempts


class SnapshotIntegrityError(TerminationPersistenceError):
    """Un snapshot relu ne correspond plus à son hash ou à sa chaîne."""
