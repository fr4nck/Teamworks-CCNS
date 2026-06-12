from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from domain.common.base import Entity


@dataclass(slots=True)
class IndividualCounter(Entity):
    person_id: str = ""
    contract_id: Optional[str] = None
    season_id: Optional[str] = None
    period_id: Optional[str] = None
    counter_code: str = ""
    value: float = 0.0
    unit: str = ""
    calculation_date: Optional[date] = None
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.person_id.strip():
            raise ValueError("person_id is required")
        if not self.counter_code.strip():
            raise ValueError("counter_code is required")
        if not self.unit.strip():
            raise ValueError("unit is required")
