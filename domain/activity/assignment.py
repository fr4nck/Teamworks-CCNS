from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from domain.common.base import Entity
from domain.activity.time_nature import TimeNature
from domain.activity.assignment_status import AssignmentStatus


@dataclass(slots=True)
class Assignment(Entity):
    person_id: str = ""
    period_id: str = ""
    activity_id: str = ""
    place_id: Optional[str] = None
    timeslot_id: Optional[str] = None
    assignment_date: Optional[date] = None
    title: str = ""
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    break_minutes: int = 0
    gross_duration_minutes: Optional[int] = None
    retained_duration_minutes: Optional[int] = None
    time_nature: TimeNature = TimeNature.FACE_PUBLIC
    prep_ratio: Optional[float] = None
    auto_prep_minutes: int = 0
    status: AssignmentStatus = AssignmentStatus.DRAFT
    comment: str = ""
    contract_id: Optional[str] = None
    stage_pfmp_id: Optional[str] = None
    service_civique_id: Optional[str] = None
    volunteer_engagement_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.person_id.strip():
            raise ValueError("person_id is required")
        if not self.period_id.strip():
            raise ValueError("period_id is required")
        if not self.activity_id.strip():
            raise ValueError("activity_id is required")
        if self.break_minutes < 0:
            raise ValueError("break_minutes cannot be negative")
        if self.auto_prep_minutes < 0:
            raise ValueError("auto_prep_minutes cannot be negative")
        if self.prep_ratio is not None and self.prep_ratio < 0:
            raise ValueError("prep_ratio cannot be negative")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        support_ids = [
            self.contract_id,
            self.stage_pfmp_id,
            self.service_civique_id,
            self.volunteer_engagement_id,
        ]
        filled_supports = [value for value in support_ids if value]
        if len(filled_supports) > 1:
            raise ValueError("only one main support can be linked to an assignment")

    def compute_gross_duration_minutes(self) -> Optional[int]:
        if self.starts_at is None or self.ends_at is None:
            return self.gross_duration_minutes
        minutes = int((self.ends_at - self.starts_at).total_seconds() // 60)
        minutes -= self.break_minutes
        self.gross_duration_minutes = max(minutes, 0)
        return self.gross_duration_minutes

    def compute_auto_prep_minutes(self) -> int:
        source = self.gross_duration_minutes
        if source is None:
            source = self.compute_gross_duration_minutes()
        if source is None or self.prep_ratio is None:
            self.auto_prep_minutes = 0
            return 0
        self.auto_prep_minutes = round(source * self.prep_ratio)
        return self.auto_prep_minutes
