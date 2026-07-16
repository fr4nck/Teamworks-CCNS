from __future__ import annotations

from .account import Account
from .responsibility import Responsibility
from .scope import Scope


class AuthorizationService:
    """Point d'entrée métier pour les décisions d'autorisation.

    Une autorisation exige un compte actif, au moins un rôle (direct ou délégué
    et actif) portant la responsabilité demandée, ainsi qu'un ensemble de
    périmètres couvrant entièrement le périmètre demandé.
    """

    def authorize(
        self,
        account: Account,
        responsibility: Responsibility,
        scope: Scope,
    ) -> bool:
        """Indique si ``account`` peut exercer ``responsibility`` sur ``scope``."""

        _ensure_authorization_arguments(account, responsibility, scope)
        if not account.active:
            return False
        if not any(role.can(responsibility) for role in _active_roles(account)):
            return False
        return Scope.combine(account.scopes).contains(scope)


def _active_roles(account: Account):
    yield from account.roles
    yield from (
        delegation.role for delegation in account.delegations if delegation.active
    )


def _ensure_authorization_arguments(
    account: Account,
    responsibility: Responsibility,
    scope: Scope,
) -> None:
    if not isinstance(account, Account):
        raise ValueError("L'autorisation attend un Account.")
    if not isinstance(responsibility, Responsibility):
        raise ValueError("L'autorisation attend une Responsibility.")
    if not isinstance(scope, Scope):
        raise ValueError("L'autorisation attend un Scope.")
