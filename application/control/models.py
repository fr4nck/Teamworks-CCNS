from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class DashboardCounter:
    code: str
    label: str
    value: int


@dataclass(slots=True)
class ControlRow:
    anomaly_id: str
    level: str
    code: str
    object_type: str
    object_id: str
    person_id: Optional[str]
    contract_id: Optional[str]
    assignment_id: Optional[str]
    message: str
    is_resolved: bool


@dataclass(slots=True)
class ContractControlView:
    contract_id: str
    person_id: Optional[str]
    classification_code: Optional[str]
    salary_grid_code: Optional[str]
    base_salary_amount: Optional[float]
    salary_unit: Optional[str]
    result_messages: list[str] = field(default_factory=list)
    anomaly_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AssignmentControlView:
    assignment_id: str
    person_id: Optional[str]
    activity_id: Optional[str]
    gross_duration_minutes: Optional[int]
    auto_prep_minutes: int
    main_support_type: Optional[str]
    result_messages: list[str] = field(default_factory=list)
    anomaly_codes: list[str] = field(default_factory=list)
