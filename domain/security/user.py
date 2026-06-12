from __future__ import annotations

from dataclasses import dataclass, field

from domain.common.base import Entity


@dataclass(slots=True)
class User(Entity):
    username: str = ""
    display_name: str = ""
    is_active: bool = True
    role_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValueError("username is required")
        if not self.display_name.strip():
            self.display_name = self.username
