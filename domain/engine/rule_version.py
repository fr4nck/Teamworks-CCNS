from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from domain.common.base import Entity
from domain.engine.rule_reference import RuleReference


class RuleVersionStatus(str, Enum):
    """Statut de cycle de vie d'une version de règle métier."""

    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class RuleVersionValidationLevel(str, Enum):
    """Niveau de validation documentaire ou métier d'une version."""

    DRAFT = "DRAFT"
    DOCUMENTED = "DOCUMENTED"
    LEGAL_REVIEW_REQUIRED = "LEGAL_REVIEW_REQUIRED"
    LEGAL_REVIEWED = "LEGAL_REVIEWED"
    BUSINESS_VALIDATED = "BUSINESS_VALIDATED"


SCHEDULED_APPLICABLE_VALIDATION_LEVELS = {
    RuleVersionValidationLevel.LEGAL_REVIEWED,
    RuleVersionValidationLevel.BUSINESS_VALIDATED,
}


@dataclass(slots=True)
class RuleVersion(Entity):
    """Version datée d'une règle métier reliée à sa référence réglementaire.

    Cette entité est volontairement descriptive : elle permet d'identifier la
    version applicable à une date donnée sans modifier les calculs existants.
    """

    rule_code: str = ""
    version: str = ""
    effective_date: date = date.min
    end_date: Optional[date] = None
    status: RuleVersionStatus = RuleVersionStatus.DRAFT
    comment: str = ""
    rule_reference: Optional[RuleReference] = None
    validation_level: RuleVersionValidationLevel = RuleVersionValidationLevel.DRAFT

    def __post_init__(self) -> None:
        if not self.rule_code.strip():
            raise ValueError("rule_code is required")
        if not self.version.strip():
            raise ValueError("version is required")
        if self.effective_date == date.min:
            raise ValueError("effective_date is required")
        if self.end_date and self.end_date < self.effective_date:
            raise ValueError("end_date cannot be earlier than effective_date")

    @property
    def rule_reference_code(self) -> Optional[str]:
        if self.rule_reference is None:
            return None
        return self.rule_reference.code

    def is_applicable_on(self, reference_date: date) -> bool:
        if (
            self.status == RuleVersionStatus.SCHEDULED
            and self.validation_level not in SCHEDULED_APPLICABLE_VALIDATION_LEVELS
        ):
            return False
        if self.status not in {RuleVersionStatus.ACTIVE, RuleVersionStatus.SCHEDULED}:
            return False
        if reference_date < self.effective_date:
            return False
        if self.end_date and reference_date > self.end_date:
            return False
        return True
