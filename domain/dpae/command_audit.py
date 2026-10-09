"""Contrat d'audit des commandes DPAE, sans duplication de données RH."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .authorization import ActorContext, ActorType


class CommandDecision(str, Enum):
    APPLIED = "APPLIED"
    ALREADY_APPLIED = "ALREADY_APPLIED"
    DENIED = "DENIED"


@dataclass(frozen=True)
class CommandInitiator:
    actor_type: ActorType
    actor_id: str


@dataclass(frozen=True)
class DpaeCommandAuditRecord:
    id: str
    command_id: str
    command_type: str
    command_hash: str
    actor_type: ActorType
    actor_id: str
    execution_id: str | None
    initiated_by: CommandInitiator | None
    case_id: str | None
    submission_id: str | None
    requested_at: datetime
    decided_at: datetime
    decision: CommandDecision
    decision_code: str | None = None
    case_version_seen: int | None = None
    submission_version_seen: int | None = None
    reason_code: str | None = None
    correlation_id: str | None = None

    @classmethod
    def from_decision(
        cls, *, id: str, command_id: str, command: object, command_hash: str,
        actor: ActorContext, requested_at: datetime, decided_at: datetime,
        decision: CommandDecision, initiated_by: CommandInitiator | None = None,
        case_id: str | None = None, submission_id: str | None = None,
        decision_code: str | None = None, case_version_seen: int | None = None,
        submission_version_seen: int | None = None, reason_code: str | None = None,
        correlation_id: str | None = None,
    ) -> "DpaeCommandAuditRecord":
        return cls(
            id=id, command_id=command_id, command_type=type(command).__name__,
            command_hash=command_hash, actor_type=actor.actor_type,
            actor_id=actor.actor_id, execution_id=actor.execution_id,
            initiated_by=initiated_by, case_id=case_id,
            submission_id=submission_id, requested_at=requested_at,
            decided_at=decided_at, decision=decision,
            decision_code=decision_code, case_version_seen=case_version_seen,
            submission_version_seen=submission_version_seen,
            reason_code=reason_code, correlation_id=correlation_id,
        )
