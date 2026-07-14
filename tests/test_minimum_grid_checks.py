from datetime import date

from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.convention.classification import CCNSClassification
from domain.convention.salary_grid import SalaryGrid
from domain.convention.salary_grid_line import SalaryGridLine
from domain.convention.minimum_type import MinimumType
from domain.engine.minimum_checks import check_contract_minimum_from_grid


def _base_contract() -> Contract:
    return Contract(
        person_id="person-1",
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2026, 9, 1),
        ccns_classification_code="G3",
        salary_grid_code="CCNS-2026",
        base_salary_amount=2100.0,
        salary_unit="monthly",
        work_ratio=1.0,
        weekly_reference_hours=35.0,
    )


def _grid() -> SalaryGrid:
    return SalaryGrid(
        code="CCNS-2026",
        label="CCNS 2026",
        effective_date=date(2026, 1, 1),
    )


def test_monthly_minimum_compliant():
    contract = _base_contract()
    grid = _grid()
    lines = [
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G3",
            minimum_type=MinimumType.MONTHLY,
            amount=1997.87,
            unit="EUR",
        )
    ]
    result, anomaly = check_contract_minimum_from_grid(
        contract=contract,
        salary_grid=grid,
        salary_grid_lines=lines,
    )
    assert anomaly is None
    assert result.theoretical_value == 1997.87
    assert result.actual_value == 2100.0
    assert result.rule_reference_code == "REF_CCNS_MIN_G1_G6_MONTHLY_2026"


def test_monthly_minimum_not_reached():
    contract = _base_contract()
    contract.base_salary_amount = 1800.0
    grid = _grid()
    lines = [
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G3",
            minimum_type=MinimumType.MONTHLY,
            amount=1997.87,
            unit="EUR",
        )
    ]
    result, anomaly = check_contract_minimum_from_grid(
        contract=contract,
        salary_grid=grid,
        salary_grid_lines=lines,
    )
    assert anomaly is not None
    assert anomaly.code == "MINIMUM_CCNS_NON_ATTEINT"
    assert result.theoretical_value == 1997.87


def test_annual_minimum_for_group_7():
    contract = _base_contract()
    contract.ccns_classification_code = "G7"
    contract.base_salary_amount = 42000.0
    contract.salary_unit = "annual"
    grid = _grid()
    lines = [
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G7",
            minimum_type=MinimumType.ANNUAL,
            amount=40597.94,
            unit="EUR",
        )
    ]
    result, anomaly = check_contract_minimum_from_grid(
        contract=contract,
        salary_grid=grid,
        salary_grid_lines=lines,
    )
    assert anomaly is None
    assert result.theoretical_value == 40597.94


def test_missing_grid_line_creates_anomaly():
    contract = _base_contract()
    grid = _grid()
    result, anomaly = check_contract_minimum_from_grid(
        contract=contract,
        salary_grid=grid,
        salary_grid_lines=[],
    )
    assert anomaly is not None
    assert anomaly.code == "REGLE_INTROUVABLE"


def test_apprenticeship_line_selected_by_age_and_execution_year():
    contract = Contract(
        person_id="person-1",
        contract_type=ContractType.APPRENTICESHIP,
        employment_regime=EmploymentRegime.APPRENTICE,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2026, 9, 1),
        ccns_classification_code="APPRENTI",
        salary_grid_code="CCNS-2026",
        base_salary_amount=900.0,
        salary_unit="monthly",
        work_ratio=1.0,
        weekly_reference_hours=35.0,
    )
    grid = _grid()
    lines = [
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="APPRENTI",
            minimum_type=MinimumType.MONTHLY,
            amount=800.0,
            unit="EUR",
            age_min=18,
            age_max=20,
            execution_year_min=2,
            execution_year_max=2,
        )
    ]
    result, anomaly = check_contract_minimum_from_grid(
        contract=contract,
        salary_grid=grid,
        salary_grid_lines=lines,
        age=18,
        execution_year=2,
    )
    assert anomaly is None
    assert result.theoretical_value == 800.0
