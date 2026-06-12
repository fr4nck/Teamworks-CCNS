from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from domain.common.base import Entity


class AgeGroup(str, Enum):
    MINOR = "minor"
    ADULT = "adult"
    UNKNOWN = "unknown"


class ConventionFrame(str, Enum):
    CCNS = "ccns"
    STRUCTURE_DEFAULT = "structure_default"
    INTERNSHIP_AGREEMENT = "internship_agreement"
    CEE = "cee"
    OTHER = "other"


@dataclass(slots=True)
class LegalProfile(Entity):
    person_id: str = ""
    is_minor: Optional[bool] = None
    age_group: AgeGroup = AgeGroup.UNKNOWN
    work_regime: str = ""
    convention_frame: ConventionFrame = ConventionFrame.CCNS
    training_time_included: bool = False
    contract_hours_basis: Optional[float] = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.person_id.strip():
            raise ValueError("person_id is required")
        if self.is_minor is True and self.age_group == AgeGroup.ADULT:
            raise ValueError("inconsistent legal profile: minor person cannot have adult age_group")
