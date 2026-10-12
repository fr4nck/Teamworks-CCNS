from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Tuple

from domain.hr_connections import (
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    OrganizationKind,
)

from .employee_protection import EmployeeProtectionService, EmployeeProtectionView


@dataclass(frozen=True)
class EmployeeProtectionSummaryRow:
    """Ligne de présentation stable pour le futur onglet salarié."""

    record_id: str
    organization_kind: OrganizationKind
    organization_code: str
    organization_label: str | None
    relation_kind: EmployeeProtectionRelationKind
    status: EmployeeProtectionStatus
    effective_start: date | None
    effective_end: date | None
    administrative_deadline: date | None
    organization_configured: bool
    payroll_relevant: bool
    due: bool


@dataclass(frozen=True)
class EmployeeProtectionSummary:
    """Synthèse descriptive sans interprétation juridique automatique."""

    structure_ref: str
    employee_ref: str
    as_of: date
    rows: Tuple[EmployeeProtectionSummaryRow, ...]
    total_count: int
    effective_count: int
    pending_count: int
    due_count: int
    payroll_relevant_count: int
    orphan_configuration_count: int

    @property
    def has_attention_items(self) -> bool:
        return self.due_count > 0 or self.orphan_configuration_count > 0


class EmployeeProtectionSummaryService:
    """Construit la projection qui pourra être rendue par wxPython.

    Le service reste volontairement descriptif : il ne déduit pas qu'une couverture
    est légalement obligatoire et ne calcule aucune cotisation. Il expose seulement
    ce qui existe dans les données, ce qui est effectif à la date demandée, les
    échéances dépassées et les références d'organismes devenues orphelines.
    """

    def __init__(self, *, protection_service: EmployeeProtectionService) -> None:
        if not isinstance(protection_service, EmployeeProtectionService):
            raise TypeError("Le service de protection sociale salarié est invalide.")
        self._protection_service = protection_service

    def build(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        as_of: date,
    ) -> EmployeeProtectionSummary:
        if not isinstance(as_of, date):
            raise TypeError("La date de synthèse est invalide.")

        views = self._protection_service.list_for_employee(
            structure_ref=structure_ref,
            employee_ref=employee_ref,
        )
        rows = tuple(
            self._row(view=view, as_of=as_of)
            for view in sorted(views, key=self._sort_key)
        )
        effective_count = sum(
            1 for view in views if view.record.is_effective_on(as_of=as_of)
        )
        pending_count = sum(
            1 for view in views if view.record.status is EmployeeProtectionStatus.PENDING
        )
        due_count = sum(1 for row in rows if row.due)
        payroll_relevant_count = sum(
            1
            for view in views
            if view.payroll_relevant and view.record.is_effective_on(as_of=as_of)
        )
        orphan_count = sum(1 for view in views if not view.organization_configured)

        return EmployeeProtectionSummary(
            structure_ref=structure_ref.strip(),
            employee_ref=employee_ref.strip(),
            as_of=as_of,
            rows=rows,
            total_count=len(rows),
            effective_count=effective_count,
            pending_count=pending_count,
            due_count=due_count,
            payroll_relevant_count=payroll_relevant_count,
            orphan_configuration_count=orphan_count,
        )

    @staticmethod
    def _row(
        *,
        view: EmployeeProtectionView,
        as_of: date,
    ) -> EmployeeProtectionSummaryRow:
        period = view.record.effective_period
        return EmployeeProtectionSummaryRow(
            record_id=view.record.record_id,
            organization_kind=view.record.organization_kind,
            organization_code=view.record.organization_code,
            organization_label=view.organization_label,
            relation_kind=view.record.relation_kind,
            status=view.record.status,
            effective_start=period.starts_on,
            effective_end=period.ends_on,
            administrative_deadline=view.record.administrative_deadline,
            organization_configured=view.organization_configured,
            payroll_relevant=view.payroll_relevant,
            due=view.record.is_due_on_or_before(as_of=as_of),
        )

    @staticmethod
    def _sort_key(view: EmployeeProtectionView):
        period = view.record.effective_period
        return (
            view.record.organization_kind.value,
            view.organization_label or view.record.organization_code,
            period.starts_on is None,
            period.starts_on or date.max,
            view.record.record_id,
        )
