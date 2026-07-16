from uuid import uuid4

import pytest

from domain.access.account import Account, Delegation
from domain.access.responsibility import Responsibility as R
from domain.access.role_catalog import (
    build_alsh_manager_role,
    build_direction_role,
    build_employee_role,
    build_sports_coordinator_role,
)
from domain.access.workspace import Workspace


def test_account_requires_business_identity_and_role():
    role = build_employee_role()

    with pytest.raises(ValueError, match="UUID"):
        Account(id="not-a-uuid", first_name="Ada", last_name="Lovelace", email="ada@example.org", roles=(role,))
    with pytest.raises(ValueError, match="prénom"):
        Account(first_name=" ", last_name="Lovelace", email="ada@example.org", roles=(role,))
    with pytest.raises(ValueError, match="nom"):
        Account(first_name="Ada", last_name=" ", email="ada@example.org", roles=(role,))
    with pytest.raises(ValueError, match="email"):
        Account(first_name="Ada", last_name="Lovelace", email="ada", roles=(role,))
    with pytest.raises(ValueError, match="rôle"):
        Account(first_name="Ada", last_name="Lovelace", email="ada@example.org")


def test_account_normalizes_identity_fields():
    account = Account(
        id=uuid4(),
        first_name=" Ada ",
        last_name=" Lovelace ",
        email=" ADA@EXAMPLE.ORG ",
        roles=(build_employee_role(),),
    )

    assert account.first_name == "Ada"
    assert account.last_name == "Lovelace"
    assert account.email == "ada@example.org"


def test_account_checks_direct_roles_responsibilities_and_workspaces():
    account = Account(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.org",
        roles=(build_employee_role(), build_sports_coordinator_role()),
    )

    assert account.can(R.SUBMIT_OWN_TIME)
    assert account.can(R.MANAGE_SPORT_PLANNING)
    assert not account.can(R.MANAGE_ACCOUNTS)
    assert account.has_workspace(Workspace.EMPLOYEE)
    assert account.has_workspace(Workspace.SPORT_COORDINATION)
    assert not account.has_workspace(Workspace.ALSH_MANAGEMENT)
    assert account.has_role("employee")
    assert not account.has_role("direction")


def test_account_checks_active_delegations():
    account = Account(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.org",
        roles=(build_employee_role(),),
        delegations=(Delegation(role=build_alsh_manager_role()), Delegation(role=build_direction_role(), active=False)),
    )

    assert account.can(R.MANAGE_ALSH_PLANNING)
    assert account.has_workspace(Workspace.ALSH_MANAGEMENT)
    assert account.has_role("alsh_manager")
    assert not account.can(R.MANAGE_ACCOUNTS)
    assert not account.has_role("direction")


def test_deactivated_account_has_no_effective_rights_until_reactivated():
    account = Account(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.org",
        roles=(build_direction_role(),),
    )

    account.deactivate()

    assert not account.active
    assert not account.can(R.MANAGE_ACCOUNTS)
    assert not account.has_workspace(Workspace.DIRECTION)
    assert not account.has_role("direction")

    account.activate()

    assert account.active
    assert account.can(R.MANAGE_ACCOUNTS)
    assert account.has_workspace(Workspace.DIRECTION)
    assert account.has_role("direction")


def test_account_rejects_duplicate_direct_or_delegated_roles():
    employee = build_employee_role()

    with pytest.raises(ValueError, match="directs"):
        Account(first_name="Ada", last_name="Lovelace", email="ada@example.org", roles=(employee, employee))
    with pytest.raises(ValueError, match="délégués"):
        Account(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.org",
            roles=(employee,),
            delegations=(Delegation(role=build_alsh_manager_role()), Delegation(role=build_alsh_manager_role())),
        )
