from __future__ import annotations

from typing import Iterable, Optional

from domain.convention.minimum_type import MinimumType
from domain.convention.salary_grid import SalaryGrid
from domain.convention.salary_grid_line import SalaryGridLine


def resolve_minimum_line(
    *,
    salary_grid: SalaryGrid,
    salary_grid_lines: Iterable[SalaryGridLine],
    classification_code: Optional[str],
    age: Optional[int] = None,
    execution_year: Optional[int] = None,
) -> Optional[SalaryGridLine]:
    if classification_code is None:
        return None

    candidates: list[SalaryGridLine] = []
    for line in salary_grid_lines:
        if line.salary_grid_id != salary_grid.id:
            continue
        if line.classification_code != classification_code:
            continue
        if not _matches_age(line, age):
            continue
        if not _matches_execution_year(line, execution_year):
            continue
        candidates.append(line)

    if not candidates:
        return None

    # Prefer the most specific line first:
    # 1. exact age / execution-year constrained lines
    # 2. monthly and annual minima before broader variants
    def sort_key(item: SalaryGridLine) -> tuple[int, int, int]:
        specificity = 0
        if item.age_min is not None or item.age_max is not None:
            specificity += 1
        if item.execution_year_min is not None or item.execution_year_max is not None:
            specificity += 1

        type_priority = {
            MinimumType.MONTHLY: 0,
            MinimumType.ANNUAL: 1,
            MinimumType.HOURLY: 2,
            MinimumType.DAILY: 3,
            MinimumType.PERCENT_SMIC: 4,
            MinimumType.PERCENT_BASE: 5,
        }.get(item.minimum_type, 99)

        return (-specificity, type_priority, 0)

    candidates.sort(key=sort_key)
    return candidates[0]


def compute_contract_theoretical_minimum(
    *,
    line: SalaryGridLine,
    weekly_reference_hours: Optional[float],
    work_ratio: Optional[float],
) -> Optional[float]:
    if line.amount is None:
        return None

    effective_ratio = work_ratio if work_ratio is not None else 1.0

    if line.minimum_type in (MinimumType.MONTHLY, MinimumType.ANNUAL):
        return round(line.amount * effective_ratio, 2)

    if line.minimum_type is MinimumType.HOURLY:
        if weekly_reference_hours is None:
            return None
        # Simplified monthly conversion base for V1:
        monthly_hours = weekly_reference_hours * 52 / 12
        return round(line.amount * monthly_hours, 2)

    if line.minimum_type is MinimumType.DAILY:
        return round(line.amount, 2)

    return None


def _matches_age(line: SalaryGridLine, age: Optional[int]) -> bool:
    if line.age_min is None and line.age_max is None:
        return True
    if age is None:
        return False
    if line.age_min is not None and age < line.age_min:
        return False
    if line.age_max is not None and age > line.age_max:
        return False
    return True


def _matches_execution_year(line: SalaryGridLine, execution_year: Optional[int]) -> bool:
    if line.execution_year_min is None and line.execution_year_max is None:
        return True
    if execution_year is None:
        return False
    if line.execution_year_min is not None and execution_year < line.execution_year_min:
        return False
    if line.execution_year_max is not None and execution_year > line.execution_year_max:
        return False
    return True
