from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.common.base import Entity
from domain.convention.minimum_type import MinimumType


@dataclass(slots=True)
class SalaryGridLine(Entity):
    salary_grid_id: str = ""
    classification_code: Optional[str] = None
    minimum_type: MinimumType = MinimumType.MONTHLY
    amount: Optional[float] = None
    unit: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    execution_year_min: Optional[int] = None
    execution_year_max: Optional[int] = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.salary_grid_id.strip():
            raise ValueError("salary_grid_id is required")
        if self.amount is not None and self.amount < 0:
            raise ValueError("amount cannot be negative")
        if self.age_min is not None and self.age_max is not None and self.age_max < self.age_min:
            raise ValueError("age_max cannot be lower than age_min")
        if self.execution_year_min is not None and self.execution_year_max is not None and self.execution_year_max < self.execution_year_min:
            raise ValueError("execution_year_max cannot be lower than execution_year_min")
