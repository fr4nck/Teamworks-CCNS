from __future__ import annotations

from .responsibility import Responsibility as R
from .role import Role
from .workspace import Workspace


def build_direction_role() -> Role:
    return Role.create(
        code="direction",
        label="Direction",
        workspace=Workspace.DIRECTION,
        responsibilities=set(R),
    )


def build_accounting_administrator_role() -> Role:
    """Rôle de confiance assurant la continuité de service de la direction."""

    return Role.create(
        code="accounting_administrator",
        label="Comptabilité / administration",
        workspace=Workspace.ACCOUNTING,
        responsibilities={
            R.MANAGE_CONTRACTS,
            R.MANAGE_EMPLOYEE_RECORDS,
            R.PREPARE_PAYROLL_VARIABLES,
            R.EXPORT_IMPACT_EMPLOI,
            R.VALIDATE_ALSH_TIME,
            R.VALIDATE_SPORT_TIME,
            R.VALIDATE_ALL_TIME,
            R.VIEW_SPORT_CONVENTIONS,
            R.MANAGE_ACCOUNTS,
            R.MANAGE_TECHNICAL_MAINTENANCE,
        },
    )


def build_sports_coordinator_role() -> Role:
    return Role.create(
        code="sports_coordinator",
        label="Coordination sportive",
        workspace=Workspace.SPORT_COORDINATION,
        responsibilities={
            R.MANAGE_SPORT_PLANNING,
            R.VALIDATE_SPORT_TIME,
            R.MANAGE_SPORT_WISH_CAMPAIGN,
            R.VIEW_SPORT_CONVENTIONS,
        },
    )


def build_alsh_manager_role() -> Role:
    return Role.create(
        code="alsh_manager",
        label="Direction adjointe ALSH",
        workspace=Workspace.ALSH_MANAGEMENT,
        responsibilities={
            R.MANAGE_ALSH_PLANNING,
            R.VALIDATE_ALSH_TIME,
            R.MANAGE_ALSH_OUTINGS,
            R.MANAGE_ALSH_TRANSPORTS,
        },
    )


def build_employee_role() -> Role:
    return Role.create(
        code="employee",
        label="Salarié",
        workspace=Workspace.EMPLOYEE,
        responsibilities={
            R.VIEW_OWN_PLANNING,
            R.CONFIRM_OWN_TIME,
            R.SUBMIT_OWN_TIME,
        },
    )
