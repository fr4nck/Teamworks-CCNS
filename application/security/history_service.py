from __future__ import annotations

from datetime import datetime
from typing import Optional

from domain.security.sensitive_event import SensitiveEvent


class HistoryService:
    def record_event(
        self,
        *,
        user_id: str,
        action_code: str,
        object_type: str,
        object_id: str,
        screen_code: Optional[str] = None,
        message: str = "",
        occurred_at: Optional[datetime] = None,
    ) -> SensitiveEvent:
        return SensitiveEvent(
            user_id=user_id,
            action_code=action_code,
            object_type=object_type,
            object_id=object_id,
            screen_code=screen_code,
            message=message,
            occurred_at=occurred_at,
        )
