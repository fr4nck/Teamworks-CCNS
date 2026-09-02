from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol, Tuple

from domain.hr_connections import (
    ExchangeStatus,
    HrCase,
    HrCaseDocumentReceipt,
    HrCaseStatus,
    HrCaseSubjectKind,
)

from .structure_configuration import ConnectionProfileRepository


class HrCaseDashboardRepository(Protocol):
    """Port de lecture minimal du cockpit des démarches RH."""

    def list_cases(self, *, structure_ref: str) -> tuple[HrCase, ...]:
        ...


class HrCaseDashboardDocumentRepository(Protocol):
    """Port de lecture groupée des réceptions administratives de pièces."""

    def list_receipts_for_structure(
        self,
        *,
        structure_ref: str,
    ) -> tuple[HrCaseDocumentReceipt, ...]:
        ...


@dataclass(frozen=True)
class HrCaseDashboardRow:
    """Ligne descriptive du cockpit, sans interprétation juridique automatique."""

    case_id: str
    case_type_code: str
    case_type_label: str
    subject_kind: HrCaseSubjectKind
    subject_identifier: str
    organization_code: str
    organization_label: str | None
    organization_configured: bool
    opened_on: date
    due_on: date | None
    status: HrCaseStatus
    exchange_status: ExchangeStatus
    overdue: bool
    business_attention: bool
    technical_attention: bool
    configuration_attention: bool
    expected_document_count: int
    required_document_count: int
    document_tracking_available: bool
    received_document_count: int | None
    missing_expected_document_count: int | None
    required_missing_document_count: int | None
    document_attention: bool
    document_coherence_attention: bool
    unexpected_document_receipt_count: int
    result: str | None
    comment: str | None

    @property
    def required_document_receipts_complete(self) -> bool | None:
        """Complétude administrative, sans conclusion de validité ou conformité."""

        if self.required_missing_document_count is None:
            return None
        return self.required_missing_document_count == 0

    @property
    def needs_attention(self) -> bool:
        return (
            self.overdue
            or self.business_attention
            or self.technical_attention
            or self.configuration_attention
            or self.document_attention
            or self.document_coherence_attention
        )


@dataclass(frozen=True)
class HrCaseDashboard:
    """Synthèse structure des démarches administratives RH."""

    structure_ref: str
    as_of: date
    rows: Tuple[HrCaseDashboardRow, ...]
    total_count: int
    open_count: int
    overdue_count: int
    todo_count: int
    prepared_count: int
    submitted_count: int
    anomaly_count: int
    regularization_count: int
    accepted_count: int
    cancelled_count: int
    exchange_failed_count: int
    orphan_organization_count: int
    document_tracking_available: bool
    document_attention_count: int
    document_coherence_attention_count: int
    received_document_count: int | None
    required_missing_document_count: int | None

    @property
    def attention_count(self) -> int:
        return sum(1 for row in self.rows if row.needs_attention)

    @property
    def has_attention_items(self) -> bool:
        return self.attention_count > 0


class HrCaseDashboardService:
    """Construit le cockpit UI-agnostique des démarches RH d'une structure.

    Le statut métier, le statut technique et le suivi documentaire restent trois
    axes distincts. Une pièce marquée « reçue » signifie uniquement qu'une réception
    administrative a été enregistrée ; cela ne vaut ni validation, ni authenticité,
    ni conformité juridique.

    Les alertes du cockpit ne concernent que les dossiers encore ouverts. L'historique
    conserve toutefois le dernier statut technique et les références d'organismes
    supprimées, qui restent visibles dans les compteurs descriptifs dédiés.
    """

    _BUSINESS_ATTENTION = frozenset(
        {
            HrCaseStatus.ANOMALY,
            HrCaseStatus.REGULARIZATION,
        }
    )

    def __init__(
        self,
        *,
        case_repository: HrCaseDashboardRepository,
        profile_repository: ConnectionProfileRepository,
        document_repository: HrCaseDashboardDocumentRepository | None = None,
    ) -> None:
        self._case_repository = case_repository
        self._profile_repository = profile_repository
        self._document_repository = document_repository

    def build(self, *, structure_ref: str, as_of: date) -> HrCaseDashboard:
        if not isinstance(structure_ref, str) or not structure_ref.strip():
            raise ValueError("La référence de structure est obligatoire.")
        if not isinstance(as_of, date):
            raise TypeError("La date du cockpit des démarches RH est invalide.")
        structure_ref = structure_ref.strip()

        cases = self._case_repository.list_cases(structure_ref=structure_ref)
        if any(not isinstance(case, HrCase) for case in cases):
            raise TypeError("Le repository a retourné un dossier RH invalide.")

        profiles = self._profile_repository.list_profiles(structure_ref=structure_ref)
        organizations = {
            profile.organization.code: profile.organization.label
            for profile in profiles
            if profile.structure_ref == structure_ref
        }
        document_tracking_available = self._document_repository is not None
        receipts_by_case = self._load_receipts(
            structure_ref=structure_ref,
            cases=cases,
        )
        rows = tuple(
            sorted(
                (
                    self._row(
                        case=case,
                        as_of=as_of,
                        organization_label=organizations.get(case.organization_code),
                        receipts_by_code=receipts_by_case.get(case.case_id, {}),
                        document_tracking_available=document_tracking_available,
                    )
                    for case in cases
                ),
                key=self._sort_key,
            )
        )

        by_status = {
            status: sum(1 for case in cases if case.status is status)
            for status in HrCaseStatus
        }
        return HrCaseDashboard(
            structure_ref=structure_ref,
            as_of=as_of,
            rows=rows,
            total_count=len(rows),
            open_count=sum(1 for case in cases if not case.is_closed),
            overdue_count=sum(1 for row in rows if row.overdue),
            todo_count=by_status[HrCaseStatus.TODO],
            prepared_count=by_status[HrCaseStatus.PREPARED],
            submitted_count=by_status[HrCaseStatus.SUBMITTED],
            anomaly_count=by_status[HrCaseStatus.ANOMALY],
            regularization_count=by_status[HrCaseStatus.REGULARIZATION],
            accepted_count=by_status[HrCaseStatus.ACCEPTED],
            cancelled_count=by_status[HrCaseStatus.CANCELLED],
            exchange_failed_count=sum(1 for row in rows if row.technical_attention),
            orphan_organization_count=sum(
                1 for row in rows if not row.organization_configured
            ),
            document_tracking_available=document_tracking_available,
            document_attention_count=sum(1 for row in rows if row.document_attention),
            document_coherence_attention_count=sum(
                1 for row in rows if row.document_coherence_attention
            ),
            received_document_count=(
                sum(row.received_document_count or 0 for row in rows)
                if document_tracking_available
                else None
            ),
            required_missing_document_count=(
                sum(row.required_missing_document_count or 0 for row in rows)
                if document_tracking_available
                else None
            ),
        )

    def _load_receipts(
        self,
        *,
        structure_ref: str,
        cases: tuple[HrCase, ...],
    ) -> dict[str, dict[str, HrCaseDocumentReceipt]]:
        if self._document_repository is None:
            return {}
        receipts = self._document_repository.list_receipts_for_structure(
            structure_ref=structure_ref,
        )
        known_case_ids = {case.case_id for case in cases}
        by_case: dict[str, dict[str, HrCaseDocumentReceipt]] = {}
        for receipt in receipts:
            if not isinstance(receipt, HrCaseDocumentReceipt):
                raise TypeError("Le repository a retourné un suivi de pièce RH invalide.")
            if receipt.case_id not in known_case_ids:
                raise ValueError(
                    "Le repository a retourné une réception rattachée à une démarche RH inconnue."
                )
            by_code = by_case.setdefault(receipt.case_id, {})
            if receipt.document_code in by_code:
                raise ValueError(
                    "Le repository a retourné plusieurs états pour une même pièce RH."
                )
            by_code[receipt.document_code] = receipt
        return by_case

    @classmethod
    def _row(
        cls,
        *,
        case: HrCase,
        as_of: date,
        organization_label: str | None,
        receipts_by_code: dict[str, HrCaseDocumentReceipt],
        document_tracking_available: bool,
    ) -> HrCaseDashboardRow:
        open_case = not case.is_closed
        organization_configured = organization_label is not None
        expected_by_code = {document.code: document for document in case.expected_documents}
        unexpected_receipt_count = (
            sum(1 for code in receipts_by_code if code not in expected_by_code)
            if document_tracking_available
            else 0
        )
        if document_tracking_available:
            received_codes = {
                code
                for code, receipt in receipts_by_code.items()
                if code in expected_by_code and receipt.is_received
            }
            received_document_count = len(received_codes)
            missing_expected_document_count = len(expected_by_code) - len(received_codes)
            required_missing_document_count = sum(
                1
                for code, document in expected_by_code.items()
                if document.required and code not in received_codes
            )
        else:
            received_document_count = None
            missing_expected_document_count = None
            required_missing_document_count = None

        document_attention = (
            open_case
            and required_missing_document_count is not None
            and required_missing_document_count > 0
        )
        document_coherence_attention = open_case and unexpected_receipt_count > 0
        return HrCaseDashboardRow(
            case_id=case.case_id,
            case_type_code=case.case_type.code,
            case_type_label=case.case_type.label,
            subject_kind=case.subject.kind,
            subject_identifier=case.subject.identifier,
            organization_code=case.organization_code,
            organization_label=organization_label,
            organization_configured=organization_configured,
            opened_on=case.opened_on,
            due_on=case.due_on,
            status=case.status,
            exchange_status=case.exchange_status,
            overdue=case.is_overdue(as_of=as_of),
            business_attention=open_case and case.status in cls._BUSINESS_ATTENTION,
            technical_attention=(
                open_case and case.exchange_status is ExchangeStatus.FAILED
            ),
            configuration_attention=open_case and not organization_configured,
            expected_document_count=len(case.expected_documents),
            required_document_count=sum(
                1 for document in case.expected_documents if document.required
            ),
            document_tracking_available=document_tracking_available,
            received_document_count=received_document_count,
            missing_expected_document_count=missing_expected_document_count,
            required_missing_document_count=required_missing_document_count,
            document_attention=document_attention,
            document_coherence_attention=document_coherence_attention,
            unexpected_document_receipt_count=unexpected_receipt_count,
            result=case.result,
            comment=case.comment,
        )

    @staticmethod
    def _sort_key(row: HrCaseDashboardRow):
        return (
            not row.needs_attention,
            row.due_on is None,
            row.due_on or date.max,
            row.opened_on,
            row.case_id,
        )
