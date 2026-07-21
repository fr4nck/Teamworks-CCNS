from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.contracts import (
    Contract,
    ContractSalaryBatchEvaluationResult,
    ContractSalaryBatchEvaluationService,
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
    SalaryMinimumAuditItem,
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


def single_service() -> ContractSalaryEvaluationService:
    engine = ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid(),))), SmicCatalog((smic(), smic(SmicTerritory.MAYOTTE, "1500.00"))))
    return ContractSalaryEvaluationService(engine)


def service() -> ContractSalaryBatchEvaluationService:
    return ContractSalaryBatchEvaluationService(single_service())


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


def test_empty_batch_is_coherent():
    result = service().evaluate([], date(2026, 6, 1))
    assert result.total_count == result.successful_count == result.failed_count == 0
    assert result.evaluations == ()
    assert result.successful_evaluations() == ()
    assert result.failed_evaluations() == ()
    assert result.to_salary_minimum_audit_items() == ()


def test_single_success_and_searches():
    c = contract()
    result = service().evaluate([c], date(2026, 6, 1))
    assert result.total_count == 1
    assert result.successful_count == 1
    assert result.failed_count == 0
    assert result.evaluation_for_contract(c.id).contract is c
    assert result.evaluations_for_employee(UUID(c.person_id)) == result.evaluations
    assert result.applicable_salary_minimum_results() == (result.evaluations[0].result(),)


def test_multiple_successes_preserve_input_order():
    contracts = [contract(), contract(), contract()]
    result = service().evaluate(contracts, date(2026, 6, 1))
    assert [evaluation.contract for evaluation in result.evaluations] == contracts
    assert [item.contract_id for item in result.to_salary_minimum_audit_items()] == [c.id for c in contracts]


def test_successes_and_business_failures_are_kept_without_interrupting_batch():
    ok = contract()
    inactive = contract(start_date=date(2026, 7, 1))
    missing_classification = contract(ccns_classification=None)
    missing_salary = contract(monthly_gross_salary_amount=None)
    missing_hours = contract(weekly_hours=None)
    annual_group = contract(ccns_classification=group(7))
    no_territory = contract(smic_territory=None)
    result = service().evaluate([ok, inactive, missing_classification, missing_salary, missing_hours, annual_group, no_territory], date(2026, 6, 1))
    assert result.successful_count == 1
    assert result.failed_count == 6
    assert [failure.reason for failure in result.failures()] == [
        ContractSalaryEvaluationFailureReason.CONTRACT_NOT_ACTIVE_ON_REFERENCE_DATE,
        ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION,
        ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION,
        ContractSalaryEvaluationFailureReason.MISSING_WEEKLY_HOURS,
        ContractSalaryEvaluationFailureReason.ANNUAL_CCNS_MINIMUM_NOT_SUPPORTED,
        ContractSalaryEvaluationFailureReason.MISSING_TERRITORY,
    ]
    assert result.to_salary_minimum_audit_items()[0].compliance_result is result.evaluations[0].result()


def test_contract_territory_has_priority_and_explicit_territory_is_fallback_only():
    own = contract(smic_territory=SmicTerritory.METROPOLITAN_FRANCE)
    fallback = contract(smic_territory=None)
    result = service().evaluate([own, fallback], date(2026, 6, 1), territory=SmicTerritory.MAYOTTE)
    assert result.evaluations[0].resolved_territory is SmicTerritory.METROPOLITAN_FRANCE
    assert result.evaluations[1].resolved_territory is SmicTerritory.MAYOTTE


def test_generator_consumed_once_and_each_contract_evaluated_once(monkeypatch):
    contracts = [contract(), contract()]
    iterations = 0
    calls = []

    def generator():
        nonlocal iterations
        for c in contracts:
            iterations += 1
            yield c

    original = ContractSalaryEvaluationService.evaluate

    def counted(self, c, reference_date, *, territory=None):
        calls.append(c.id)
        return original(self, c, reference_date, territory=territory)

    monkeypatch.setattr(ContractSalaryEvaluationService, "evaluate", counted)
    result = service().evaluate(generator(), date(2026, 6, 1))
    assert iterations == 2
    assert calls == [c.id for c in contracts]
    assert [e.contract for e in result.evaluations] == contracts


def test_duplicate_contract_id_refused_but_same_employee_accepted():
    employee_id = str(uuid4())
    first = contract(person_id=employee_id)
    second = contract(person_id=employee_id)
    result = service().evaluate([first, second], date(2026, 6, 1))
    assert result.evaluations_for_employee(UUID(employee_id)) == result.evaluations
    duplicate = contract(id=first.id)
    with pytest.raises(ValueError, match="Un même contrat ne peut pas être évalué plusieurs fois"):
        service().evaluate([first, duplicate], date(2026, 6, 1))


def test_strict_input_types_are_rejected():
    svc = service()
    with pytest.raises(TypeError):
        ContractSalaryBatchEvaluationService("bad")
    with pytest.raises(TypeError):
        svc.evaluate([contract()], datetime(2026, 6, 1))
    with pytest.raises(TypeError):
        svc.evaluate([contract()], date(2026, 6, 1), territory="metro")
    with pytest.raises(TypeError):
        svc.evaluate([object()], date(2026, 6, 1))
    result = svc.evaluate([contract()], date(2026, 6, 1))
    with pytest.raises(TypeError):
        result.evaluation_for_contract(str(result.evaluations[0].contract_id()))
    with pytest.raises(TypeError):
        result.evaluations_for_employee(str(result.evaluations[0].employee_id()))


def test_audit_item_conversion_keeps_instances_and_references_and_excludes_failures():
    ok = contract()
    failed = contract(smic_territory=None)
    result = service().evaluate([ok, failed], date(2026, 6, 1))
    items = result.to_salary_minimum_audit_items()
    assert len(items) == 1
    assert type(items[0]) is SalaryMinimumAuditItem
    assert items[0].compliance_result is result.evaluations[0].applicable_salary_minimum_result
    assert items[0].employee_id == UUID(ok.person_id)
    assert items[0].contract_id == ok.id


def test_result_invariants_and_immutability():
    c = contract()
    evaluation = single_service().evaluate(c, date(2026, 6, 1))
    result = ContractSalaryBatchEvaluationResult(date(2026, 6, 1), (evaluation,), id=uuid4())
    with pytest.raises(FrozenInstanceError):
        result.evaluations = ()
    with pytest.raises(TypeError):
        ContractSalaryBatchEvaluationResult(datetime(2026, 6, 1), (evaluation,))
    with pytest.raises(TypeError):
        ContractSalaryBatchEvaluationResult(date(2026, 6, 1), [evaluation])
    with pytest.raises(TypeError):
        ContractSalaryBatchEvaluationResult(date(2026, 6, 1), (object(),))
    with pytest.raises(TypeError):
        ContractSalaryBatchEvaluationResult(date(2026, 6, 1), (evaluation,), id=str(uuid4()))
    with pytest.raises(ValueError, match="date de référence"):
        ContractSalaryBatchEvaluationResult(date(2026, 6, 2), (evaluation,))
    with pytest.raises(ValueError, match="Un même contrat"):
        ContractSalaryBatchEvaluationResult(date(2026, 6, 1), (evaluation, evaluation))


def test_result_detects_incoherent_duplicate_during_lookup(monkeypatch):
    c = contract()
    first = single_service().evaluate(c, date(2026, 6, 1))
    second = single_service().evaluate(contract(), date(2026, 6, 1))
    result = ContractSalaryBatchEvaluationResult(date(2026, 6, 1), (first, second))
    monkeypatch.setattr(ContractSalaryEvaluationResult, "contract_id", lambda self: c.id)
    with pytest.raises(ValueError, match="Plusieurs évaluations"):
        result.evaluation_for_contract(c.id)
