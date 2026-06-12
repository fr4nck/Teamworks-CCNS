from __future__ import annotations

from domain.security.access_scope import AccessScope
from domain.security.permission import Permission
from domain.security.role import Role
from domain.security.user import User


class AccessService:
    def user_has_permission(self, *, user: User, roles: list[Role], permission: Permission) -> bool:
        role_map = {role.id: role for role in roles}
        return any(role_map[role_id].has_permission(permission) for role_id in user.role_ids if role_id in role_map)

    def can_access_group(self, *, scope: AccessScope | None, group_number: int) -> bool:
        if scope is None or scope.max_group_number is None:
            return True
        return group_number <= scope.max_group_number
