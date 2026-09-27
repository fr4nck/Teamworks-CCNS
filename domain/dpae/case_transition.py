"""Machine à états V1 des dossiers DPAE."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet

from .model import DpaeCase, DpaeCaseStatus, DpaeDomainError


class DpaeCaseEvent(str, Enum):
    CONTRACT_READY = "CONTRACT_READY"
    CANCEL_CASE = "CANCEL_CASE"
    VALIDATION_OK = "VALIDATION_OK"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    CORRECTION_COMPLETED = "CORRECTION_COMPLETED"
    RETURN_RESOLVED_POSITIVE = "RETURN_RESOLVED_POSITIVE"
    RETURN_RESOLVED_REJECTED = "RETURN_RESOLVED_REJECTED"
    CONFIRM_SUBMISSION = "CONFIRM_SUBMISSION"
    SOURCE_DATA_CHANGED = "SOURCE_DATA_CHANGED"
    TRANSPORT_ACCEPTED = "TRANSPORT_ACCEPTED"
    DEFINITIVE_REJECTION = "DEFINITIVE_REJECTION"
    DELIVERY_UNCERTAIN = "DELIVERY_UNCERTAIN"
    POSITIVE_RETURN = "POSITIVE_RETURN"
    REJECTION_RETURN = "REJECTION_RETURN"
    BIS_OR_ACTION_REQUIRED = "BIS_OR_ACTION_REQUIRED"
    RETURN_TIMEOUT = "RETURN_TIMEOUT"
    RECONCILED_POSITIVE = "RECONCILED_POSITIVE"
    RECONCILED_REJECTED = "RECONCILED_REJECTED"
    RECONCILED_PENDING = "RECONCILED_PENDING"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    CORRECTION_STARTED = "CORRECTION_STARTED"
    CLOSE_WITHOUT_RESUBMISSION = "CLOSE_WITHOUT_RESUBMISSION"
    ARCHIVE_EVIDENCE = "ARCHIVE_EVIDENCE"


class DpaeCapability(str, Enum):
    PREPARE = "DPAE_PREPARE"
    SUBMIT = "DPAE_SUBMIT"
    CORRECT = "DPAE_CORRECT"
    REVIEW_RETURN = "DPAE_REVIEW_RETURN"
    EXCEPTIONAL_CLOSE = "DPAE_EXCEPTIONAL_CLOSE"


@dataclass(frozen=True)
class TransitionContext:
    actor_id: str
    capabilities: FrozenSet[DpaeCapability] = frozenset()
    expected_version: int = 0
    contract_complete: bool = True
    validation_blocking_errors: int = 0
    validation_fresh: bool = True
    source_data_changed: bool = False
    correction_applied: bool = False
    submission_started: bool = False
    uncertain_submission_exists: bool = False
    return_confirmed: bool = False
    positive_evidence: bool = False
    definitive_rejection: bool = False
    transport_acceptance_proven: bool = False
    pending_transmission_proven: bool = False
    timeout_reached: bool = False
    evidence_archived: bool = False
    reason_code: str | None = None


@dataclass(frozen=True)
class TransitionRule:
    target: DpaeCaseStatus
    capability: DpaeCapability | None = None
    guards: tuple[str, ...] = field(default_factory=tuple)


RULES = {
    (DpaeCaseStatus.DRAFT, DpaeCaseEvent.CONTRACT_READY): TransitionRule(DpaeCaseStatus.TO_VALIDATE, DpaeCapability.PREPARE, ("contract_complete",)),
    (DpaeCaseStatus.DRAFT, DpaeCaseEvent.CANCEL_CASE): TransitionRule(DpaeCaseStatus.CANCELLED, DpaeCapability.PREPARE, ("not_submission_started", "reason")),
    (DpaeCaseStatus.TO_VALIDATE, DpaeCaseEvent.VALIDATION_OK): TransitionRule(DpaeCaseStatus.READY, None, ("no_blocking_errors",)),
    (DpaeCaseStatus.TO_VALIDATE, DpaeCaseEvent.VALIDATION_FAILED): TransitionRule(DpaeCaseStatus.ACTION_REQUIRED, None, ("has_blocking_errors",)),
    (DpaeCaseStatus.ACTION_REQUIRED, DpaeCaseEvent.CORRECTION_COMPLETED): TransitionRule(DpaeCaseStatus.TO_VALIDATE, DpaeCapability.CORRECT, ("correction_applied",)),
    (DpaeCaseStatus.ACTION_REQUIRED, DpaeCaseEvent.RETURN_RESOLVED_POSITIVE): TransitionRule(DpaeCaseStatus.REGISTERED, DpaeCapability.REVIEW_RETURN, ("confirmed_positive",)),
    (DpaeCaseStatus.ACTION_REQUIRED, DpaeCaseEvent.RETURN_RESOLVED_REJECTED): TransitionRule(DpaeCaseStatus.REJECTED, DpaeCapability.REVIEW_RETURN, ("confirmed_rejection",)),
    (DpaeCaseStatus.ACTION_REQUIRED, DpaeCaseEvent.CANCEL_CASE): TransitionRule(DpaeCaseStatus.CANCELLED, DpaeCapability.EXCEPTIONAL_CLOSE, ("reason", "not_positive")),
    (DpaeCaseStatus.READY, DpaeCaseEvent.CONFIRM_SUBMISSION): TransitionRule(DpaeCaseStatus.SUBMITTING, DpaeCapability.SUBMIT, ("validation_fresh", "no_source_change", "no_uncertain_submission")),
    (DpaeCaseStatus.READY, DpaeCaseEvent.SOURCE_DATA_CHANGED): TransitionRule(DpaeCaseStatus.TO_VALIDATE, None, ("source_changed",)),
    (DpaeCaseStatus.READY, DpaeCaseEvent.CANCEL_CASE): TransitionRule(DpaeCaseStatus.CANCELLED, DpaeCapability.PREPARE, ("not_submission_started", "reason")),
    (DpaeCaseStatus.SUBMITTING, DpaeCaseEvent.TRANSPORT_ACCEPTED): TransitionRule(DpaeCaseStatus.WAITING_RETURN, None, ("transport_proven",)),
    (DpaeCaseStatus.SUBMITTING, DpaeCaseEvent.DEFINITIVE_REJECTION): TransitionRule(DpaeCaseStatus.REJECTED, None, ("definitive_rejection",)),
    (DpaeCaseStatus.SUBMITTING, DpaeCaseEvent.DELIVERY_UNCERTAIN): TransitionRule(DpaeCaseStatus.OUTCOME_UNKNOWN),
    (DpaeCaseStatus.WAITING_RETURN, DpaeCaseEvent.POSITIVE_RETURN): TransitionRule(DpaeCaseStatus.REGISTERED, None, ("confirmed_positive",)),
    (DpaeCaseStatus.WAITING_RETURN, DpaeCaseEvent.REJECTION_RETURN): TransitionRule(DpaeCaseStatus.REJECTED, None, ("confirmed_rejection",)),
    (DpaeCaseStatus.WAITING_RETURN, DpaeCaseEvent.BIS_OR_ACTION_REQUIRED): TransitionRule(DpaeCaseStatus.ACTION_REQUIRED, None, ("return_confirmed",)),
    (DpaeCaseStatus.WAITING_RETURN, DpaeCaseEvent.RETURN_TIMEOUT): TransitionRule(DpaeCaseStatus.ACTION_REQUIRED, None, ("timeout_reached",)),
    (DpaeCaseStatus.OUTCOME_UNKNOWN, DpaeCaseEvent.RECONCILED_POSITIVE): TransitionRule(DpaeCaseStatus.REGISTERED, None, ("confirmed_positive",)),
    (DpaeCaseStatus.OUTCOME_UNKNOWN, DpaeCaseEvent.RECONCILED_REJECTED): TransitionRule(DpaeCaseStatus.REJECTED, None, ("confirmed_rejection",)),
    (DpaeCaseStatus.OUTCOME_UNKNOWN, DpaeCaseEvent.RECONCILED_PENDING): TransitionRule(DpaeCaseStatus.WAITING_RETURN, None, ("pending_proven",)),
    (DpaeCaseStatus.OUTCOME_UNKNOWN, DpaeCaseEvent.MANUAL_REVIEW_REQUIRED): TransitionRule(DpaeCaseStatus.ACTION_REQUIRED),
    (DpaeCaseStatus.REJECTED, DpaeCaseEvent.CORRECTION_STARTED): TransitionRule(DpaeCaseStatus.ACTION_REQUIRED, DpaeCapability.CORRECT),
    (DpaeCaseStatus.REJECTED, DpaeCaseEvent.CLOSE_WITHOUT_RESUBMISSION): TransitionRule(DpaeCaseStatus.CANCELLED, DpaeCapability.EXCEPTIONAL_CLOSE, ("reason",)),
    (DpaeCaseStatus.REGISTERED, DpaeCaseEvent.ARCHIVE_EVIDENCE): TransitionRule(DpaeCaseStatus.CLOSED, None, ("evidence_archived",)),
}


_GUARD_ERRORS = {
    "contract_complete": ("DPAE-P001", "Le contrat ne permet pas encore de préparer la DPAE."),
    "not_submission_started": ("DPAE-P002", "Une transmission DPAE a déjà commencé."),
    "no_blocking_errors": ("DPAE-P003", "La validation contient des erreurs bloquantes."),
    "has_blocking_errors": ("DPAE-I002", "VALIDATION_FAILED exige au moins une erreur bloquante."),
    "correction_applied": ("DPAE-P004", "Aucune correction effective n'a été enregistrée."),
    "return_confirmed": ("DPAE-P005", "Le retour DPAE n'est pas corrélé avec certitude."),
    "confirmed_positive": ("DPAE-P006", "Une preuve positive confirmée est requise."),
    "confirmed_rejection": ("DPAE-P007", "Un rejet définitif confirmé est requis."),
    "not_positive": ("DPAE-P008", "Un dossier enregistré ne peut pas être annulé."),
    "validation_fresh": ("DPAE-P009", "La validation DPAE est obsolète."),
    "no_source_change": ("DPAE-P009", "Les données sources ont changé depuis la validation."),
    "no_uncertain_submission": ("DPAE-I006", "Une transmission précédente a un résultat inconnu."),
    "source_changed": ("DPAE-I005", "SOURCE_DATA_CHANGED exige une modification des données déclaratives."),
    "transport_proven": ("DPAE-P010", "L'acceptation technique du transport n'est pas prouvée."),
    "definitive_rejection": ("DPAE-P011", "Le rejet n'est pas définitif."),
    "timeout_reached": ("DPAE-P013", "Le délai d'attente du retour n'est pas expiré."),
    "pending_proven": ("DPAE-P014", "L'existence de la transmission en attente n'est pas prouvée."),
    "reason": ("DPAE-P015", "Une justification structurée est obligatoire."),
    "evidence_archived": ("DPAE-P016", "La preuve DPAE n'est pas archivée."),
}


def _guard_ok(name: str, ctx: TransitionContext) -> bool:
    return {
        "contract_complete": ctx.contract_complete,
        "not_submission_started": not ctx.submission_started,
        "no_blocking_errors": ctx.validation_blocking_errors == 0,
        "has_blocking_errors": ctx.validation_blocking_errors > 0,
        "correction_applied": ctx.correction_applied,
        "return_confirmed": ctx.return_confirmed,
        "confirmed_positive": ctx.return_confirmed and ctx.positive_evidence,
        "confirmed_rejection": ctx.return_confirmed and ctx.definitive_rejection,
        "not_positive": not ctx.positive_evidence,
        "validation_fresh": ctx.validation_fresh,
        "no_source_change": not ctx.source_data_changed,
        "no_uncertain_submission": not ctx.uncertain_submission_exists,
        "source_changed": ctx.source_data_changed,
        "transport_proven": ctx.transport_acceptance_proven,
        "definitive_rejection": ctx.definitive_rejection,
        "timeout_reached": ctx.timeout_reached,
        "pending_proven": ctx.pending_transmission_proven,
        "reason": bool(ctx.reason_code),
        "evidence_archived": ctx.evidence_archived,
    }[name]


class DpaeCaseTransitionService:
    def transition(self, case: DpaeCase, event: DpaeCaseEvent, ctx: TransitionContext) -> DpaeCaseStatus:
        if case.version != ctx.expected_version:
            raise DpaeDomainError("DPAE-I010", "Version du dossier DPAE obsolète.", expected_version=ctx.expected_version, current_version=case.version)
        rule = RULES.get((case.status, event))
        if rule is None:
            raise DpaeDomainError("DPAE-T001", f"Événement {event.value} interdit depuis {case.status.value}.")
        if rule.capability is not None and rule.capability not in ctx.capabilities:
            raise DpaeDomainError("DPAE-A001", f"Capacité requise: {rule.capability.value}.")
        for guard in rule.guards:
            if not _guard_ok(guard, ctx):
                code, message = _GUARD_ERRORS[guard]
                raise DpaeDomainError(code, message, event=event.value, current_state=case.status.value)
        case.status = rule.target
        case.version += 1
        return rule.target
