from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.common.base import Entity


@dataclass(slots=True)
class SensitiveEvent(Entity):
    user_id: str = ""
    action_code: str = ""
    object_type: str = ""
    object_id: str = ""
    screen_code: Optional[str] = None
    message: str = ""
    occurred_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ValueError("user_id is required")
        if not self.action_code.strip():
            raise ValueError("action_code is required")
        if not self.object_type.strip():
            raise ValueError("object_type is required")
        if not self.object_id.strip():
            raise ValueError("object_id is required")
        if not self.message.strip():
            self.message = f"{self.action_code} on {self.object_type}:{self.object_id}"
