from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TerminationDomainError(ValueError):
    """Erreur métier déterministe du domaine de sortie salarié."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class TerminationReason(str, Enum):
    UNKNOWN = "UNKNOWN"
    END_OF_FIXED_TERM = "END_OF_FIXED_TERM"
    RESIGNATION = "RESIGNATION"
    DISMISSAL = "DISMISSAL"
    MUTUAL_TERMINATION = "MUTUAL_TERMINATION"
    RETIREMENT = "RETIREMENT"
    OTHER = "OTHER"


class NoticeStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    NONE = "NONE"
    PROVIDED = "PROVIDED"


class CheckState(str, Enum):
    UNKNOWN = "UNKNOWN"
    NONE = "NONE"
    PROVIDED = "PROVIDED"


class TerminationWorkflowStatus(str, Enum):
    A_PREPARER = "A_PREPARER"
    PRET_IMPACT_EMPLOI = "PRET_IMPACT_EMPLOI"
    TRANSMIS_IMPACT_EMPLOI = "TRANSMIS_IMPACT_EMPLOI"
    EN_ATTENTE_RESULTATS = "EN_ATTENTE_RESULTATS"
    RESULTATS_RECUS = "RESULTATS_RECUS"
    DOCUMENTS_REMIS = "DOCUMENTS_REMIS"
    CLOTURE = "CLOTURE"


@dataclass(frozen=True, slots=True)
class HrInputChecks:
    hours: CheckState = CheckState.UNKNOWN
    absences: CheckState = CheckState.UNKNOWN
    leave: CheckState = CheckState.UNKNOWN
    variable_pay: CheckState = CheckState.UNKNOWN
    exceptional_items: CheckState = CheckState.UNKNOWN

    def unknown_fields(self) -> tuple[str, ...]:
        return tuple(
            name
            for name in ("hours", "absences", "leave", "variable_pay", "exceptional_items")
            if getattr(self, name) is CheckState.UNKNOWN
        )


_ALLOWED_TRANSITIONS = {
    TerminationWorkflowStatus.A_PREPARER: TerminationWorkflowStatus.PRET_IMPACT_EMPLOI,
    TerminationWorkflowStatus.PRET_IMPACT_EMPLOI: TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI,
    TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI: TerminationWorkflowStatus.EN_ATTENTE_RESULTATS,
    TerminationWorkflowStatus.EN_ATTENTE_RESULTATS: TerminationWorkflowStatus.RESULTATS_RECUS,
    TerminationWorkflowStatus.RESULTATS_RECUS: TerminationWorkflowStatus.DOCUMENTS_REMIS,
    TerminationWorkflowStatus.DOCUMENTS_REMIS: TerminationWorkflowStatus.CLOTURE,
}

_PROTECTED_AFTER_TRANSMISSION = {
    "effective_end_date",
    "termination_reason",
    "notification_date",
    "last_worked_date",
    "notice_status",
    "notice_start",
    "notice_end",
    "hr_checks",
}


@dataclass(slots=True)
class ContractTermination:
    contract_id: str
    effective_end_date: date
    known_at: datetime
    last_worked_date: date
    created_by: str
    termination_id: str = field(default_factory=lambda: str(uuid4()))
    decision_date: Optional[date] = None
    termination_reason: TerminationReason = TerminationReason.UNKNOWN
    notification_date: Optional[date] = None
    notice_status: NoticeStatus = NoticeStatus.UNKNOWN
    notice_start: Optional[date] = None
    notice_end: Optional[date] = None
    comments: str = ""
    hr_checks: HrInputChecks = field(default_factory=HrInputChecks)
    workflow_status: TerminationWorkflowStatus = TerminationWorkflowStatus.A_PREPARER
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    version: int = 0

    def __post_init__(self) -> None:
        if not self.contract_id.strip():
            raise TerminationDomainError("CONTRACT_ID_REQUIRED", "contract_id is required")
        if not self.created_by.strip():
            raise TerminationDomainError("CREATED_BY_REQUIRED", "created_by is required")
        if type(self.effective_end_date) is not date:
            raise TerminationDomainError("EFFECTIVE_END_DATE_REQUIRED", "effective_end_date must be a date")
        if type(self.last_worked_date) is not date:
            raise TerminationDomainError("LAST_WORKED_DATE_REQUIRED", "last_worked_date must be a date")
        if self.last_worked_date > self.effective_end_date:
            raise TerminationDomainError("LAST_WORKED_AFTER_END", "last_worked_date cannot be after effective_end_date")
        if not isinstance(self.known_at, datetime) or not isinstance(self.created_at, datetime):
            raise TerminationDomainError("TIMESTAMP_REQUIRED", "known_at and created_at must be datetimes")
        if self.known_at > self.created_at:
            raise TerminationDomainError("KNOWN_AFTER_RECORDED", "known_at cannot be after created_at")
        if self.version < 0:
            raise TerminationDomainError("INVALID_VERSION", "version cannot be negative")
        self._validate_notice()

    @property
    def late_discovery(self) -> bool:
        return self.known_at.date() > self.effective_end_date

    @property
    def late_recording(self) -> bool:
        return self.created_at.date() > self.known_at.date()

    def validate_against_contract_start(self, contract_start_date: date) -> None:
        if self.effective_end_date < contract_start_date:
            raise TerminationDomainError("END_BEFORE_CONTRACT_START", "effective_end_date cannot be before contract start")

    def _validate_notice(self) -> None:
        if self.notice_status is NoticeStatus.NONE and (self.notice_start is not None or self.notice_end is not None):
            raise TerminationDomainError("NOTICE_NONE_WITH_DATES", "notice dates must be absent when notice_status is NONE")
        if self.notice_status is NoticeStatus.PROVIDED:
            if self.notice_start is None or self.notice_end is None:
                raise TerminationDomainError("NOTICE_DATES_REQUIRED", "notice dates are required when notice is provided")
            if self.notice_start > self.notice_end:
                raise TerminationDomainError("NOTICE_DATES_INVALID", "notice_start cannot be after notice_end")

    def readiness_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.termination_reason is TerminationReason.UNKNOWN:
            errors.append("TERMINATION_REASON_UNKNOWN")
        if self.notice_status is NoticeStatus.UNKNOWN:
            errors.append("NOTICE_STATUS_UNKNOWN")
        errors.extend(f"HR_CHECK_{name.upper()}_UNKNOWN" for name in self.hr_checks.unknown_fields())
        return tuple(errors)

    def can_be_ready_for_impact_emploi(self) -> bool:
        return not self.readiness_errors()

    def transition_to(self, target: TerminationWorkflowStatus, *, external_checklist_complete: bool = False) -> None:
        expected = _ALLOWED_TRANSITIONS.get(self.workflow_status)
        if target is not expected:
            raise TerminationDomainError("INVALID_WORKFLOW_TRANSITION", f"cannot transition from {self.workflow_status.value} to {target.value}")
        if target is TerminationWorkflowStatus.PRET_IMPACT_EMPLOI:
            errors = self.readiness_errors()
            if errors:
                raise TerminationDomainError(errors[0], ", ".join(errors))
        if target is TerminationWorkflowStatus.CLOTURE and not external_checklist_complete:
            raise TerminationDomainError("CLOSURE_CHECKLIST_INCOMPLETE", "external closure checklist must be complete")
        self.workflow_status = target
        self._touch()

    def update_transmittable(self, **changes: object) -> None:
        if self.workflow_status is TerminationWorkflowStatus.CLOTURE:
            raise TerminationDomainError("TERMINATION_CLOSED", "closed termination cannot be modified")
        if self.workflow_status in {
            TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI,
            TerminationWorkflowStatus.EN_ATTENTE_RESULTATS,
            TerminationWorkflowStatus.RESULTATS_RECUS,
            TerminationWorkflowStatus.DOCUMENTS_REMIS,
        } and _PROTECTED_AFTER_TRANSMISSION.intersection(changes):
            raise TerminationDomainError("CORRECTION_REQUIRED", "transmitted data require an explicit correction")
        unknown = set(changes) - {
            "decision_date", "effective_end_date", "termination_reason", "notification_date",
            "last_worked_date", "notice_status", "notice_start", "notice_end", "comments", "hr_checks",
        }
        if unknown:
            raise TerminationDomainError("UNKNOWN_FIELD", f"unsupported fields: {sorted(unknown)}")
        previous = {name: getattr(self, name) for name in changes}
        try:
            for name, value in changes.items():
                setattr(self, name, value)
            if self.last_worked_date > self.effective_end_date:
                raise TerminationDomainError("LAST_WORKED_AFTER_END", "last_worked_date cannot be after effective_end_date")
            self._validate_notice()
        except Exception:
            for name, value in previous.items():
                setattr(self, name, value)
            raise
        self._touch()

    def _touch(self) -> None:
        self.updated_at = _utcnow()
        self.version += 1
