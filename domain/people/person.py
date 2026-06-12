from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from domain.common.base import Entity


@dataclass(slots=True)
class Person(Entity):
    code_internal: str = ""
    first_name: str = ""
    last_name: str = ""
    display_name: str = ""
    birth_date: Optional[date] = None
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.code_internal.strip():
            raise ValueError("code_internal is required")
        if not self.display_name.strip():
            computed = f"{self.first_name} {self.last_name}".strip()
            self.display_name = computed or self.code_internal

    @property
    def is_minor_today(self) -> Optional[bool]:
        if self.birth_date is None:
            return None
        today = date.today()
        age = today.year - self.birth_date.year
        before_birthday = (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        if before_birthday:
            age -= 1
        return age < 18
