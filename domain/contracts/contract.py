from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from domain.common.base import Entity
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.convention.classification import CCNSClassification
from domain.convention.smic import SmicTerritory


@dataclass(slots=True)
class Contract(Entity):
    person_id: str = ""
    contract_type: ContractType = ContractType.CDI
    employment_regime: EmploymentRegime = EmploymentRegime.CCNS_STANDARD
    time_organization: TimeOrganization = TimeOrganization.WEEKLY_CONSTANT
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    annual_target_volume_hours: Optional[float] = None
    monthly_smoothed_volume_hours: Optional[float] = None
    weekly_reference_hours: Optional[float] = None
    work_ratio: Optional[float] = None
    ccns_classification_code: Optional[str] = None
    salary_grid_code: Optional[str] = None
    base_salary_amount: Optional[float] = None
    salary_unit: Optional[str] = None
    contract_status: str = "draft"
    notes: str = ""
    ccns_classification: Optional[CCNSClassification] = None
    monthly_gross_salary_amount: Optional[Decimal] = None
    weekly_hours: Optional[Decimal] = None
    smic_territory: Optional[SmicTerritory] = None

    def __post_init__(self) -> None:
        if not self.person_id.strip():
            raise ValueError("person_id is required")
        if self.contract_type in {
            ContractType.CDD,
            ContractType.CEE,
            ContractType.APPRENTICESHIP,
            ContractType.INTERNSHIP,
            ContractType.CIVIC_SERVICE,
        } and self.end_date is None:
            raise ValueError("end_date is required for fixed-term contracts")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        if self.weekly_reference_hours is not None and self.weekly_reference_hours < 0:
            raise ValueError("weekly_reference_hours cannot be negative")
        if self.base_salary_amount is not None and self.base_salary_amount < 0:
            raise ValueError("base_salary_amount cannot be negative")
        if self.ccns_classification is not None and type(self.ccns_classification) is not CCNSClassification:
            raise TypeError("ccns_classification doit être un CCNSClassification.")
        if self.monthly_gross_salary_amount is not None and type(self.monthly_gross_salary_amount) is not Decimal:
            raise TypeError("monthly_gross_salary_amount doit être un Decimal strict.")
        if self.weekly_hours is not None and type(self.weekly_hours) is not Decimal:
            raise TypeError("weekly_hours doit être un Decimal strict.")
        if self.smic_territory is not None and type(self.smic_territory) is not SmicTerritory:
            raise TypeError("smic_territory doit être un SmicTerritory.")
        if self.monthly_gross_salary_amount is not None and self.monthly_gross_salary_amount < Decimal("0.00"):
            raise ValueError("monthly_gross_salary_amount ne peut pas être négatif.")
        if self.weekly_hours is not None and self.weekly_hours <= Decimal("0.00"):
            raise ValueError("weekly_hours doit être strictement positif.")

    @property
    def is_open_ended(self) -> bool:
        return self.end_date is None

    @property
    def is_ccns(self) -> bool:
        return self.employment_regime in {
            EmploymentRegime.CCNS_STANDARD,
            EmploymentRegime.CCNS_MODULATION,
            EmploymentRegime.CCNS_CDII,
            EmploymentRegime.APPRENTICE,
            EmploymentRegime.CEE,
        }

    def is_applicable_on(self, reference_date: date) -> bool:
        if type(reference_date) is not date:
            raise TypeError("reference_date doit être une date stricte.")
        if self.start_date is not None and reference_date < self.start_date:
            return False
        if self.end_date is not None and reference_date > self.end_date:
            return False
        return True
