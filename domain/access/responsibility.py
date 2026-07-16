from __future__ import annotations

from enum import Enum


class Responsibility(str, Enum):
    """Responsabilités métier stables, indépendantes de l'interface utilisateur."""

    VIEW_OWN_PLANNING = "view_own_planning"
    CONFIRM_OWN_TIME = "confirm_own_time"
    SUBMIT_OWN_TIME = "submit_own_time"

    MANAGE_ALSH_PLANNING = "manage_alsh_planning"
    MANAGE_SPORT_PLANNING = "manage_sport_planning"
    VALIDATE_ALSH_TIME = "validate_alsh_time"
    VALIDATE_SPORT_TIME = "validate_sport_time"
    VALIDATE_ALL_TIME = "validate_all_time"

    MANAGE_CONTRACTS = "manage_contracts"
    MANAGE_EMPLOYEE_RECORDS = "manage_employee_records"
    PREPARE_PAYROLL_VARIABLES = "prepare_payroll_variables"
    EXPORT_IMPACT_EMPLOI = "export_impact_emploi"

    MANAGE_SPORT_WISH_CAMPAIGN = "manage_sport_wish_campaign"
    VIEW_SPORT_CONVENTIONS = "view_sport_conventions"
    GENERATE_SPORT_CONVENTIONS = "generate_sport_conventions"

    MANAGE_ALSH_OUTINGS = "manage_alsh_outings"
    MANAGE_ALSH_TRANSPORTS = "manage_alsh_transports"

    MANAGE_ACCOUNTS = "manage_accounts"
    MANAGE_TECHNICAL_MAINTENANCE = "manage_technical_maintenance"
