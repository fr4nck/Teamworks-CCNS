from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable, Protocol
from uuid import uuid4

from domain.hr_connections import (
    ExpectedDocument,
    HrAuditEvent,
    HrAuditField,
    HrCase,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrEventKind,
    HrEventTargetKind,
)

from .structure_configuration import ConnectionProfileRepository


class HrCaseCreationRepository(Protocol):
    """Port transactionnel minimal pour créer une démarche et son audit initial."""

    def get_case(self, *, structure_ref: str, case_id: str) -> HrCase | None:
        ...

    def create_case_with_event(
        self,
        *,
        structure_ref: str,
        case: HrCase,
        event: HrAuditEvent,
    ) -> HrCase:
        ...


@dataclass(frozen=True)
class HrCaseCreationRequest:
    """Données explicites nécessaires à l'ouverture d'une démarche RH.

    Le service ne déduit aucune obligation réglementaire : type, organisme,
    sujet, échéance et pièces attendues sont fournis explicitement par le cas
    d'usage appelant.
    """

    case_type_code: str
    case_type_label: str
    subject_kind: HrCaseSubjectKind
    subject_identifier: str
    organization_code: str
    opened_on: date
    due_on: date | None = None
    expected_documents: tuple[ExpectedDocument, ...] = ()
    comment: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.subject_kind, HrCaseSubjectKind):
            raise TypeError("La nature du sujet de la démarche RH est invalide.")
        if not isinstance(self.opened_on, date):
            raise TypeError("La date d'ouverture de la démarche RH est invalide.")
        if self.due_on is not None and not isinstance(self.due_on, date):
            raise TypeError("L'échéance de la démarche RH est invalide.")
        if self.due_on is not None and self.due_on < self.opened_on:
            raise ValueError("L'échéance ne peut pas précéder l'ouverture de la démarche RH.")
        if any(not isinstance(item, ExpectedDocument) for item in self.expected_documents):
            raise TypeError("Les pièces attendues de la démarche RH sont invalides.")
        _required_text(self.case_type_code, "Le code du type de démarche RH est obligatoire.")
        _required_text(self.case_type_label, "Le libellé du type de démarche RH est obligatoire.")
        _required_text(self.subject_identifier, "L'identifiant du sujet de la démarche RH est obligatoire.")
        _required_text(self.organization_code, "Le code de l'organisme est obligatoire.")
        _optional_text(self.comment)

    def to_case(self, *, case_id: str, source: str) -> HrCase:
        return HrCase.create(
            case_id=case_id,
            case_type=HrCaseType.create(
                code=self.case_type_code,
                label=self.case_type_label,
            ),
            subject=HrCaseSubject.create(
                kind=self.subject_kind,
                identifier=self.subject_identifier,
            ),
            organization_code=self.organization_code,
            opened_on=self.opened_on,
            due_on=self.due_on,
            expected_documents=self.expected_documents,
            source=source,
            comment=self.comment,
        )


@dataclass(frozen=True)
class HrCaseCreationResult:
    case: HrCase
    event: HrAuditEvent


class HrCaseCreationService:
    """Ouvre une démarche RH sans inventer de règle juridique ou de transport.

    L'organisme doit déjà être configuré pour la structure. La création produit
    systématiquement un dossier `TODO` / `NOT_APPLICABLE` via ``HrCase.create``
    et un événement append-only `CASE_CREATED`, persistés dans la même transaction.
    """

    def __init__(
        self,
        *,
        repository: HrCaseCreationRepository,
        profile_repository: ConnectionProfileRepository,
        now_provider: Callable[[], datetime] | None = None,
        case_id_factory: Callable[[], str] | None = None,
        event_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._profile_repository = profile_repository
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self._case_id_factory = case_id_factory or (lambda: str(uuid4()))
        self._event_id_factory = event_id_factory or (lambda: str(uuid4()))

    def create(
        self,
        *,
        structure_ref: str,
        request: HrCaseCreationRequest,
        actor_ref: str | None = None,
        source: str = "teamworks-ui",
    ) -> HrCaseCreationResult:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(request, HrCaseCreationRequest):
            raise TypeError("La demande de création de démarche RH est invalide.")
        source = _required_text(source, "La source de la démarche RH est obligatoire.")
        actor_ref = _optional_text(actor_ref)

        organization_code = _required_text(
            request.organization_code,
            "Le code de l'organisme est obligatoire.",
        )
        profile = self._profile_repository.get_profile(
            structure_ref=structure_ref,
            organization_code=organization_code,
        )
        if profile is None:
            raise LookupError(
                "L'organisme doit être configuré dans « Organismes & connexions RH » "
                "avant d'ouvrir cette démarche."
            )

        case_id = _required_text(
            self._case_id_factory(),
            "L'identifiant de la démarche RH est obligatoire.",
        )
        if self._repository.get_case(
            structure_ref=structure_ref,
            case_id=case_id,
        ) is not None:
            raise ValueError("L'identifiant généré pour la démarche RH existe déjà.")

        case = request.to_case(case_id=case_id, source=source)
        occurred_at = self._now_provider()
        if not isinstance(occurred_at, datetime):
            raise TypeError("L'horodatage de création de la démarche RH est invalide.")
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("L'horodatage de création de la démarche RH doit contenir un fuseau horaire.")

        event = HrAuditEvent.create(
            event_id=_required_text(
                self._event_id_factory(),
                "L'identifiant de l'événement de création RH est obligatoire.",
            ),
            kind=HrEventKind.CASE_CREATED,
            target_kind=HrEventTargetKind.CASE,
            target_ref=case.case_id,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            source=source,
            fields=(
                HrAuditField.create(key="case_type", value=case.case_type.code),
                HrAuditField.create(key="subject_kind", value=case.subject.kind.value),
                HrAuditField.create(key="organization_code", value=case.organization_code),
            ),
        )

        persisted = self._repository.create_case_with_event(
            structure_ref=structure_ref,
            case=case,
            event=event,
        )
        return HrCaseCreationResult(case=persisted, event=event)


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
        raise TypeError("Le texte facultatif de la démarche RH est invalide.")
    return value.strip() or None
