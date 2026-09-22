from application.security.access_service import AccessService
from domain.security.default_roles import build_default_roles
from domain.security.permission import Permission, list_permissions, permission_label
from domain.security.role import Role
from domain.security.role_name import RoleName


def test_permission_catalog_is_complete_and_displayable():
    permissions = list_permissions()

    assert permissions == tuple(Permission)
    assert len(permissions) == len(set(permissions))
    assert all(permission_label(permission).strip() for permission in permissions)


def test_profile_view_exposes_every_permission_with_enabled_state():
    role = Role(
        name=RoleName.COORDINATION_PLANNING,
        label="Encadrants",
        permissions={Permission.READ_ASSIGNMENTS, Permission.EDIT_ASSIGNMENTS},
    )

    profile = AccessService().get_profile_view(role=role)

    assert profile.profile_id == role.id
    assert profile.label == "Encadrants"
    assert len(profile.permissions) == len(Permission)

    states = {item.code: item.enabled for item in profile.permissions}
    assert states[Permission.READ_ASSIGNMENTS.value] is True
    assert states[Permission.EDIT_ASSIGNMENTS.value] is True
    assert states[Permission.READ_CONTRACTS.value] is False


def test_profile_view_uses_central_french_labels():
    role = Role(name=RoleName.COORDINATION_PLANNING, label="Test")
    profile = AccessService().get_profile_view(role=role)

    labels = {item.code: item.label for item in profile.permissions}
    assert labels[Permission.READ_CONTRACTS.value] == "Consulter les contrats"
    assert labels[Permission.MANAGE_PERMISSIONS.value] == "Gérer les profils et autorisations"


def test_full_access_default_profiles_follow_central_catalog():
    roles = build_default_roles()
    direction = next(role for role in roles if role.name == RoleName.DIRECTION)

    assert direction.permissions == set(Permission)
