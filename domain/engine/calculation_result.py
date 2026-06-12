from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from domain.common.base import Entity
from domain.engine.result_status import ResultStatus


@dataclass(slots=True)
class CalculationResult(Entity):
    object_type: str = ""
    object_id: str = ""
    person_id: Optional[str] = None
    contract_id: Optional[str] = None
    assignment_id: Optional[str] = None
    rule_id: Optional[str] = None
    rule_code: Optional[str] = None
    calculation_date: Optional[date] = None
    retained_base: Optional[str] = None
    actual_value: Optional[float] = None
    theoretical_value: Optional[float] = None
    retained_coefficient: Optional[float] = None
    gap: Optional[float] = None
    status: ResultStatus = ResultStatus.INFO
    readable_message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.object_type.strip():
            raise ValueError("object_type is required")
        if not self.object_id.strip():
            raise ValueError("object_id is required")
        if not self.readable_message.strip():
            self.readable_message = self.rule_code or "calculation_result"
