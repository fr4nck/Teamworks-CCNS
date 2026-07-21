from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class PartTimeMinimumIncreaseRule:
    minimum_weekly_hours: Optional[Decimal]
    maximum_weekly_hours: Decimal
    increase_rate: Decimal
    maximum_inclusive: bool
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if self.minimum_weekly_hours is not None and type(self.minimum_weekly_hours) is not Decimal:
            raise TypeError("minimum_weekly_hours doit être un Decimal strict ou None.")
        if type(self.maximum_weekly_hours) is not Decimal:
            raise TypeError("maximum_weekly_hours doit être un Decimal strict.")
        if type(self.increase_rate) is not Decimal:
            raise TypeError("increase_rate doit être un Decimal strict.")
        if type(self.maximum_inclusive) is not bool:
            raise TypeError("maximum_inclusive doit être un booléen strict.")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")
        if self.maximum_weekly_hours <= Decimal("0"):
            raise ValueError("maximum_weekly_hours doit être strictement positif.")
        if self.minimum_weekly_hours is not None:
            if self.minimum_weekly_hours < Decimal("0"):
                raise ValueError("minimum_weekly_hours ne peut pas être négatif.")
            if self.minimum_weekly_hours >= self.maximum_weekly_hours:
                raise ValueError("minimum_weekly_hours doit être inférieur à maximum_weekly_hours.")
        if self.increase_rate < Decimal("0"):
            raise ValueError("increase_rate ne peut pas être négatif.")

    def applies_to(self, weekly_hours: Decimal) -> bool:
        if type(weekly_hours) is not Decimal:
            raise TypeError("weekly_hours doit être un Decimal strict.")
        above_minimum = self.minimum_weekly_hours is None or weekly_hours > self.minimum_weekly_hours
        below_maximum = (
            weekly_hours <= self.maximum_weekly_hours
            if self.maximum_inclusive
            else weekly_hours < self.maximum_weekly_hours
        )
        return above_minimum and below_maximum


def create_ccns_part_time_minimum_increase_rules() -> tuple[PartTimeMinimumIncreaseRule, ...]:
    return (
        PartTimeMinimumIncreaseRule(
            minimum_weekly_hours=None,
            maximum_weekly_hours=Decimal("10.00"),
            increase_rate=Decimal("0.05"),
            maximum_inclusive=True,
        ),
        PartTimeMinimumIncreaseRule(
            minimum_weekly_hours=Decimal("10.00"),
            maximum_weekly_hours=Decimal("24.00"),
            increase_rate=Decimal("0.02"),
            maximum_inclusive=False,
        ),
    )


def increase_rate_for_weekly_hours(weekly_hours: Decimal) -> Decimal:
    if type(weekly_hours) is not Decimal:
        raise TypeError("weekly_hours doit être un Decimal strict.")
    if weekly_hours <= Decimal("0"):
        raise ValueError("weekly_hours doit être strictement supérieur à zéro.")
    for rule in create_ccns_part_time_minimum_increase_rules():
        if rule.applies_to(weekly_hours):
            return rule.increase_rate
    return Decimal("0.00")
