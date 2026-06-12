from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class TimePartShortRule:
    threshold_hours_min: float
    threshold_hours_max: float
    multiplier: float
    notes: str = ""


@dataclass(slots=True)
class SeniorityRule:
    applies_from_group: int
    applies_to_group: int
    step_years: int
    percent_per_step: float
    max_percent: float
    base_reference_code: str
    notes: str = ""


@dataclass(slots=True)
class CEERule:
    rolling_period_months: int
    max_days: int
    notes: str = ""


@dataclass(slots=True)
class PreparationRule:
    population_code: str
    coefficient: float
    base_calculation: str = "gross_duration"
    rounding_mode: str = "standard"
    notes: str = ""
