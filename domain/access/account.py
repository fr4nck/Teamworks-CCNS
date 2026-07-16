from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .access_grant import AccessGrant
from .role import Role
from .scope import Scope


@dataclass(frozen=True)
class Delegation:
    """Habilitation confiée temporairement à un compte."""

    role: Role
    scope: Scope
    active: bool = True

    def __post_init__(self) -> None:
        AccessGrant(role=self.role, scope=self.scope)

    @property
    def grant(self) -> AccessGrant:
        """Expose la délégation sous la forme d'une habilitation liée."""

        return AccessGrant(role=self.role, scope=self.scope)


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
    access_grants: tuple[AccessGrant, ...] = field(default_factory=tuple)
    delegations: tuple[Delegation, ...] = field(default_factory=tuple)

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
        self.access_grants = tuple(self.access_grants)
        self.delegations = tuple(self.delegations)
        if not self.access_grants:
            raise ValueError("Un compte doit porter au moins une habilitation métier.")
        _ensure_grants(self.access_grants)
        _ensure_delegations(self.delegations)

    def active_grants(self) -> tuple[AccessGrant, ...]:
        """Retourne les habilitations directes et les délégations actives."""

        return self.access_grants + tuple(
            delegation.grant for delegation in self.delegations if delegation.active
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


def _ensure_grants(grants: tuple[AccessGrant, ...]) -> None:
    if any(not isinstance(grant, AccessGrant) for grant in grants):
        raise ValueError("Les habilitations directes d'un compte doivent être des habilitations métier.")


def _ensure_delegations(delegations: tuple[Delegation, ...]) -> None:
    if any(not isinstance(delegation, Delegation) for delegation in delegations):
        raise ValueError("Les délégations d'un compte doivent être des délégations métier.")
