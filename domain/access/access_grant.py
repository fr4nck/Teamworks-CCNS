from __future__ import annotations

from dataclasses import dataclass

from .responsibility import Responsibility
from .role import Role
from .scope import Scope


@dataclass(frozen=True)
class AccessGrant:
    """Association explicite d'un rôle métier et de son périmètre d'exercice."""

    role: Role
    scope: Scope

    def __post_init__(self) -> None:
        if not isinstance(self.role, Role):
            raise ValueError("Une habilitation doit porter un rôle métier.")
        if not isinstance(self.scope, Scope):
            raise ValueError("Une habilitation doit porter un périmètre explicite.")

    def authorizes(self, responsibility: Responsibility, scope: Scope) -> bool:
        """Indique si cette habilitation seule couvre la demande d'accès."""

        if not isinstance(responsibility, Responsibility):
            raise ValueError("L'autorisation attend une responsabilité métier.")
        if not isinstance(scope, Scope):
            raise ValueError("L'autorisation attend un périmètre métier.")
        return self.role.can(responsibility) and self.scope.contains(scope)
