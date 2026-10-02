from application.security.access_service import AccessService
from domain.security.permission import Permission
from domain.security.role import Role
from domain.security.role_name import RoleName
from domain.security.user import User


def test_inactive_user_has_no_permission():
    role = Role(
        name=RoleName.COORDINATION_PLANNING,
        label="Encadrants",
        permissions={Permission.READ_ASSIGNMENTS},
    )
    user = User(
        username="inactif",
        display_name="Compte inactif",
        is_active=False,
        role_ids=[role.id],
    )

    assert AccessService().user_has_permission(
        user=user,
        roles=[role],
        permission=Permission.READ_ASSIGNMENTS,
    ) is False


def test_multiple_profiles_union_permissions():
    planning = Role(
        name=RoleName.COORDINATION_PLANNING,
        label="Planning",
        permissions={Permission.READ_ASSIGNMENTS},
    )
    contracts = Role(
        name=RoleName.DIRECTION_ADJOINTE,
        label="Contrats",
        permissions={Permission.READ_CONTRACTS},
    )
    user = User(
        username="multi",
        display_name="Multi-profils",
        role_ids=[planning.id, contracts.id],
    )
    access = AccessService()

    assert access.user_has_permission(
        user=user,
        roles=[planning, contracts],
        permission=Permission.READ_ASSIGNMENTS,
    ) is True
    assert access.user_has_permission(
        user=user,
        roles=[planning, contracts],
        permission=Permission.READ_CONTRACTS,
    ) is True
    assert access.user_has_permission(
        user=user,
        roles=[planning, contracts],
        permission=Permission.EXPORT_SENSITIVE_DATA,
    ) is False


def test_profile_label_never_grants_implicit_business_permissions():
    profile = Role(
        name=RoleName.DIRECTION,
        label="Profil technique",
        permissions={Permission.MANAGE_PERMISSIONS},
    )
    user = User(
        username="technique",
        display_name="Profil technique",
        role_ids=[profile.id],
    )
    access = AccessService()

    assert access.user_has_permission(
        user=user,
        roles=[profile],
        permission=Permission.MANAGE_PERMISSIONS,
    ) is True
    assert access.user_has_permission(
        user=user,
        roles=[profile],
        permission=Permission.READ_CONTRACTS,
    ) is False
