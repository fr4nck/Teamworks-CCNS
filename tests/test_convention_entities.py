from datetime import date

from domain.convention.classification import CCNSClassification
from domain.convention.salary_grid import SalaryGrid
from domain.convention.salary_grid_line import SalaryGridLine
from domain.convention.minimum_type import MinimumType


def test_classification_creation():
    item = CCNSClassification(
        code="G3",
        label="Groupe 3",
        effective_date=date(2026, 1, 1),
    )
    assert item.code == "G3"


def test_salary_grid_creation():
    grid = SalaryGrid(
        code="CCNS-2026",
        label="CCNS 2026",
        effective_date=date(2026, 1, 1),
    )
    assert grid.convention_code == "CCNS"


def test_salary_grid_line_creation():
    line = SalaryGridLine(
        salary_grid_id="grid-1",
        classification_code="G3",
        minimum_type=MinimumType.MONTHLY,
        amount=1997.87,
        unit="EUR",
    )
    assert line.amount == 1997.87
