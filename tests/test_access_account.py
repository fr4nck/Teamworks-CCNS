from uuid import uuid4

import pytest

from domain.access.access_grant import AccessGrant
from domain.access.account import Account, Delegation
from domain.access.authorization_service import AuthorizationService
from domain.access.responsibility import Responsibility as R
from domain.access.role_catalog import (
    build_alsh_manager_role,
    build_direction_role,
    build_employee_role,
    build_sports_coordinator_role,
)
from domain.access.scope import Scope, ScopeKind


def _site(name: str) -> Scope:
    return Scope.for_targets(ScopeKind.SITE, [name])


def _account(*grants: AccessGrant, delegations: tuple[Delegation, ...] = ()) -> Account:
    return Account(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.org",
        access_grants=grants,
        delegations=delegations,
    )


def test_account_requires_business_identity_and_explicit_access_grant():
    grant = AccessGrant(build_employee_role(), _site("Bais"))

    with pytest.raises(ValueError, match="UUID"):
        Account(id="not-a-uuid", first_name="Ada", last_name="Lovelace", email="ada@example.org", access_grants=(grant,))
    with pytest.raises(ValueError, match="prénom"):
        Account(first_name=" ", last_name="Lovelace", email="ada@example.org", access_grants=(grant,))
    with pytest.raises(ValueError, match="nom"):
        Account(first_name="Ada", last_name=" ", email="ada@example.org", access_grants=(grant,))
    with pytest.raises(ValueError, match="email"):
        Account(first_name="Ada", last_name="Lovelace", email="ada", access_grants=(grant,))
    with pytest.raises(ValueError, match="habilitation"):
        Account(first_name="Ada", last_name="Lovelace", email="ada@example.org")


def test_account_normalizes_identity_fields():
    account = Account(
        id=uuid4(), first_name=" Ada ", last_name=" Lovelace ", email=" ADA@EXAMPLE.ORG ",
        access_grants=(AccessGrant(build_employee_role(), _site("Bais")),),
    )

    assert account.first_name == "Ada"
    assert account.last_name == "Lovelace"
    assert account.email == "ada@example.org"


def test_role_with_responsibility_on_covered_scope_is_authorized():
    account = _account(AccessGrant(build_sports_coordinator_role(), _site("Evron")))

    assert AuthorizationService.authorize(
        account=account, responsibility=R.MANAGE_SPORT_PLANNING, scope=_site("Evron")
    )


def test_role_with_responsibility_on_insufficient_scope_is_refused():
    account = _account(AccessGrant(build_sports_coordinator_role(), _site("Bais")))

    assert not AuthorizationService.authorize(
        account=account, responsibility=R.MANAGE_SPORT_PLANNING, scope=_site("Evron")
    )


def test_distinct_grants_cannot_combine_role_and_scope():
    account = _account(
        AccessGrant(build_sports_coordinator_role(), _site("Bais")),
        AccessGrant(build_employee_role(), _site("Evron")),
    )

    assert not AuthorizationService.authorize(
        account=account, responsibility=R.MANAGE_SPORT_PLANNING, scope=_site("Evron")
    )


def test_inactive_delegation_is_refused():
    account = _account(
        AccessGrant(build_employee_role(), _site("Bais")),
        delegations=(Delegation(build_alsh_manager_role(), _site("Evron"), active=False),),
    )

    assert not AuthorizationService.authorize(
        account=account, responsibility=R.MANAGE_ALSH_PLANNING, scope=_site("Evron")
    )


def test_active_delegation_with_suitable_role_and_scope_is_authorized():
    account = _account(
        AccessGrant(build_employee_role(), _site("Bais")),
        delegations=(Delegation(build_alsh_manager_role(), _site("Evron")),),
    )

    assert AuthorizationService.authorize(
        account=account, responsibility=R.MANAGE_ALSH_PLANNING, scope=_site("Evron")
    )


def test_access_grant_requires_an_explicit_scope():
    with pytest.raises(ValueError, match="périmètre explicite"):
        AccessGrant(role=build_employee_role(), scope=None)  # type: ignore[arg-type]


def test_global_scope_only_applies_when_explicitly_granted():
    local_account = _account(AccessGrant(build_direction_role(), _site("Bais")))
    global_account = _account(AccessGrant(build_direction_role(), Scope.global_scope()))

    assert not AuthorizationService.authorize(
        account=local_account, responsibility=R.MANAGE_ACCOUNTS, scope=_site("Evron")
    )
    assert AuthorizationService.authorize(
        account=global_account, responsibility=R.MANAGE_ACCOUNTS, scope=_site("Evron")
    )


def test_inactive_account_is_refused():
    account = _account(AccessGrant(build_direction_role(), Scope.global_scope()))
    account.deactivate()

    assert not AuthorizationService.authorize(
        account=account, responsibility=R.MANAGE_ACCOUNTS, scope=Scope.global_scope()
    )
