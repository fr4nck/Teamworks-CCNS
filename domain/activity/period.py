from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from domain.common.base import Entity


@dataclass(slots=True)
class Period(Entity):
    season_id: str = ""
    code: str = ""
    label: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    period_type: Optional[str] = None
    is_planning_active: bool = True

    def __post_init__(self) -> None:
        if not self.season_id.strip():
            raise ValueError("season_id is required")
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.label.strip():
            raise ValueError("label is required")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
