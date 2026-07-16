from __future__ import annotations

from enum import Enum


class Workspace(str, Enum):
    """Espace de travail principal présenté à l'utilisateur."""

    DIRECTION = "direction"
    ACCOUNTING = "accounting"
    SPORT_COORDINATION = "sport_coordination"
    ALSH_MANAGEMENT = "alsh_management"
    EMPLOYEE = "employee"
    GOVERNANCE = "governance"
