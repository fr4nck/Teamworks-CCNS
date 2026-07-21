from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.contracts import (
    Contract,
    ContractSalaryEvaluationFailure,
    ContractSalaryEvaluationFailureReason,
    ContractSalaryEvaluationResult,
    ContractSalaryEvaluationService,
    ContractType,
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


def group(number: int) -> CCNSClassification:
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def grid() -> SalaryGridVersion:
    return SalaryGridVersion(
        "G",
        "Grille",
        date(2026, 1, 1),
        (
            SalaryGridEntry(group(1), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),
            SalaryGridEntry(group(7), Decimal("42000.00"), SalaryMinimumPeriodicity.ANNUAL),
        ),
    )


def smic(territory=SmicTerritory.METROPOLITAN_FRANCE, amount="1800.00") -> SmicVersion:
    return SmicVersion(f"S-{territory.value}", "SMIC", territory, date(2026, 1, 1), None, Decimal("10.00"), Decimal(amount), Decimal("35.00"), "test")


def service() -> ContractSalaryEvaluationService:
    engine = ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid(),))), SmicCatalog((smic(), smic(SmicTerritory.MAYOTTE, "1500.00"))))
    return ContractSalaryEvaluationService(engine)


def contract(**overrides) -> Contract:
    data = dict(
        id=uuid4(),
        person_id=str(uuid4()),
        contract_type=ContractType.CDI,
        start_date=date(2026, 1, 1),
        end_date=None,
        ccns_classification=group(1),
        monthly_gross_salary_amount=Decimal("2100.00"),
        salary_unit="monthly",
        weekly_hours=Decimal("35.00"),
        smic_territory=SmicTerritory.METROPOLITAN_FRANCE,
    )
    data.update(overrides)
    return Contract(**data)


def test_evaluation_success_delegates_and_keeps_engine_instance():
    result = service().evaluate(contract(), date(2026, 6, 1))
    assert result.is_successful()
    assert result.result() is result.applicable_salary_minimum_result
    assert result.contract_id() == result.contract.id
    assert result.employee_id() == UUID(result.contract.person_id)
    assert result.result().classification_group == result.contract.ccns_classification


def test_territory_parameter_used_only_when_contract_has_no_territory():
    c = contract(smic_territory=None)
    result = service().evaluate(c, date(2026, 6, 1), territory=SmicTerritory.MAYOTTE)
    assert result.result().territory is SmicTerritory.MAYOTTE


def test_contract_territory_has_priority_over_parameter():
    result = service().evaluate(contract(), date(2026, 6, 1), territory=SmicTerritory.MAYOTTE)
    assert result.result().territory is SmicTerritory.METROPOLITAN_FRANCE


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"start_date": date(2026, 2, 1)}, ContractSalaryEvaluationFailureReason.CONTRACT_NOT_ACTIVE_ON_REFERENCE_DATE),
        ({"ccns_classification": None}, ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION),
        ({"monthly_gross_salary_amount": None}, ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION),
        ({"salary_unit": "annual"}, ContractSalaryEvaluationFailureReason.UNSUPPORTED_REMUNERATION_PERIODICITY),
        ({"weekly_hours": None}, ContractSalaryEvaluationFailureReason.MISSING_WEEKLY_HOURS),
        ({"smic_territory": None}, ContractSalaryEvaluationFailureReason.MISSING_TERRITORY),
    ],
)
def test_business_failures_do_not_call_engine(kwargs, reason):
    result = service().evaluate(contract(**kwargs), date(2026, 1, 15))
    assert not result.is_successful()
    assert result.failure_reason() is reason


def test_annual_group_failure_is_mapped():
    result = service().evaluate(contract(ccns_classification=group(7)), date(2026, 6, 1))
    assert result.failure_reason() is ContractSalaryEvaluationFailureReason.ANNUAL_CCNS_MINIMUM_NOT_SUPPORTED
    assert result.failure.message == "Le contrôle salarial direct du contrat est limité aux minima CCNS mensuels."


def test_technical_inputs_are_strict():
    svc = service()
    with pytest.raises(TypeError):
        ContractSalaryEvaluationService("bad")
    with pytest.raises(TypeError):
        svc.evaluate({}, date(2026, 1, 1))
    with pytest.raises(TypeError):
        svc.evaluate(contract(), datetime(2026, 1, 1))
    with pytest.raises(TypeError):
        svc.evaluate(contract(), date(2026, 1, 1), territory="metro")


def test_result_invariants_and_immutability():
    c = contract()
    ok = service().evaluate(c, date(2026, 6, 1))
    with pytest.raises(FrozenInstanceError):
        ok.successful = False
    with pytest.raises(ValueError, match="L’évaluation salariale du contrat n’a pas abouti."):
        service().evaluate(contract(smic_territory=None), date(2026, 6, 1)).result()
    failure = ContractSalaryEvaluationFailure(ContractSalaryEvaluationFailureReason.MISSING_TERRITORY, "x", c.id, UUID(c.person_id), date(2026, 6, 1), id=uuid4())
    assert failure.id
    with pytest.raises(TypeError):
        ContractSalaryEvaluationFailure(ContractSalaryEvaluationFailureReason.MISSING_TERRITORY, "x", c.id, UUID(c.person_id), date(2026, 6, 1), id=str(uuid4()))
    with pytest.raises(ValueError):
        ContractSalaryEvaluationResult(c, date(2026, 6, 1), True, None, failure)
