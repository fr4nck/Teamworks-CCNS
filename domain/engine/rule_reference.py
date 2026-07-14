from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from domain.common.base import Entity
from domain.engine.legal_certainty import LegalCertainty


class RuleReferenceStatus(str, Enum):
    DRAFT = "DRAFT"
    VERIFIED = "VERIFIED"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class RuleReference(Entity):
    """Référence réglementaire associable à une règle métier CCNS.

    Cette entité ne porte aucun calcul : elle documente l'origine officielle,
    la période de validité et le niveau de fiabilité d'une règle déjà codée.
    """

    code: str = ""
    title: str = ""
    official_source: str = ""
    official_url: Optional[str] = None
    organization: Optional[str] = None
    legal_reference: Optional[str] = None
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    version: str = ""
    comment: str = ""
    status: RuleReferenceStatus = RuleReferenceStatus.DRAFT
    confidence_level: str = "documented"
    legal_certainty: LegalCertainty = LegalCertainty.NON_EVALUEE
    calculation_mode: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.official_source.strip():
            raise ValueError("official_source is required")
        if self.effective_date and self.end_date and self.end_date < self.effective_date:
            raise ValueError("end_date cannot be earlier than effective_date")

    def is_valid_on(self, reference_date: date) -> bool:
        if self.effective_date and reference_date < self.effective_date:
            return False
        if self.end_date and reference_date > self.end_date:
            return False
        return True

    def explanation(self) -> str:
        source = self.official_source
        if self.legal_reference:
            source = f"{source}, {self.legal_reference}"
        if self.official_url:
            source = f"{source} ({self.official_url})"
        return f"Cette règle provient de {source}."
