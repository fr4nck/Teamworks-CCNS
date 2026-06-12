from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Optional

from domain.common.base import Entity


@dataclass(slots=True)
class Timeslot(Entity):
    activity_id: str = ""
    place_id: Optional[str] = None
    code: str = ""
    label: str = ""
    weekday: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes_default: int = 0
    prep_ratio: Optional[float] = None
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.activity_id.strip():
            raise ValueError("activity_id is required")
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.label.strip():
            raise ValueError("label is required")
        if self.break_minutes_default < 0:
            raise ValueError("break_minutes_default cannot be negative")
        if self.prep_ratio is not None and self.prep_ratio < 0:
            raise ValueError("prep_ratio cannot be negative")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time")
        if self.weekday is not None and not 0 <= self.weekday <= 6:
            raise ValueError("weekday must be between 0 and 6")
