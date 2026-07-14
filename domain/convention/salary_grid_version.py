from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from domain.common.base import Entity
from domain.engine.rule_reference import RuleReference
from domain.engine.rule_version import RuleVersion, RuleVersionValidationLevel


class SalaryGridVersionStatus(str, Enum):
    """Statut de cycle de vie d'une version de grille salariale."""

    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


SALARY_GRID_SCHEDULED_APPLICABLE_VALIDATION_LEVELS = {
    RuleVersionValidationLevel.LEGAL_REVIEWED,
    RuleVersionValidationLevel.BUSINESS_VALIDATED,
}


@dataclass(slots=True)
class SalaryGridVersion(Entity):
    """Version descriptive d'une grille salariale CCNS.

    Cette entité prépare l'historisation et le raccord réglementaire des
    grilles sans intervenir dans le choix des lignes ni dans les calculs de
    rémunération existants.
    """

    grid_code: str = ""
    version: str = ""
    effective_date: date = date.min
    end_date: Optional[date] = None
    status: SalaryGridVersionStatus = SalaryGridVersionStatus.DRAFT
    comment: str = ""
    rule_version: Optional[RuleVersion] = None
    rule_reference: Optional[RuleReference] = None
    validation_level: RuleVersionValidationLevel = RuleVersionValidationLevel.DRAFT
    validation_date: Optional[date] = None

    def __post_init__(self) -> None:
        if not self.grid_code.strip():
            raise ValueError("grid_code is required")
        if not self.version.strip():
            raise ValueError("version is required")
        if self.effective_date == date.min:
            raise ValueError("effective_date is required")
        if self.end_date and self.end_date < self.effective_date:
            raise ValueError("end_date cannot be earlier than effective_date")

    @property
    def rule_version_code(self) -> Optional[str]:
        if self.rule_version is None:
            return None
        return self.rule_version.rule_code

    @property
    def rule_reference_code(self) -> Optional[str]:
        if self.rule_reference is not None:
            return self.rule_reference.code
        if self.rule_version is not None:
            return self.rule_version.rule_reference_code
        return None

    def is_applicable_on(self, reference_date: date) -> bool:
        if (
            self.status == SalaryGridVersionStatus.SCHEDULED
            and self.validation_level not in SALARY_GRID_SCHEDULED_APPLICABLE_VALIDATION_LEVELS
        ):
            return False
        if self.status not in {SalaryGridVersionStatus.ACTIVE, SalaryGridVersionStatus.SCHEDULED}:
            return False
        if reference_date < self.effective_date:
            return False
        if self.end_date and reference_date > self.end_date:
            return False
        return True
