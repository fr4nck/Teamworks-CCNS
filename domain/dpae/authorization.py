"""Autorisation des commandes DPAE.

La classe d'exécution est une barrière structurelle : attribuer par erreur une
capability humaine à un JOB ou SERVICE ne lui permet jamais d'exécuter une
commande HUMAN_ONLY.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Type

from .case_transition import DpaeCapability
from .model import DpaeDomainError


class ActorType(str, Enum):
    USER = "USER"
    SERVICE = "SERVICE"
    JOB = "JOB"


class ExecutionClass(str, Enum):
    HUMAN_ONLY = "HUMAN_ONLY"
    TECHNICAL_ONLY = "TECHNICAL_ONLY"
    AUTOMATION_ALLOWED = "AUTOMATION_ALLOWED"
    INTERNAL_ONLY = "INTERNAL_ONLY"


@dataclass(frozen=True)
class ActorContext:
    actor_type: ActorType
    actor_id: str
    capabilities: FrozenSet[DpaeCapability] = frozenset()
    execution_id: str | None = None


@dataclass(frozen=True)
class CommandPolicy:
    execution_class: ExecutionClass
    required_capabilities: FrozenSet[DpaeCapability] = frozenset()
    allowed_services: FrozenSet[str] = frozenset()
    allowed_jobs: FrozenSet[str] = frozenset()


# Marqueurs de commandes : les payloads métier concrets peuvent les étendre.
class PrepareDpaeCase: pass
class ValidateDpaeCase: pass
class AcknowledgeDpaeWarnings: pass
class CorrectDpaeCase: pass
class RequestDpaeSubmission: pass
class ExecuteAuthorizedSubmission: pass
class RecordTransportAcceptance: pass
class MarkSubmissionOutcomeUnknown: pass
class IngestDpaeReturn: pass
class ProposeReturnCorrelation: pass
class ResolveAmbiguousCorrelation: pass
class ApplyConfirmedReturn: pass
class ResolveUnknownOutcome: pass
class CancelDpaeCase: pass
class ExceptionallyCloseDpaeCase: pass
class CloseRegisteredCase: pass


COMMAND_POLICIES: dict[Type[object], CommandPolicy] = {
    PrepareDpaeCase: CommandPolicy(ExecutionClass.AUTOMATION_ALLOWED, frozenset({DpaeCapability.PREPARE}), frozenset({"CONTRACT_SERVICE"}), frozenset({"DPAE_PREPARATION_JOB"})),
    ValidateDpaeCase: CommandPolicy(ExecutionClass.AUTOMATION_ALLOWED, allowed_services=frozenset({"DPAE_VALIDATOR"}), allowed_jobs=frozenset({"DPAE_VALIDATION_JOB"})),
    AcknowledgeDpaeWarnings: CommandPolicy(ExecutionClass.HUMAN_ONLY, frozenset({DpaeCapability.REVIEW_RETURN})),
    CorrectDpaeCase: CommandPolicy(ExecutionClass.HUMAN_ONLY, frozenset({DpaeCapability.CORRECT})),
    RequestDpaeSubmission: CommandPolicy(ExecutionClass.HUMAN_ONLY, frozenset({DpaeCapability.SUBMIT})),
    ExecuteAuthorizedSubmission: CommandPolicy(ExecutionClass.TECHNICAL_ONLY, allowed_services=frozenset({"DPAE_GATEWAY"}), allowed_jobs=frozenset({"DPAE_SEND_RETRY_JOB"})),
    RecordTransportAcceptance: CommandPolicy(ExecutionClass.TECHNICAL_ONLY, allowed_services=frozenset({"DPAE_GATEWAY"})),
    MarkSubmissionOutcomeUnknown: CommandPolicy(ExecutionClass.AUTOMATION_ALLOWED, allowed_services=frozenset({"DPAE_GATEWAY", "DPAE_RECONCILIATION_SERVICE"}), allowed_jobs=frozenset({"DPAE_RECONCILIATION_JOB"})),
    IngestDpaeReturn: CommandPolicy(ExecutionClass.AUTOMATION_ALLOWED, allowed_services=frozenset({"DPAE_RETURN_RECEIVER"}), allowed_jobs=frozenset({"DPAE_RETURN_IMPORT_JOB"})),
    ProposeReturnCorrelation: CommandPolicy(ExecutionClass.AUTOMATION_ALLOWED, allowed_services=frozenset({"DPAE_CORRELATION_ENGINE"}), allowed_jobs=frozenset({"DPAE_CORRELATION_JOB"})),
    ResolveAmbiguousCorrelation: CommandPolicy(ExecutionClass.HUMAN_ONLY, frozenset({DpaeCapability.REVIEW_RETURN})),
    ApplyConfirmedReturn: CommandPolicy(ExecutionClass.TECHNICAL_ONLY, allowed_services=frozenset({"DPAE_RETURN_PROCESSOR"}), allowed_jobs=frozenset({"DPAE_RETURN_PROCESSOR_JOB"})),
    ResolveUnknownOutcome: CommandPolicy(ExecutionClass.AUTOMATION_ALLOWED, frozenset({DpaeCapability.REVIEW_RETURN}), frozenset({"DPAE_RECONCILIATION_SERVICE"}), frozenset({"DPAE_RECONCILIATION_JOB"})),
    CancelDpaeCase: CommandPolicy(ExecutionClass.HUMAN_ONLY, frozenset({DpaeCapability.PREPARE})),
    ExceptionallyCloseDpaeCase: CommandPolicy(ExecutionClass.HUMAN_ONLY, frozenset({DpaeCapability.EXCEPTIONAL_CLOSE})),
    CloseRegisteredCase: CommandPolicy(ExecutionClass.INTERNAL_ONLY, allowed_services=frozenset({"DPAE_CASE_SERVICE"}), allowed_jobs=frozenset({"DPAE_CLOSURE_JOB"})),
}


def authorize_command(command: object, actor: ActorContext) -> None:
    policy = COMMAND_POLICIES.get(type(command))
    if policy is None:
        raise DpaeDomainError("DPAE-A006", "Commande DPAE sans politique d'autorisation.")

    if policy.execution_class is ExecutionClass.HUMAN_ONLY and actor.actor_type is not ActorType.USER:
        raise DpaeDomainError("DPAE-A002", "Cette commande exige une décision humaine.", actor_type=actor.actor_type.value)
    if policy.execution_class in {ExecutionClass.TECHNICAL_ONLY, ExecutionClass.INTERNAL_ONLY} and actor.actor_type is ActorType.USER:
        raise DpaeDomainError("DPAE-A002", "Cette commande est réservée à l'exécution technique.", actor_type=actor.actor_type.value)

    if actor.actor_type is ActorType.SERVICE and actor.actor_id not in policy.allowed_services:
        raise DpaeDomainError("DPAE-A003", "Service technique non autorisé pour cette commande.", actor_id=actor.actor_id)
    if actor.actor_type is ActorType.JOB and actor.actor_id not in policy.allowed_jobs:
        raise DpaeDomainError("DPAE-A004", "Tâche automatique non autorisée pour cette commande.", actor_id=actor.actor_id)

    if actor.actor_type is ActorType.USER and not policy.required_capabilities.issubset(actor.capabilities):
        missing = sorted(c.value for c in policy.required_capabilities - actor.capabilities)
        raise DpaeDomainError("DPAE-A001", "Habilitation DPAE manquante.", missing_capabilities=missing)
