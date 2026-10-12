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
    HrCaseDocumentReceipt,
    HrCaseDocumentState,
    HrEventKind,
    HrEventTargetKind,
)


class HrCaseDocumentRepository(Protocol):
    """Port transactionnel du suivi administratif des pièces d'une démarche."""

    def get_case(self, *, structure_ref: str, case_id: str) -> HrCase | None:
        ...

    def get_receipt(
        self,
        *,
        structure_ref: str,
        case_id: str,
        document_code: str,
    ) -> HrCaseDocumentReceipt | None:
        ...

    def list_receipts(
        self,
        *,
        structure_ref: str,
        case_id: str,
    ) -> tuple[HrCaseDocumentReceipt, ...]:
        ...

    def persist_receipt_change(
        self,
        *,
        structure_ref: str,
        expected_state: HrCaseDocumentState | None,
        receipt: HrCaseDocumentReceipt,
        event: HrAuditEvent,
    ) -> HrCaseDocumentReceipt:
        ...


@dataclass(frozen=True)
class HrCaseDocumentChecklistRow:
    expected_document: ExpectedDocument
    receipt: HrCaseDocumentReceipt | None

    @property
    def received(self) -> bool:
        return self.receipt is not None and self.receipt.is_received

    @property
    def missing(self) -> bool:
        return not self.received

    @property
    def required_missing(self) -> bool:
        return self.expected_document.required and self.missing


@dataclass(frozen=True)
class HrCaseDocumentChecklist:
    case_id: str
    rows: tuple[HrCaseDocumentChecklistRow, ...]
    expected_count: int
    required_count: int
    received_count: int
    required_missing_count: int

    @property
    def complete_administratively(self) -> bool:
        """Indique seulement que toutes les pièces marquées obligatoires sont reçues."""

        return self.required_missing_count == 0


@dataclass(frozen=True)
class HrCaseDocumentTrackingResult:
    receipt: HrCaseDocumentReceipt
    event: HrAuditEvent


class HrCaseDocumentTrackingService:
    """Suit la réception administrative des pièces explicitement attendues.

    Le service ne conclut jamais à l'authenticité, à la validité ou à la conformité
    d'une pièce. Une pièce « reçue » signifie uniquement qu'une réception a été
    enregistrée dans Teamworks. Les changements sont journalisés sur la démarche
    afin d'apparaître dans l'historique CRH-27/28.
    """

    def __init__(
        self,
        *,
        repository: HrCaseDocumentRepository,
        now_provider: Callable[[], datetime] | None = None,
        event_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self._event_id_factory = event_id_factory or (lambda: str(uuid4()))

    def build_checklist(
        self,
        *,
        structure_ref: str,
        case_id: str,
    ) -> HrCaseDocumentChecklist:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        case_id = _required_text(
            case_id,
            "L'identifiant de la démarche RH est obligatoire.",
        )
        case = self._require_case(structure_ref=structure_ref, case_id=case_id)
        receipts = self._repository.list_receipts(
            structure_ref=structure_ref,
            case_id=case_id,
        )
        expected = {item.code: item for item in case.expected_documents}
        by_code = {}
        for receipt in receipts:
            if not isinstance(receipt, HrCaseDocumentReceipt):
                raise TypeError("Le repository a retourné un suivi de pièce RH invalide.")
            if receipt.case_id != case_id:
                raise ValueError("Le repository a retourné une pièce étrangère à la démarche RH.")
            if receipt.document_code not in expected:
                raise ValueError(
                    "Le repository a retourné une pièce qui n'est pas attendue par la démarche RH."
                )
            if receipt.document_code in by_code:
                raise ValueError("Le repository a retourné plusieurs états pour une même pièce RH.")
            by_code[receipt.document_code] = receipt

        rows = tuple(
            HrCaseDocumentChecklistRow(
                expected_document=document,
                receipt=by_code.get(document.code),
            )
            for document in sorted(
                case.expected_documents,
                key=lambda item: (not item.required, item.label.casefold(), item.code.casefold()),
            )
        )
        return HrCaseDocumentChecklist(
            case_id=case_id,
            rows=rows,
            expected_count=len(rows),
            required_count=sum(1 for row in rows if row.expected_document.required),
            received_count=sum(1 for row in rows if row.received),
            required_missing_count=sum(1 for row in rows if row.required_missing),
        )

    def record_received(
        self,
        *,
        structure_ref: str,
        case_id: str,
        document_code: str,
        received_on: date,
        artifact_ref: str | None = None,
        actor_ref: str | None = None,
        source: str = "teamworks-ui",
    ) -> HrCaseDocumentTrackingResult:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        case_id = _required_text(
            case_id,
            "L'identifiant de la démarche RH est obligatoire.",
        )
        document_code = _required_text(
            document_code,
            "Le code de la pièce RH est obligatoire.",
        )
        if not isinstance(received_on, date):
            raise TypeError("La date de réception de la pièce RH est invalide.")
        source = _required_text(source, "La source du suivi de pièce RH est obligatoire.")
        actor_ref = _optional_text(actor_ref)
        artifact_ref = _optional_text(artifact_ref)

        case = self._require_open_case(structure_ref=structure_ref, case_id=case_id)
        document = self._require_expected_document(case=case, document_code=document_code)
        current = self._repository.get_receipt(
            structure_ref=structure_ref,
            case_id=case_id,
            document_code=document_code,
        )
        if current is not None and current.state is HrCaseDocumentState.RECEIVED:
            raise ValueError("Cette pièce est déjà enregistrée comme reçue.")
        if current is not None and current.case_id != case_id:
            raise ValueError("Le repository a retourné une pièce étrangère à la démarche RH.")

        receipt = HrCaseDocumentReceipt.received(
            case_id=case_id,
            document_code=document_code,
            received_on=received_on,
            artifact_ref=artifact_ref,
            source=source,
        )
        event = self._event(
            kind=HrEventKind.DOCUMENT_ADDED,
            case_id=case_id,
            actor_ref=actor_ref,
            source=source,
            fields=(
                HrAuditField.create(key="document_code", value=document.code),
                HrAuditField.create(key="document_label", value=document.label),
                HrAuditField.create(
                    key="required",
                    value="true" if document.required else "false",
                ),
                HrAuditField.create(key="received_on", value=received_on.isoformat()),
            ),
        )
        persisted = self._repository.persist_receipt_change(
            structure_ref=structure_ref,
            expected_state=current.state if current is not None else None,
            receipt=receipt,
            event=event,
        )
        return HrCaseDocumentTrackingResult(receipt=persisted, event=event)

    def withdraw_received(
        self,
        *,
        structure_ref: str,
        case_id: str,
        document_code: str,
        withdrawn_on: date,
        actor_ref: str | None = None,
        source: str = "teamworks-ui",
    ) -> HrCaseDocumentTrackingResult:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        case_id = _required_text(
            case_id,
            "L'identifiant de la démarche RH est obligatoire.",
        )
        document_code = _required_text(
            document_code,
            "Le code de la pièce RH est obligatoire.",
        )
        if not isinstance(withdrawn_on, date):
            raise TypeError("La date de retrait de la pièce RH est invalide.")
        source = _required_text(source, "La source du suivi de pièce RH est obligatoire.")
        actor_ref = _optional_text(actor_ref)

        case = self._require_open_case(structure_ref=structure_ref, case_id=case_id)
        self._require_expected_document(case=case, document_code=document_code)
        current = self._repository.get_receipt(
            structure_ref=structure_ref,
            case_id=case_id,
            document_code=document_code,
        )
        if current is None or current.state is not HrCaseDocumentState.RECEIVED:
            raise ValueError("Cette pièce n'est pas actuellement enregistrée comme reçue.")
        receipt = current.withdraw(withdrawn_on=withdrawn_on)
        event = self._event(
            kind=HrEventKind.DOCUMENT_REMOVED,
            case_id=case_id,
            actor_ref=actor_ref,
            source=source,
            fields=(
                HrAuditField.create(key="document_code", value=document_code),
                HrAuditField.create(key="from_state", value=current.state.value),
                HrAuditField.create(key="to_state", value=receipt.state.value),
                HrAuditField.create(key="withdrawn_on", value=withdrawn_on.isoformat()),
            ),
        )
        persisted = self._repository.persist_receipt_change(
            structure_ref=structure_ref,
            expected_state=HrCaseDocumentState.RECEIVED,
            receipt=receipt,
            event=event,
        )
        return HrCaseDocumentTrackingResult(receipt=persisted, event=event)

    def _require_case(self, *, structure_ref: str, case_id: str) -> HrCase:
        case = self._repository.get_case(
            structure_ref=structure_ref,
            case_id=case_id,
        )
        if case is None:
            raise LookupError("La démarche RH demandée est introuvable.")
        if not isinstance(case, HrCase):
            raise TypeError("Le repository a retourné une démarche RH invalide.")
        return case

    def _require_open_case(self, *, structure_ref: str, case_id: str) -> HrCase:
        case = self._require_case(structure_ref=structure_ref, case_id=case_id)
        if case.is_closed:
            raise ValueError(
                "Les pièces d'une démarche RH acceptée ou annulée ne peuvent plus être modifiées."
            )
        return case

    @staticmethod
    def _require_expected_document(*, case: HrCase, document_code: str) -> ExpectedDocument:
        for document in case.expected_documents:
            if document.code == document_code:
                return document
        raise ValueError("Cette pièce n'est pas déclarée comme attendue dans la démarche RH.")

    def _event(
        self,
        *,
        kind: HrEventKind,
        case_id: str,
        actor_ref: str | None,
        source: str,
        fields: tuple[HrAuditField, ...],
    ) -> HrAuditEvent:
        occurred_at = self._now_provider()
        if not isinstance(occurred_at, datetime):
            raise TypeError("L'horodatage du suivi de pièce RH est invalide.")
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("L'horodatage du suivi de pièce RH doit contenir un fuseau horaire.")
        return HrAuditEvent.create(
            event_id=_required_text(
                self._event_id_factory(),
                "L'identifiant de l'événement de pièce RH est obligatoire.",
            ),
            kind=kind,
            target_kind=HrEventTargetKind.CASE,
            target_ref=case_id,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            source=source,
            fields=fields,
        )


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
        raise TypeError("Le texte facultatif du suivi de pièce RH est invalide.")
    return value.strip() or None
