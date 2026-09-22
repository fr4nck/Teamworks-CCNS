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


@dataclass(frozen=True)
class ProfileView:
    """Contenu d'un profil prêt à afficher au super-utilisateur."""

    profile_id: str
    label: str
    permissions: tuple[ProfilePermissionView, ...]


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

    def get_profile_view(self, *, role: Role) -> ProfileView:
        """Retourne exactement les données nécessaires à l'affichage d'un profil."""

        if not isinstance(role, Role):
            raise ValueError("Un profil Teamworks est attendu.")
        return ProfileView(
            profile_id=role.id,
            label=role.label,
            permissions=self.list_profile_permissions(role=role),
        )

    def set_profile_permission(
        self,
        *,
        role: Role,
        permission: Permission,
        enabled: bool,
    ) -> ProfileView:
        """Active ou désactive un droit du profil sans toucher à l'historique."""

        if not isinstance(role, Role):
            raise ValueError("Un profil Teamworks est attendu.")
        if not isinstance(permission, Permission):
            raise ValueError("Une autorisation Teamworks est attendue.")
        if not isinstance(enabled, bool):
            raise ValueError("L'état de l'autorisation doit être activé ou désactivé.")

        if enabled:
            role.permissions.add(permission)
        else:
            role.permissions.discard(permission)

        return self.get_profile_view(role=role)

    def can_access_group(self, *, scope: AccessScope | None, group_number: int) -> bool:
        if scope is None or scope.max_group_number is None:
            return True
        return group_number <= scope.max_group_number
