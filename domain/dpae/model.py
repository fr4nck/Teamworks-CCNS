"""Modèle métier minimal de la DPAE.

Aucune dépendance UI ou persistence : ce module porte les invariants purs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DpaeCaseStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    REGISTERED = "REGISTERED"
    CLOSED = "CLOSED"


class DpaeSubmissionState(str, Enum):
    PREPARED = "PREPARED"
    SENDING = "SENDING"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    TECHNICALLY_ACCEPTED = "TECHNICALLY_ACCEPTED"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"


class DpaeReturnType(str, Enum):
    AEE = "AEE"
    ARE = "ARE"
    BAN = "BAN"
    CCO = "CCO"
    BIS = "BIS"
    RETURN_41 = "RETURN_41"


class CorrelationStatus(str, Enum):
    UNMATCHED = "UNMATCHED"
    AUTO_MATCHED = "AUTO_MATCHED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    CORRELATION_CONFLICT = "CORRELATION_CONFLICT"
    CONFIRMED = "CONFIRMED"
    UNRESOLVED = "UNRESOLVED"
    INVALIDATED = "INVALIDATED"


class DpaeDomainError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_ALLOWED_TRANSITIONS = {
    DpaeSubmissionState.PREPARED: {DpaeSubmissionState.SENDING},
    DpaeSubmissionState.SENDING: {
        DpaeSubmissionState.TECHNICALLY_ACCEPTED,
        DpaeSubmissionState.REJECTED,
        DpaeSubmissionState.OUTCOME_UNKNOWN,
    },
    DpaeSubmissionState.OUTCOME_UNKNOWN: {
        DpaeSubmissionState.TECHNICALLY_ACCEPTED,
        DpaeSubmissionState.REJECTED,
    },
    DpaeSubmissionState.TECHNICALLY_ACCEPTED: {DpaeSubmissionState.PROCESSED},
    DpaeSubmissionState.REJECTED: set(),
    DpaeSubmissionState.PROCESSED: set(),
}


@dataclass
class DpaeCase:
    id: str
    case_key: str
    employee_id: str
    contract_id: str
    establishment_id: str
    expected_hiring_at: datetime
    status: DpaeCaseStatus = DpaeCaseStatus.DRAFT
    origin: str = "TEAMWORKS"
    created_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None


@dataclass
class DpaeSubmission:
    id: str
    case_id: str
    attempt_no: int
    idempotency_key: str
    payload_hash: str
    state: DpaeSubmissionState = DpaeSubmissionState.PREPARED
    external_flux_id: Optional[str] = None
    version: int = 0

    def transition_to(self, new_state: DpaeSubmissionState) -> None:
        if new_state == self.state:
            return
        if new_state not in _ALLOWED_TRANSITIONS[self.state]:
            raise DpaeDomainError(
                "DPAE-I-TRANSITION",
                f"Transition DPAE interdite: {self.state.value} -> {new_state.value}",
            )
        self.state = new_state
        self.version += 1


@dataclass
class DpaeReturn:
    id: str
    provider: str
    return_type: DpaeReturnType
    raw_hash: str
    received_at: datetime
    external_return_id: Optional[str] = None
    external_flux_id: Optional[str] = None
    employer_siret: Optional[str] = None
    submission_id: Optional[str] = None
    case_id: Optional[str] = None
    correlation_status: CorrelationStatus = CorrelationStatus.UNMATCHED
    version: int = 0

    @property
    def may_have_business_effect(self) -> bool:
        return self.correlation_status is CorrelationStatus.CONFIRMED

    def confirm_correlation(self, submission_id: str, case_id: str, expected_version: int) -> str:
        if expected_version != self.version:
            if (
                self.correlation_status is CorrelationStatus.CONFIRMED
                and self.submission_id == submission_id
                and self.case_id == case_id
            ):
                return "ALREADY_CONFIRMED"
            raise DpaeDomainError(
                "DPAE_CORRELATION_STALE",
                "Le retour DPAE a été modifié depuis sa lecture.",
            )
        if self.correlation_status is CorrelationStatus.CONFIRMED:
            if self.submission_id == submission_id and self.case_id == case_id:
                return "ALREADY_CONFIRMED"
            raise DpaeDomainError(
                "CONCURRENT_CORRELATION_CONFLICT",
                "Le retour DPAE est déjà corrélé à une autre tentative.",
            )
        self.submission_id = submission_id
        self.case_id = case_id
        self.correlation_status = CorrelationStatus.CONFIRMED
        self.version += 1
        return "CONFIRMED"


@dataclass(frozen=True)
class DpaeCorrelationDecision:
    id: str
    return_id: str
    action: str
    actor_id: str
    decided_at: datetime
    candidate_submission_id: Optional[str] = None
    reason_code: Optional[str] = None
    supersedes_id: Optional[str] = None


@dataclass(frozen=True)
class DpaeReturnEffect:
    return_id: str
    effect_type: str
    created_at: datetime
