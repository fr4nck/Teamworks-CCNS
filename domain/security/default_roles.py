from domain.security.permission import Permission
from domain.security.role import Role
from domain.security.role_name import RoleName


def build_default_roles() -> list[Role]:
    full_access = {
        Permission.READ_CONTRACTS,
        Permission.EDIT_CONTRACTS,
        Permission.READ_ASSIGNMENTS,
        Permission.EDIT_ASSIGNMENTS,
        Permission.READ_CONTROLS,
        Permission.READ_SENSITIVE_HISTORY,
        Permission.EXPORT_SENSITIVE_DATA,
        Permission.MANAGE_PERMISSIONS,
    }
    return [
        Role(name=RoleName.DIRECTION, label="Direction", permissions=set(full_access)),
        Role(name=RoleName.RH, label="Ressources humaines", permissions=set(full_access)),
        Role(name=RoleName.COMPTABILITE, label="Comptabilité", permissions=set(full_access)),
        Role(
            name=RoleName.DIRECTION_ADJOINTE,
            label="Direction adjointe",
            permissions={
                Permission.READ_CONTRACTS,
                Permission.EDIT_CONTRACTS,
                Permission.READ_ASSIGNMENTS,
                Permission.EDIT_ASSIGNMENTS,
                Permission.READ_CONTROLS,
            },
        ),
        Role(
            name=RoleName.COORDINATION_PLANNING,
            label="Coordination planning",
            permissions={
                Permission.READ_ASSIGNMENTS,
                Permission.EDIT_ASSIGNMENTS,
                Permission.READ_CONTROLS,
            },
        ),
        Role(
            name=RoleName.BENEVOLE_DIRIGEANT,
            label="Bénévole dirigeant",
            permissions={
                Permission.READ_CONTROLS,
            },
        ),
    ]
