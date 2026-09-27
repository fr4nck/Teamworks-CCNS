"""Modèle métier minimal de la DPAE.

Aucune dépendance UI ou persistence : ce module porte les invariants purs.
DATA-001 : Teamworks reste la source de vérité RH ; le domaine DPAE ne conserve
que la référence contrat, les snapshots déclaratifs et le cycle transactionnel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DpaeCaseStatus(str, Enum):
    DRAFT = "DRAFT"
    TO_VALIDATE = "TO_VALIDATE"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    READY = "READY"
    SUBMITTING = "SUBMITTING"
    WAITING_RETURN = "WAITING_RETURN"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    REJECTED = "REJECTED"
    REGISTERED = "REGISTERED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


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
    def __init__(self, code: str, message: str, **details) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


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
    """Dossier logique DPAE.

    Il référence le contrat Teamworks mais ne duplique aucune donnée RH vivante.
    """

    id: str
    case_key: str
    contract_id: str
    status: DpaeCaseStatus = DpaeCaseStatus.DRAFT
    origin: str = "TEAMWORKS"
    created_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    version: int = 0


@dataclass(frozen=True)
class DpaeSnapshot:
    """Photographie immuable des valeurs utilisées pour une déclaration.

    ``canonical_payload`` est la représentation canonique des données métier
    déclarables après résolution/validation. Le payload fournisseur peut en être
    dérivé sans relire les données RH vivantes.
    """

    id: str
    case_id: str
    contract_id: str
    rules_version: str
    source_fingerprint: str
    canonical_payload: str
    payload_hash: str
    created_at: datetime


@dataclass
class DpaeSubmission:
    id: str
    case_id: str
    snapshot_id: str
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
            if self.correlation_status is CorrelationStatus.CONFIRMED and self.submission_id == submission_id and self.case_id == case_id:
                return "ALREADY_CONFIRMED"
            raise DpaeDomainError("DPAE_CORRELATION_STALE", "Le retour DPAE a été modifié depuis sa lecture.")
        if self.correlation_status is CorrelationStatus.CONFIRMED:
            if self.submission_id == submission_id and self.case_id == case_id:
                return "ALREADY_CONFIRMED"
            raise DpaeDomainError("CONCURRENT_CORRELATION_CONFLICT", "Le retour DPAE est déjà corrélé à une autre tentative.")
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
