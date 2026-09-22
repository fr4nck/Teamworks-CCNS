from __future__ import annotations

from dataclasses import dataclass

from domain.security.access_scope import AccessScope
from domain.security.permission import Permission, list_permissions, permission_label
from domain.security.role import Role
from domain.security.user import User


@dataclass(frozen=True)
class ProfilePermissionView:
    """Autorisation prête à afficher dans l'édition d'un profil."""

    code: str
    label: str
    enabled: bool


class AccessService:
    def user_has_permission(self, *, user: User, roles: list[Role], permission: Permission) -> bool:
        role_map = {role.id: role for role in roles}
        return any(
            role_map[role_id].has_permission(permission)
            for role_id in user.role_ids
            if role_id in role_map
        )

    def list_profile_permissions(self, *, role: Role) -> tuple[ProfilePermissionView, ...]:
        """Retourne toutes les autorisations avec leur état pour un profil."""

        if not isinstance(role, Role):
            raise ValueError("Un profil Teamworks est attendu.")
        return tuple(
            ProfilePermissionView(
                code=permission.value,
                label=permission_label(permission),
                enabled=role.has_permission(permission),
            )
            for permission in list_permissions()
        )

    def can_access_group(self, *, scope: AccessScope | None, group_number: int) -> bool:
        if scope is None or scope.max_group_number is None:
            return True
        return group_number <= scope.max_group_number
