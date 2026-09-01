from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol, Tuple

from domain.hr_connections import (
    ExchangeStatus,
    HrCase,
    HrCaseStatus,
    HrCaseSubjectKind,
)

from .structure_configuration import ConnectionProfileRepository


class HrCaseDashboardRepository(Protocol):
    """Port de lecture minimal du cockpit des démarches RH."""

    def list_cases(self, *, structure_ref: str) -> tuple[HrCase, ...]:
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
    expected_document_count: int
    required_document_count: int
    result: str | None
    comment: str | None

    @property
    def needs_attention(self) -> bool:
        return self.overdue or self.business_attention or self.technical_attention


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

    @property
    def attention_count(self) -> int:
        return sum(1 for row in self.rows if row.needs_attention)

    @property
    def has_attention_items(self) -> bool:
        return self.attention_count > 0


class HrCaseDashboardService:
    """Construit le cockpit UI-agnostique des démarches RH d'une structure.

    Le statut métier et le statut technique restent volontairement comptés sur deux
    axes distincts. Un échange technique réussi ne signifie jamais que l'organisme
    a accepté la démarche ; inversement, une anomalie métier n'est pas transformée
    en panne technique.
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
    ) -> None:
        self._case_repository = case_repository
        self._profile_repository = profile_repository

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
        rows = tuple(
            sorted(
                (
                    self._row(
                        case=case,
                        as_of=as_of,
                        organization_label=organizations.get(case.organization_code),
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
            exchange_failed_count=sum(
                1 for case in cases if case.exchange_status is ExchangeStatus.FAILED
            ),
            orphan_organization_count=sum(
                1 for row in rows if not row.organization_configured
            ),
        )

    @classmethod
    def _row(
        cls,
        *,
        case: HrCase,
        as_of: date,
        organization_label: str | None,
    ) -> HrCaseDashboardRow:
        return HrCaseDashboardRow(
            case_id=case.case_id,
            case_type_code=case.case_type.code,
            case_type_label=case.case_type.label,
            subject_kind=case.subject.kind,
            subject_identifier=case.subject.identifier,
            organization_code=case.organization_code,
            organization_label=organization_label,
            organization_configured=organization_label is not None,
            opened_on=case.opened_on,
            due_on=case.due_on,
            status=case.status,
            exchange_status=case.exchange_status,
            overdue=case.is_overdue(as_of=as_of),
            business_attention=case.status in cls._BUSINESS_ATTENTION,
            technical_attention=case.exchange_status is ExchangeStatus.FAILED,
            expected_document_count=len(case.expected_documents),
            required_document_count=sum(
                1 for document in case.expected_documents if document.required
            ),
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
