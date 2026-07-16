import pytest

from domain.access.responsibility import Responsibility as R
from domain.access.role import Role
from domain.access.role_catalog import (
    build_accounting_administrator_role,
    build_alsh_manager_role,
    build_direction_role,
    build_employee_role,
    build_sports_coordinator_role,
)
from domain.access.workspace import Workspace


def test_role_requires_code_and_label():
    with pytest.raises(ValueError):
        Role.create(code=" ", label="Test", workspace=Workspace.DIRECTION)
    with pytest.raises(ValueError):
        Role.create(code="test", label=" ", workspace=Workspace.DIRECTION)


def test_employee_can_confirm_and_submit_only_own_time():
    role = build_employee_role()

    assert role.can(R.VIEW_OWN_PLANNING)
    assert role.can(R.CONFIRM_OWN_TIME)
    assert role.can(R.SUBMIT_OWN_TIME)
    assert not role.can(R.VALIDATE_ALL_TIME)


def test_sports_coordinator_can_prepare_season_but_not_generate_convention():
    role = build_sports_coordinator_role()

    assert role.can(R.MANAGE_SPORT_WISH_CAMPAIGN)
    assert role.can(R.MANAGE_SPORT_PLANNING)
    assert role.can(R.VIEW_SPORT_CONVENTIONS)
    assert not role.can(R.GENERATE_SPORT_CONVENTIONS)
    assert not role.can(R.PREPARE_PAYROLL_VARIABLES)


def test_alsh_manager_handles_planning_outings_and_transports_without_financial_rights():
    role = build_alsh_manager_role()

    assert role.can(R.MANAGE_ALSH_PLANNING)
    assert role.can(R.MANAGE_ALSH_OUTINGS)
    assert role.can(R.MANAGE_ALSH_TRANSPORTS)
    assert not role.can(R.PREPARE_PAYROLL_VARIABLES)


def test_direction_can_generate_sport_conventions_and_validate_all_time():
    role = build_direction_role()

    assert role.can(R.GENERATE_SPORT_CONVENTIONS)
    assert role.can(R.VALIDATE_ALL_TIME)


def test_accounting_administrator_ensures_operational_continuity():
    role = build_accounting_administrator_role()

    assert role.can(R.MANAGE_CONTRACTS)
    assert role.can(R.PREPARE_PAYROLL_VARIABLES)
    assert role.can(R.EXPORT_IMPACT_EMPLOI)
    assert role.can(R.VALIDATE_ALL_TIME)
    assert role.can(R.MANAGE_ACCOUNTS)
