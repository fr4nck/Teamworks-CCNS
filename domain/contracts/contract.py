from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from domain.common.base import Entity
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization


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
