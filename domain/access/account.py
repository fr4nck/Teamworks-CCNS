from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .responsibility import Responsibility
from .role import Role
from .scope import Scope
from .workspace import Workspace


@dataclass(frozen=True)
class Delegation:
    """Rôle confié temporairement à un compte, sans notion d'authentification."""

    role: Role
    active: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.role, Role):
            raise ValueError("Une délégation doit porter un rôle métier.")

    def can(self, responsibility: Responsibility) -> bool:
        return self.active and self.role.can(responsibility)


@dataclass(slots=True)
class Account:
    """Utilisateur métier Teamworks indépendant de l'authentification.

    Account porte uniquement l'identité fonctionnelle et les habilitations métier.
    Il ne connaît ni mot de passe, ni session, ni persistance, ni interface graphique.
    """

    id: UUID = field(default_factory=uuid4)
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    active: bool = True
    roles: tuple[Role, ...] = field(default_factory=tuple)
    delegations: tuple[Delegation, ...] = field(default_factory=tuple)
    scopes: tuple[Scope, ...] = field(default_factory=lambda: (Scope.global_scope(),))

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant du compte doit être un UUID.")
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        self.email = self.email.strip().lower()
        if not self.first_name:
            raise ValueError("Le prénom du compte est obligatoire.")
        if not self.last_name:
            raise ValueError("Le nom du compte est obligatoire.")
        if not _is_valid_email(self.email):
            raise ValueError("L'email du compte est invalide.")
        self.roles = tuple(self.roles)
        self.delegations = tuple(self.delegations)
        self.scopes = tuple(self.scopes)
        if not self.roles:
            raise ValueError("Un compte doit porter au moins un rôle métier.")
        _ensure_roles(self.roles)
        _ensure_delegations(self.delegations)
        _ensure_scopes(self.scopes)
        _ensure_unique_role_codes(self.roles)
        _ensure_unique_delegated_role_codes(self.delegations)

    def can(self, responsibility: Responsibility) -> bool:
        """Indique si le compte actif porte la responsabilité demandée."""

        if not self.active:
            return False
        return any(role.can(responsibility) for role in self.roles) or any(
            delegation.can(responsibility) for delegation in self.delegations
        )

    def has_workspace(self, workspace: Workspace) -> bool:
        """Indique si le compte actif accède à l'espace demandé."""

        if not self.active:
            return False
        return any(role.workspace == workspace for role in self.roles) or any(
            delegation.active and delegation.role.workspace == workspace
            for delegation in self.delegations
        )

    def has_role(self, code: str) -> bool:
        """Indique si le compte actif porte directement ou par délégation le rôle."""

        searched_code = code.strip()
        if not self.active or not searched_code:
            return False
        return any(role.code == searched_code for role in self.roles) or any(
            delegation.active and delegation.role.code == searched_code
            for delegation in self.delegations
        )

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False


def _is_valid_email(email: str) -> bool:
    local_part, separator, domain = email.partition("@")
    if separator != "@":
        return False
    if not local_part or not domain or domain.startswith(".") or domain.endswith("."):
        return False
    return "." in domain and " " not in email


def _ensure_roles(roles: tuple[Role, ...]) -> None:
    if any(not isinstance(role, Role) for role in roles):
        raise ValueError("Les rôles directs d'un compte doivent être des rôles métier.")


def _ensure_delegations(delegations: tuple[Delegation, ...]) -> None:
    if any(not isinstance(delegation, Delegation) for delegation in delegations):
        raise ValueError("Les délégations d'un compte doivent être des délégations métier.")


def _ensure_scopes(scopes: tuple[Scope, ...]) -> None:
    if not scopes:
        raise ValueError("Un compte doit porter au moins un périmètre métier.")
    if any(not isinstance(scope, Scope) for scope in scopes):
        raise ValueError("Les périmètres d'un compte doivent être des Scope métier.")


def _ensure_unique_role_codes(roles: tuple[Role, ...]) -> None:
    codes = [role.code for role in roles]
    if len(codes) != len(set(codes)):
        raise ValueError("Les rôles directs d'un compte doivent être uniques.")


def _ensure_unique_delegated_role_codes(delegations: tuple[Delegation, ...]) -> None:
    codes = [delegation.role.code for delegation in delegations]
    if len(codes) != len(set(codes)):
        raise ValueError("Les rôles délégués d'un compte doivent être uniques.")
