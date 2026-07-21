from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from domain.contracts.contract import Contract
from domain.convention import (
    ApplicableSalaryMinimumService,
    CCNSClassification,
    ContractSalaryEvaluationResult,
    ContractSalaryEvaluationService,
    ContractSalaryEvaluationStatus,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumComplianceService,
    SalaryMinimumPeriodicity,
    SmicCatalog,
    SmicTerritory,
    SmicVersion,
)


def group(number: int) -> CCNSClassification:
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def smic(code: str, territory: SmicTerritory, monthly: str) -> SmicVersion:
    return SmicVersion(code, code, territory, date(2026, 1, 1), None, Decimal("10.00"), Decimal(monthly), Decimal("35.00"), "test")


def service() -> ContractSalaryEvaluationService:
    grid = SalaryGridVersion("G", "G", date(2026, 1, 1), (SalaryGridEntry(group(1), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),))
    app = ApplicableSalaryMinimumService(
        SalaryMinimumComplianceService(SalaryGridCatalog((grid,))),
        SmicCatalog((smic("S-M", SmicTerritory.METROPOLITAN_FRANCE, "1900.00"), smic("S-Y", SmicTerritory.MAYOTTE, "1500.00"))),
    )
    return ContractSalaryEvaluationService(app)


def contract(**overrides) -> Contract:
    values = {
        "person_id": "P1",
        "ccns_classification_code": "G1",
        "base_salary_amount": 2100.0,
        "weekly_reference_hours": 35.0,
    }
    values.update(overrides)
    return Contract(**values)


def result_kwargs(result: ContractSalaryEvaluationResult, **overrides):
    values = {name: getattr(result, name) for name in result.__dataclass_fields__ if name != "id"}
    values.update(overrides)
    return values


def test_contract_territory_is_used_for_success():
    c = contract(smic_territory=SmicTerritory.MAYOTTE)
    result = service().evaluate(c, date(2026, 6, 1))

    assert result.is_success()
    assert result.resolved_territory is SmicTerritory.MAYOTTE
    assert result.applicable_salary_minimum_result.territory is SmicTerritory.MAYOTTE


def test_parameter_territory_is_used_when_contract_has_none():
    result = service().evaluate(contract(), date(2026, 6, 1), SmicTerritory.METROPOLITAN_FRANCE)

    assert result.resolved_territory is SmicTerritory.METROPOLITAN_FRANCE
    assert result.applicable_salary_minimum_result.territory is SmicTerritory.METROPOLITAN_FRANCE


def test_contract_territory_has_priority_over_parameter_territory():
    result = service().evaluate(contract(smic_territory=SmicTerritory.MAYOTTE), date(2026, 6, 1), SmicTerritory.METROPOLITAN_FRANCE)

    assert result.resolved_territory is SmicTerritory.MAYOTTE
    assert result.applicable_salary_minimum_result.territory is SmicTerritory.MAYOTTE


def test_success_without_resolved_territory_is_refused():
    result = service().evaluate(contract(), date(2026, 6, 1), SmicTerritory.METROPOLITAN_FRANCE)

    with pytest.raises(ValueError, match="resolved_territory"):
        ContractSalaryEvaluationResult(**result_kwargs(result, resolved_territory=None))


def test_engine_result_with_different_territory_is_refused():
    svc = service()
    metro = svc.evaluate(contract(), date(2026, 6, 1), SmicTerritory.METROPOLITAN_FRANCE)
    mayotte_engine = svc.evaluate(contract(), date(2026, 6, 1), SmicTerritory.MAYOTTE).applicable_salary_minimum_result

    with pytest.raises(ValueError, match="territoire résolu"):
        ContractSalaryEvaluationResult(**result_kwargs(metro, applicable_salary_minimum_result=mayotte_engine))


def test_missing_territory_failure_without_territory_is_accepted():
    result = service().evaluate(contract(), date(2026, 6, 1))

    assert result.status is ContractSalaryEvaluationStatus.MISSING_TERRITORY
    assert result.resolved_territory is None
    assert result.applicable_salary_minimum_result is None


def test_missing_territory_failure_with_territory_is_refused():
    result = service().evaluate(contract(), date(2026, 6, 1))

    with pytest.raises(ValueError, match="None"):
        ContractSalaryEvaluationResult(**result_kwargs(result, resolved_territory=SmicTerritory.MAYOTTE))


def test_bad_resolved_territory_type_is_refused():
    result = service().evaluate(contract(), date(2026, 6, 1), SmicTerritory.METROPOLITAN_FRANCE)

    with pytest.raises(TypeError, match="SmicTerritory"):
        ContractSalaryEvaluationResult(**result_kwargs(result, resolved_territory="mayotte"))


def test_contract_salary_evaluation_result_is_immutable():
    result = service().evaluate(contract(), date(2026, 6, 1), SmicTerritory.METROPOLITAN_FRANCE)

    with pytest.raises(FrozenInstanceError):
        result.resolved_territory = SmicTerritory.MAYOTTE
