from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.common.base import Entity


@dataclass(slots=True)
class Activity(Entity):
    code: str = ""
    label: str = ""
    category: Optional[str] = None
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.label.strip():
            raise ValueError("label is required")
