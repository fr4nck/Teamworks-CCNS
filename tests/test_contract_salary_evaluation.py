from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from domain.contracts.contract import Contract
from domain.contracts.contract_salary_evaluation import (
    ContractSalaryEvaluationFailureReason,
    ContractSalaryEvaluationResult,
    ContractSalaryEvaluationService,
    ContractSalaryEvaluationStatus,
)
from domain.convention import (
    ApplicableSalaryMinimumService,
    CCNSClassification,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumComplianceService,
    SalaryMinimumPeriodicity,
    SmicCatalog,
    SmicTerritory,
    SmicVersion,
)


def group() -> CCNSClassification:
    return CCNSClassification(code="G1", label="Groupe 1")


def grid_version() -> SalaryGridVersion:
    return SalaryGridVersion(
        "G-2026",
        "G-2026",
        date(2026, 1, 1),
        (SalaryGridEntry(group(), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),),
    )


def smic(code: str, territory: SmicTerritory, monthly: str) -> SmicVersion:
    return SmicVersion(code, code, territory, date(2026, 1, 1), None, Decimal("10.00"), Decimal(monthly), Decimal("35.00"), "test")


def service() -> ContractSalaryEvaluationService:
    applicable = ApplicableSalaryMinimumService(
        SalaryMinimumComplianceService(SalaryGridCatalog((grid_version(),))),
        SmicCatalog((
            smic("MET", SmicTerritory.METROPOLITAN_FRANCE, "1800.00"),
            smic("MAY", SmicTerritory.MAYOTTE, "1500.00"),
        )),
    )
    return ContractSalaryEvaluationService(applicable)


def contract(**overrides) -> Contract:
    values = {
        "person_id": "person-1",
        "start_date": date(2026, 1, 1),
        "ccns_classification": group(),
        "base_salary_amount": Decimal("2100.00"),
        "weekly_reference_hours": Decimal("35.00"),
    }
    values.update(overrides)
    return Contract(**values)


def result_kwargs(result: ContractSalaryEvaluationResult, **overrides):
    values = {name: getattr(result, name) for name in result.__dataclass_fields__ if name != "id"}
    values.update(overrides)
    return values


def test_success_resolves_territory_from_evaluate_parameter():
    result = service().evaluate(contract(), territory=SmicTerritory.MAYOTTE)

    assert result.is_success()
    assert result.resolved_territory is SmicTerritory.MAYOTTE
    assert result.applicable_salary_minimum_result.territory is result.resolved_territory


def test_contract_territory_overrides_evaluate_parameter():
    result = service().evaluate(
        contract(smic_territory=SmicTerritory.METROPOLITAN_FRANCE),
        territory=SmicTerritory.MAYOTTE,
    )

    assert result.is_success()
    assert result.resolved_territory is SmicTerritory.METROPOLITAN_FRANCE
    assert result.applicable_salary_minimum_result.territory is result.resolved_territory


def test_missing_territory_failure_has_no_resolved_territory():
    result = service().evaluate(contract())

    assert result.is_failure()
    assert result.failure_reason is ContractSalaryEvaluationFailureReason.MISSING_TERRITORY
    assert result.resolved_territory is None


def test_result_rejects_success_without_resolved_territory_and_incoherent_territory():
    result = service().evaluate(contract(), territory=SmicTerritory.MAYOTTE)

    with pytest.raises(ValueError, match="territoire résolu"):
        ContractSalaryEvaluationResult(**result_kwargs(result, resolved_territory=None))
    with pytest.raises(ValueError, match="minimum applicable"):
        ContractSalaryEvaluationResult(**result_kwargs(result, resolved_territory=SmicTerritory.METROPOLITAN_FRANCE))


def test_contract_territory_must_match_success_result():
    result = service().evaluate(contract(smic_territory=SmicTerritory.MAYOTTE), territory=SmicTerritory.MAYOTTE)

    with pytest.raises(ValueError, match="contrat"):
        ContractSalaryEvaluationResult(**result_kwargs(result, resolved_territory=SmicTerritory.METROPOLITAN_FRANCE))


def test_invalid_territory_types_are_rejected():
    with pytest.raises(TypeError, match="territory"):
        service().evaluate(contract(), territory="mayotte")
    with pytest.raises(TypeError, match="smic_territory"):
        contract(smic_territory="mayotte")


def test_result_is_immutable():
    result = service().evaluate(contract(), territory=SmicTerritory.MAYOTTE)

    with pytest.raises(FrozenInstanceError):
        result.resolved_territory = SmicTerritory.METROPOLITAN_FRANCE
