from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from domain.convention.applicable_salary_minimum import (
    ApplicableSalaryMinimumResult,
    ApplicableSalaryMinimumService,
)
from domain.convention.ccns_salary_grid_data import create_ccns_salary_grid_2026_01
from domain.convention.classification import CCNSClassification
from domain.convention.salary_grid_catalog import SalaryGridCatalog
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity
from domain.convention.salary_minimum_compliance import SalaryMinimumComplianceService
from domain.convention.smic import SmicTerritory, create_smic_catalog_2026


@dataclass(frozen=True, slots=True)
class CCNSGroupChoice:
    code: str
    label: str
    periodicity: SalaryMinimumPeriodicity
    minimum_amount: Decimal


@dataclass(frozen=True, slots=True)
class CCNSContractCompliancePreview:
    group: CCNSGroupChoice
    reference_date: date
    weekly_hours: Decimal
    remuneration_amount: Decimal
    ccns_minimum_amount: Decimal
    smic_minimum_amount: Decimal
    required_minimum_amount: Decimal
    difference_amount: Decimal
    source: str
    compliant: bool


class CCNSContractCompliancePresenter:
    """Pont entre l'assistant historique et le moteur CCNS.

    Les calculs financiers du domaine utilisent leurs propres contextes Decimal
    locaux. Cette couche ne modifie donc jamais le contexte global du thread,
    afin de ne pas altérer les calculs du runtime Teamworks historique.
    """

    def __init__(self) -> None:
        salary_grid = create_ccns_salary_grid_2026_01()
        self._grid_catalog = SalaryGridCatalog((salary_grid,))
        self._service = ApplicableSalaryMinimumService(
            salary_minimum_compliance_service=SalaryMinimumComplianceService(self._grid_catalog),
            smic_catalog=create_smic_catalog_2026(),
        )

    def group_choices(self, reference_date: date) -> tuple[CCNSGroupChoice, ...]:
        if type(reference_date) is not date:
            raise TypeError("reference_date doit être une date stricte.")
        version = self._grid_catalog.version_applicable_on(reference_date)
        return tuple(
            CCNSGroupChoice(
                code=entry.classification_group.code,
                label=entry.classification_group.label,
                periodicity=entry.periodicity,
                minimum_amount=entry.amount,
            )
            for entry in version.entries
        )

    def evaluate_monthly(
        self,
        *,
        group_code: str,
        reference_date: date,
        weekly_hours: Decimal,
        remuneration_amount: Decimal,
        territory: SmicTerritory = SmicTerritory.METROPOLITAN_FRANCE,
    ) -> CCNSContractCompliancePreview:
        if type(group_code) is not str or not group_code.strip():
            raise ValueError("group_code est obligatoire.")
        choices = self.group_choices(reference_date)
        choice = next((item for item in choices if item.code == group_code.strip().upper()), None)
        if choice is None:
            raise ValueError("Groupe CCNS inconnu pour la grille applicable.")
        if choice.periodicity is SalaryMinimumPeriodicity.ANNUAL:
            raise ValueError(
                "Les groupes CCNS G7 et G8 ont un minimum annuel : le contrôle mensuel ne doit pas les convertir artificiellement."
            )

        version = self._grid_catalog.version_applicable_on(reference_date)
        classification: CCNSClassification = next(
            entry.classification_group
            for entry in version.entries
            if entry.classification_group.code == choice.code
        )
        result: ApplicableSalaryMinimumResult = self._service.evaluate(
            classification_group=classification,
            reference_date=reference_date,
            territory=territory,
            remuneration_amount=remuneration_amount,
            weekly_hours=weekly_hours,
        )
        return CCNSContractCompliancePreview(
            group=choice,
            reference_date=reference_date,
            weekly_hours=weekly_hours,
            remuneration_amount=result.remuneration_amount,
            ccns_minimum_amount=result.ccns_minimum_amount,
            smic_minimum_amount=result.smic_required_minimum_amount,
            required_minimum_amount=result.required_minimum_amount,
            difference_amount=result.difference_amount,
            source=result.source.value,
            compliant=result.is_compliant(),
        )
