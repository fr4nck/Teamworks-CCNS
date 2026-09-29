from enum import Enum
from typing import Final


class Permission(str, Enum):
    READ_CONTRACTS = "READ_CONTRACTS"
    EDIT_CONTRACTS = "EDIT_CONTRACTS"
    READ_ASSIGNMENTS = "READ_ASSIGNMENTS"
    EDIT_ASSIGNMENTS = "EDIT_ASSIGNMENTS"
    READ_CONTROLS = "READ_CONTROLS"
    READ_SENSITIVE_HISTORY = "READ_SENSITIVE_HISTORY"
    EXPORT_SENSITIVE_DATA = "EXPORT_SENSITIVE_DATA"
    MANAGE_PERMISSIONS = "MANAGE_PERMISSIONS"


_PERMISSION_LABELS: Final[dict[Permission, str]] = {
    Permission.READ_CONTRACTS: "Consulter les contrats",
    Permission.EDIT_CONTRACTS: "Modifier les contrats",
    Permission.READ_ASSIGNMENTS: "Consulter les affectations",
    Permission.EDIT_ASSIGNMENTS: "Modifier les affectations",
    Permission.READ_CONTROLS: "Consulter les contrôles",
    Permission.READ_SENSITIVE_HISTORY: "Consulter l'historique sensible",
    Permission.EXPORT_SENSITIVE_DATA: "Exporter des données sensibles",
    Permission.MANAGE_PERMISSIONS: "Gérer les profils et autorisations",
}


def list_permissions() -> tuple[Permission, ...]:
    """Retourne le catalogue canonique des autorisations Teamworks."""

    return tuple(Permission)


def permission_label(permission: Permission) -> str:
    """Retourne le libellé français affichable d'une autorisation."""

    if not isinstance(permission, Permission):
        raise ValueError("Une autorisation Teamworks est attendue.")
    return _PERMISSION_LABELS[permission]
