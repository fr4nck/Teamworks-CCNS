from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from domain.common.base import Entity
from domain.engine.anomaly_level import AnomalyLevel


@dataclass(slots=True)
class Anomaly(Entity):
    object_type: str = ""
    object_id: str = ""
    person_id: Optional[str] = None
    contract_id: Optional[str] = None
    assignment_id: Optional[str] = None
    calculation_result_id: Optional[str] = None
    level: AnomalyLevel = AnomalyLevel.ATTENTION
    code: str = ""
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    detection_date: Optional[date] = None
    resolved: bool = False
    resolution_date: Optional[date] = None
    resolved_by_user_id: Optional[str] = None
    resolution_comment: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.object_type.strip():
            raise ValueError("object_type is required")
        if not self.object_id.strip():
            raise ValueError("object_id is required")
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.message.strip():
            raise ValueError("message is required")
