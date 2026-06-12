from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from domain.common.base import Entity
from domain.engine.rule_family import RuleFamily


@dataclass(slots=True)
class CalculationRule(Entity):
    code: str = ""
    label: str = ""
    family: RuleFamily = RuleFamily.CCNS_MINIMUM
    context: str = ""
    target_object: str = ""
    population_code: Optional[str] = None
    classification_code: Optional[str] = None
    contract_type_code: Optional[str] = None
    employment_regime_code: Optional[str] = None
    time_organization_code: Optional[str] = None
    convention_frame: Optional[str] = None
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: int = 100
    is_active: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.label.strip():
            raise ValueError("label is required")
        if self.priority < 0:
            raise ValueError("priority cannot be negative")
        if self.effective_date and self.end_date and self.end_date < self.effective_date:
            raise ValueError("end_date cannot be earlier than effective_date")

    def is_applicable_on(self, reference_date: date) -> bool:
        if not self.is_active:
            return False
        if self.effective_date and reference_date < self.effective_date:
            return False
        if self.end_date and reference_date > self.end_date:
            return False
        return True
