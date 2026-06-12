from __future__ import annotations

from dataclasses import dataclass, field

from domain.common.base import Entity
from domain.security.permission import Permission
from domain.security.role_name import RoleName


@dataclass(slots=True)
class Role(Entity):
    name: RoleName = RoleName.COORDINATION_PLANNING
    label: str = ""
    permissions: set[Permission] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.label.strip():
            self.label = self.name.value.replace("_", " ").title()

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions
