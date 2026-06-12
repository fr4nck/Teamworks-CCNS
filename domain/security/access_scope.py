from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.common.base import Entity


@dataclass(slots=True)
class AccessScope(Entity):
    user_id: str = ""
    max_group_number: Optional[int] = None
    site_code: Optional[str] = None
    domain_code: Optional[str] = None
    data_type: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ValueError("user_id is required")
        if self.max_group_number is not None and self.max_group_number < 1:
            raise ValueError("max_group_number must be >= 1")
