"""Résultats externes et clôture du dossier de sortie — SORTIE-004.

Un document décrit un artefact reçu ; il ne reconstruit ni paie, ni DSN, ni
FCTU. Son contenu reste opaque au domaine. L'empreinte sert à l'intégrité et à
la déduplication, pas à interpréter le document.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import Enum
from typing import Iterable, Optional
from uuid import uuid4

from domain.employment.termination import (
    ContractTermination,
    TerminationDomainError,
    TerminationWorkflowStatus,
)


class TerminationDocumentType(str, Enum):
    FINAL_PAYSLIP = "FINAL_PAYSLIP"
    AER = "AER"
    WORK_CERTIFICATE = "WORK_CERTIFICATE"
    FINAL_SETTLEMENT_RECEIPT = "FINAL_SETTLEMENT_RECEIPT"
    OTHER = "OTHER"


class TerminationDocumentSource(str, Enum):
    IMPACT_EMPLOI = "IMPACT_EMPLOI"
    FRANCE_TRAVAIL = "FRANCE_TRAVAIL"
    EMPLOYER = "EMPLOYER"
    OTHER = "OTHER"


def _enum(enum_type, value, code):
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        raise TerminationDomainError(code, "invalid %s: %r" % (enum_type.__name__, value)) from None


def _aware(value, name):
    if not isinstance(value, datetime):
        raise TerminationDomainError("TIMESTAMP_REQUIRED", "%s must be a datetime" % name)
    if value.tzinfo is None or value.utcoffset() is None:
        raise TerminationDomainError("TIMESTAMP_TIMEZONE_REQUIRED", "%s must be timezone-aware" % name)


@dataclass(frozen=True, slots=True)
class TerminationDocument:
    termination_id: str
    document_type: TerminationDocumentType
    source: TerminationDocumentSource
    document_date: date
    received_at: datetime
    file_reference: str
    sha256: str
    received_by: str
    document_id: str = ""
    external_reference: Optional[str] = None
    archived_at: Optional[datetime] = None
    archived_by: Optional[str] = None
    delivered_at: Optional[datetime] = None
    delivered_by: Optional[str] = None

    def __post_init__(self):
        if not self.document_id:
            object.__setattr__(self, "document_id", str(uuid4()))
        if not isinstance(self.termination_id, str) or not self.termination_id.strip():
            raise TerminationDomainError("TERMINATION_ID_REQUIRED", "termination_id is required")
        object.__setattr__(self, "document_type", _enum(TerminationDocumentType, self.document_type, "INVALID_DOCUMENT_TYPE"))
        object.__setattr__(self, "source", _enum(TerminationDocumentSource, self.source, "INVALID_DOCUMENT_SOURCE"))
        if type(self.document_date) is not date:
            raise TerminationDomainError("DOCUMENT_DATE_REQUIRED", "document_date must be a date")
        _aware(self.received_at, "received_at")
        if not isinstance(self.file_reference, str) or not self.file_reference.strip():
            raise TerminationDomainError("FILE_REFERENCE_REQUIRED", "file_reference is required")
        if not isinstance(self.sha256, str) or len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise TerminationDomainError("INVALID_DOCUMENT_SHA256", "sha256 must be 64 lowercase hexadecimal characters")
        if not isinstance(self.received_by, str) or not self.received_by.strip():
            raise TerminationDomainError("RECEIVED_BY_REQUIRED", "received_by is required")
        for instant, actor, prefix in (
            (self.archived_at, self.archived_by, "ARCHIVED"),
            (self.delivered_at, self.delivered_by, "DELIVERED"),
        ):
            if (instant is None) != (actor is None):
                raise TerminationDomainError(prefix + "_PAIR_REQUIRED", prefix.lower() + " timestamp and actor must be set together")
            if instant is not None:
                _aware(instant, prefix.lower() + "_at")
                if instant < self.received_at:
                    raise TerminationDomainError(prefix + "_BEFORE_RECEIVED", prefix.lower() + "_at cannot precede received_at")
        if self.delivered_at is not None and self.document_type is TerminationDocumentType.AER and self.archived_at is None:
            raise TerminationDomainError("AER_MUST_BE_ARCHIVED_BEFORE_DELIVERY", "AER must be archived before delivery")

    @property
    def is_archived(self):
        return self.archived_at is not None

    @property
    def is_delivered(self):
        return self.delivered_at is not None

    def mark_archived(self, *, at: datetime, by: str):
        if self.archived_at is not None:
            raise TerminationDomainError("DOCUMENT_ALREADY_ARCHIVED", "document is already archived")
        return replace(self, archived_at=at, archived_by=by)

    def mark_delivered(self, *, at: datetime, by: str):
        if self.delivered_at is not None:
            raise TerminationDomainError("DOCUMENT_ALREADY_DELIVERED", "document is already delivered")
        return replace(self, delivered_at=at, delivered_by=by)


@dataclass(frozen=True, slots=True)
class TerminationClosureChecklist:
    final_payslip_received: bool
    aer_received: bool
    work_certificate_received: bool
    final_settlement_receipt_received: bool
    aer_archived: bool
    work_certificate_delivered: bool
    final_settlement_receipt_delivered: bool

    @property
    def complete(self):
        return all((
            self.final_payslip_received,
            self.aer_received,
            self.work_certificate_received,
            self.final_settlement_receipt_received,
            self.aer_archived,
            self.work_certificate_delivered,
            self.final_settlement_receipt_delivered,
        ))

    @classmethod
    def from_documents(cls, documents: Iterable[TerminationDocument]):
        docs = tuple(documents)
        def of_type(kind):
            return tuple(d for d in docs if d.document_type is kind)
        payslips = of_type(TerminationDocumentType.FINAL_PAYSLIP)
        aers = of_type(TerminationDocumentType.AER)
        certificates = of_type(TerminationDocumentType.WORK_CERTIFICATE)
        settlements = of_type(TerminationDocumentType.FINAL_SETTLEMENT_RECEIPT)
        return cls(
            final_payslip_received=bool(payslips),
            aer_received=bool(aers),
            work_certificate_received=bool(certificates),
            final_settlement_receipt_received=bool(settlements),
            aer_archived=any(d.is_archived for d in aers),
            work_certificate_delivered=any(d.is_delivered for d in certificates),
            final_settlement_receipt_delivered=any(d.is_delivered for d in settlements),
        )


def advance_results_workflow(termination: ContractTermination, documents: Iterable[TerminationDocument]):
    """Avance une étape post-transmission uniquement sur des faits documentaires."""
    docs = tuple(documents)
    if any(d.termination_id != termination.termination_id for d in docs):
        raise TerminationDomainError("DOCUMENT_TERMINATION_MISMATCH", "all documents must belong to this termination")
    checklist = TerminationClosureChecklist.from_documents(docs)
    status = termination.workflow_status
    if status is TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI:
        termination.transition_to(TerminationWorkflowStatus.EN_ATTENTE_RESULTATS)
    elif status is TerminationWorkflowStatus.EN_ATTENTE_RESULTATS:
        if not (checklist.final_payslip_received and checklist.aer_received):
            raise TerminationDomainError("RESULTS_INCOMPLETE", "final payslip and AER are required")
        termination.transition_to(TerminationWorkflowStatus.RESULTATS_RECUS)
    elif status is TerminationWorkflowStatus.RESULTATS_RECUS:
        if not (checklist.work_certificate_delivered and checklist.final_settlement_receipt_delivered):
            raise TerminationDomainError("DOCUMENTS_NOT_DELIVERED", "required employee documents have not been delivered")
        termination.transition_to(TerminationWorkflowStatus.DOCUMENTS_REMIS)
    elif status is TerminationWorkflowStatus.DOCUMENTS_REMIS:
        if termination.has_open_correction:
            raise TerminationDomainError("CORRECTION_OPEN", "an open correction prevents closure")
        if not checklist.complete:
            raise TerminationDomainError("CLOSURE_CHECKLIST_INCOMPLETE", "documentary closure checklist is incomplete")
        # Pont temporaire vers l'API SORTIE-001 ; la décision est désormais
        # calculée exclusivement depuis les faits documentaires SORTIE-004.
        termination.transition_to(TerminationWorkflowStatus.CLOTURE, external_checklist_complete=True)
    else:
        raise TerminationDomainError("RESULT_WORKFLOW_NOT_APPLICABLE", "document workflow is not applicable from this status")
    return checklist
