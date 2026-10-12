from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol
from uuid import uuid4

from domain.hr_connections import (
    HrAuditEvent,
    HrAuditField,
    HrCase,
    HrCaseStatus,
    HrEventKind,
    HrEventTargetKind,
)


class HrCaseWorkflowRepository(Protocol):
    """Port minimal pour appliquer une transition métier de manière atomique."""

    def get_case(self, *, structure_ref: str, case_id: str) -> HrCase | None:
        ...

    def persist_case_transition(
        self,
        *,
        structure_ref: str,
        expected_status: HrCaseStatus,
        case: HrCase,
        event: HrAuditEvent,
    ) -> HrCase:
        ...


@dataclass(frozen=True)
class HrCaseTransitionOptions:
    case: HrCase
    allowed_statuses: tuple[HrCaseStatus, ...]


@dataclass(frozen=True)
class HrCaseTransitionResult:
    case: HrCase
    event: HrAuditEvent


class HrCaseWorkflowService:
    """Frontière applicative des transitions métier des démarches RH.

    La machine d'états reste portée par ``HrCase``. Le service ajoute seulement
    l'orchestration, la création d'un événement d'audit et l'exigence d'une
    persistance atomique entre projection courante et journal append-only.
    """

    def __init__(
        self,
        *,
        repository: HrCaseWorkflowRepository,
        now_provider: Callable[[], datetime] | None = None,
        event_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self._event_id_factory = event_id_factory or (lambda: str(uuid4()))

    def available_transitions(
        self,
        *,
        structure_ref: str,
        case_id: str,
    ) -> HrCaseTransitionOptions:
        case = self._get_required_case(structure_ref=structure_ref, case_id=case_id)
        allowed = tuple(
            status for status in HrCaseStatus if case.can_transition_to(status)
        )
        return HrCaseTransitionOptions(case=case, allowed_statuses=allowed)

    def transition(
        self,
        *,
        structure_ref: str,
        case_id: str,
        status: HrCaseStatus,
        actor_ref: str | None = None,
        source: str = "teamworks-ui",
        result: str | None = None,
        comment: str | None = None,
    ) -> HrCaseTransitionResult:
        if not isinstance(status, HrCaseStatus):
            raise TypeError("Le nouveau statut métier du dossier RH est invalide.")
        source = _required_text(source, "La source de la transition RH est obligatoire.")
        actor_ref = _optional_text(actor_ref)

        current = self._get_required_case(
            structure_ref=structure_ref,
            case_id=case_id,
        )
        updated = current.transition_to(
            status,
            result=result,
            comment=comment,
        )

        occurred_at = self._now_provider()
        if not isinstance(occurred_at, datetime):
            raise TypeError("L'horodatage de la transition RH est invalide.")
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("L'horodatage de la transition RH doit contenir un fuseau horaire.")

        event_id = _required_text(
            self._event_id_factory(),
            "L'identifiant de l'événement de transition RH est obligatoire.",
        )
        event = HrAuditEvent.create(
            event_id=event_id,
            kind=HrEventKind.CASE_STATUS_CHANGED,
            target_kind=HrEventTargetKind.CASE,
            target_ref=current.case_id,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            source=source,
            fields=(
                HrAuditField.create(key="from_status", value=current.status.value),
                HrAuditField.create(key="to_status", value=updated.status.value),
            ),
        )

        persisted = self._repository.persist_case_transition(
            structure_ref=_required_text(
                structure_ref,
                "La référence de structure est obligatoire.",
            ),
            expected_status=current.status,
            case=updated,
            event=event,
        )
        return HrCaseTransitionResult(case=persisted, event=event)

    def _get_required_case(self, *, structure_ref: str, case_id: str) -> HrCase:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        case_id = _required_text(case_id, "L'identifiant du dossier RH est obligatoire.")
        case = self._repository.get_case(
            structure_ref=structure_ref,
            case_id=case_id,
        )
        if case is None:
            raise LookupError("Le dossier RH demandé n'existe pas.")
        if not isinstance(case, HrCase):
            raise TypeError("Le repository a retourné un dossier RH invalide.")
        return case


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("La référence d'acteur de la transition RH est invalide.")
    return value.strip() or None
