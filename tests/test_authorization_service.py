from domain.access.account import Account
from domain.access.authorization_service import AuthorizationService
from domain.access.responsibility import Responsibility as R
from domain.access.role import Role
from domain.access.scope import Scope, ScopeKind
from domain.access.workspace import Workspace


def _account(*, roles, scopes, active=True) -> Account:
    return Account(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.org",
        active=active,
        roles=roles,
        scopes=scopes,
    )


def _role(code: str, *responsibilities: R) -> Role:
    return Role.create(
        code=code,
        label=code.replace("_", " ").title(),
        workspace=Workspace.DIRECTION,
        responsibilities=responsibilities,
    )


def test_authorize_grants_a_role_responsibility_on_a_covered_scope():
    account = _account(
        roles=(_role("planner", R.MANAGE_ALSH_PLANNING),),
        scopes=(Scope.for_targets(ScopeKind.SITE, ["Bais", "Evron"]),),
    )

    assert AuthorizationService().authorize(
        account,
        R.MANAGE_ALSH_PLANNING,
        Scope.for_targets(ScopeKind.SITE, ["Bais"]),
    )


def test_authorize_refuses_an_absent_responsibility():
    account = _account(
        roles=(_role("employee", R.VIEW_OWN_PLANNING),),
        scopes=(Scope.global_scope(),),
    )

    assert not AuthorizationService().authorize(
        account,
        R.MANAGE_ALSH_PLANNING,
        Scope.global_scope(),
    )


def test_authorize_refuses_an_insufficient_scope():
    account = _account(
        roles=(_role("planner", R.MANAGE_ALSH_PLANNING),),
        scopes=(Scope.for_targets(ScopeKind.SITE, ["Bais"]),),
    )

    assert not AuthorizationService().authorize(
        account,
        R.MANAGE_ALSH_PLANNING,
        Scope.for_targets(ScopeKind.SITE, ["Evron"]),
    )


def test_authorize_refuses_an_inactive_account():
    account = _account(
        active=False,
        roles=(_role("planner", R.MANAGE_ALSH_PLANNING),),
        scopes=(Scope.global_scope(),),
    )

    assert not AuthorizationService().authorize(
        account,
        R.MANAGE_ALSH_PLANNING,
        Scope.global_scope(),
    )


def test_authorize_uses_all_account_roles():
    account = _account(
        roles=(
            _role("employee", R.VIEW_OWN_PLANNING),
            _role("planner", R.MANAGE_ALSH_PLANNING),
        ),
        scopes=(Scope.global_scope(),),
    )

    assert AuthorizationService().authorize(
        account,
        R.MANAGE_ALSH_PLANNING,
        Scope.global_scope(),
    )


def test_authorize_combines_all_account_scopes():
    account = _account(
        roles=(_role("planner", R.MANAGE_ALSH_PLANNING),),
        scopes=(
            Scope.for_targets(ScopeKind.SITE, ["Bais"]),
            Scope.for_targets(ScopeKind.SITE, ["Evron"]),
        ),
    )

    assert AuthorizationService().authorize(
        account,
        R.MANAGE_ALSH_PLANNING,
        Scope.for_targets(ScopeKind.SITE, ["Bais", "Evron"]),
    )
