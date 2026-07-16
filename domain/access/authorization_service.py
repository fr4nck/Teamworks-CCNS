from __future__ import annotations

from .account import Account
from .responsibility import Responsibility
from .scope import Scope


class AuthorizationService:
    """Point d'entrée unique pour l'autorisation métier liée à un périmètre."""

    @staticmethod
    def authorize(*, account: Account, responsibility: Responsibility, scope: Scope) -> bool:
        if not isinstance(account, Account):
            raise ValueError("L'autorisation attend un compte métier.")
        if not isinstance(responsibility, Responsibility):
            raise ValueError("L'autorisation attend une responsabilité métier.")
        if not isinstance(scope, Scope):
            raise ValueError("L'autorisation attend un périmètre métier.")
        if not account.active:
            return False
        return any(grant.authorizes(responsibility, scope) for grant in account.active_grants())
