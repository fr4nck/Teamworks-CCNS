from datetime import date
from decimal import Decimal

import application.control.contract_compensation_preflight as module
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity


class Choice:
    def __init__(self, code, amount):
        self.code = code
        self.minimum_amount = Decimal(amount)
        self.periodicity = SalaryMinimumPeriodicity.ANNUAL


class Presenter:
    def group_choices(self, reference_date):
        return (Choice("G7", "40597.94"), Choice("G8", "46833.81"))


def setup_module():
    module.CCNSContractCompliancePresenter = Presenter


def test_g7_full_time_full_year_minimum():
    result = module.validate_ccns_annual_compensation(
        group_code="G7",
        reference_date=date(2026, 1, 1),
        weekly_hours=Decimal("35.00"),
        gross_annual_salary=Decimal("40597.94"),
    )
    assert result.compliant is True
    assert result.required_minimum == Decimal("40597.94")


def test_g8_part_time_is_prorated():
    result = module.validate_ccns_annual_compensation(
        group_code="G8",
        reference_date=date(2026, 1, 1),
        weekly_hours=Decimal("17.50"),
        gross_annual_salary=Decimal("23416.91"),
    )
    assert result.required_minimum == Decimal("23885.24")
    assert result.compliant is False


def test_g7_incomplete_six_month_period_is_prorated_by_months():
    result = module.validate_ccns_annual_compensation(
        group_code="G7",
        reference_date=date(2026, 1, 1),
        weekly_hours=Decimal("35.00"),
        gross_annual_salary=Decimal("20298.97"),
        reference_period_months=6,
    )
    assert result.required_minimum == Decimal("20298.97")
    assert result.compliant is True


def test_short_part_time_majoration_applies_to_annual_minimum():
    result = module.validate_ccns_annual_compensation(
        group_code="G7",
        reference_date=date(2026, 1, 1),
        weekly_hours=Decimal("10.00"),
        gross_annual_salary=Decimal("10000.00"),
    )
    # 40597.94 * 10/35 * 1.05
    assert result.required_minimum == Decimal("12179.38")
    assert result.compliant is False
