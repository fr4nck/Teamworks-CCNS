from __future__ import annotations

from datetime import date
from decimal import Decimal

from domain.convention.classification import CCNSClassification
from domain.convention.salary_grid_entry import SalaryGridEntry, SalaryMinimumPeriodicity
from domain.convention.salary_grid_version import SalaryGridVersion


def create_ccns_salary_grid_2026_01() -> SalaryGridVersion:
    """Construit une nouvelle instance de la grille CCNS applicable au 1er janvier 2026."""

    groups = tuple(
        CCNSClassification(code=f"G{number}", label=f"Groupe {number}", effective_date=date(2026, 1, 1))
        for number in range(1, 9)
    )
    amounts = (
        Decimal("1848.42"),
        Decimal("1885.14"),
        Decimal("1997.87"),
        Decimal("2099.37"),
        Decimal("2333.99"),
        Decimal("2865.97"),
        Decimal("40597.94"),
        Decimal("46833.81"),
    )
    entries = tuple(
        SalaryGridEntry(
            classification_group=group,
            amount=amount,
            periodicity=(
                SalaryMinimumPeriodicity.MONTHLY
                if index < 6
                else SalaryMinimumPeriodicity.ANNUAL
            ),
        )
        for index, (group, amount) in enumerate(zip(groups, amounts))
    )
    return SalaryGridVersion(
        code="CCNS-2026-01",
        name="Minima salariaux CCNS applicables au 1er janvier 2026",
        effective_from=date(2026, 1, 1),
        effective_until=None,
        entries=entries,
        source_reference="CCNS, article 9.2.1, montants applicables au 1er janvier 2026",
    )
