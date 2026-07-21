from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.contracts import (
    Contract,
    ContractSalaryBatchAuditResult,
    ContractSalaryBatchAuditService,
    ContractSalaryBatchEvaluationResult,
    ContractSalaryBatchEvaluationService,
    ContractSalaryEvaluationFailureReason,
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
    SalaryMinimumAuditService,
    SalaryMinimumBatchAuditResult,
    SalaryMinimumBatchAuditService,
    SalaryMinimumComplianceService,
    SalaryMinimumPeriodicity,
    SmicCatalog,
    SmicTerritory,
    SmicVersion,
)


def group(number=1):
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def grid():
    return SalaryGridVersion(
        "G", "Grille", date(2026, 1, 1),
        (SalaryGridEntry(group(1), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),
         SalaryGridEntry(group(7), Decimal("42000.00"), SalaryMinimumPeriodicity.ANNUAL)),
    )


def smic(territory=SmicTerritory.METROPOLITAN_FRANCE, amount="1800.00"):
    return SmicVersion(f"S-{territory.value}", "SMIC", territory, date(2026, 1, 1), None, Decimal("10.00"), Decimal(amount), Decimal("35.00"), "test")


def evaluation_service():
    engine = ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid(),))), SmicCatalog((smic(), smic(SmicTerritory.MAYOTTE, "1500.00"))))
    return ContractSalaryEvaluationService(engine)


def batch_evaluation_service():
    return ContractSalaryBatchEvaluationService(evaluation_service())


def service():
    return ContractSalaryBatchAuditService(batch_evaluation_service(), SalaryMinimumBatchAuditService(SalaryMinimumAuditService()))


def contract(**overrides):
    data = dict(
        id=uuid4(), person_id=str(uuid4()), contract_type=ContractType.CDI,
        start_date=date(2026, 1, 1), end_date=None, ccns_classification=group(1),
        monthly_gross_salary_amount=Decimal("2100.00"), salary_unit="monthly",
        weekly_hours=Decimal("35.00"), smic_territory=SmicTerritory.METROPOLITAN_FRANCE,
    )
    data.update(overrides)
    return Contract(**data)


def audit(contracts, *, territory=None):
    return service().audit(contracts, date(2026, 6, 1), territory=territory)


def test_lot_vide_accepte_et_coherent():
    result = audit([])
    assert result.total_contract_count == result.evaluated_contract_count == result.failed_contract_count == 0
    assert result.compliant_contract_count == result.non_compliant_contract_count == result.issue_count == 0
    assert result.evaluations == result.audit_results == result.issues == ()
    assert result.failures == result.successful_evaluations() == result.failed_evaluations() == ()
    assert result.total_shortfall_amount == Decimal("0.00")
    assert result.valid is True


def test_contrat_conforme_et_valid_true():
    c = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    result = audit([c])
    assert result.total_contract_count == result.evaluated_contract_count == result.compliant_contract_count == 1
    assert result.failed_contract_count == result.non_compliant_contract_count == result.issue_count == 0
    assert result.valid is True
    assert result.evaluation_for_contract(c.id).contract is c
    assert result.audit_result_for_contract(c.id) is result.audit_results[0]


def test_contrat_non_conforme_anomalie_et_manque_total():
    c = contract(monthly_gross_salary_amount=Decimal("1999.99"))
    result = audit([c])
    assert result.non_compliant_contract_count == 1
    assert result.compliant_contract_count == 0
    assert result.issue_count == 1
    assert result.total_shortfall_amount == Decimal("0.01")
    assert result.valid is False
    assert result.issues_for_contract(c.id) == result.issues
    assert result.issues_for_employee(UUID(c.person_id)) == result.issues


def test_contrat_en_refus_metier_non_audite_et_valid_false():
    c = contract(smic_territory=None)
    result = audit([c])
    assert result.failed_contract_count == 1
    assert result.evaluated_contract_count == 0
    assert result.audit_results == result.issues == ()
    assert result.failures[0].reason is ContractSalaryEvaluationFailureReason.MISSING_TERRITORY
    assert result.valid is False


def test_melange_ordre_compteurs_references_et_instances_conserves():
    ok = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    ko = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    failed = contract(smic_territory=None)
    result = audit([ok, ko, failed])
    assert [e.contract for e in result.evaluations] == [ok, ko, failed]
    assert [a.contract_id for a in result.audit_results] == [ok.id, ko.id]
    assert tuple(a.compliance_result for a in result.audit_results) == tuple(e.result() for e in result.successful_evaluations())
    assert result.total_contract_count == 3
    assert result.evaluated_contract_count == 2
    assert result.failed_contract_count == 1
    assert result.compliant_contract_count == 1
    assert result.non_compliant_contract_count == 1
    assert result.issue_count == 1
    assert result.total_shortfall_amount == Decimal("10.00")
    assert result.valid is False


def test_appels_services_exactement_une_fois_et_generateur_consomme_une_fois(monkeypatch):
    contracts = [contract(), contract(monthly_gross_salary_amount=Decimal("1999.00"))]
    iterations = 0
    calls = {"evaluate": 0, "audit": 0}

    def gen():
        nonlocal iterations
        for c in contracts:
            iterations += 1
            yield c

    original_evaluate = ContractSalaryBatchEvaluationService.evaluate
    original_audit = SalaryMinimumBatchAuditService.audit

    def counted_evaluate(self, items, reference_date, *, territory=None):
        calls["evaluate"] += 1
        return original_evaluate(self, items, reference_date, territory=territory)

    def counted_audit(self, items):
        calls["audit"] += 1
        return original_audit(self, items)

    monkeypatch.setattr(ContractSalaryBatchEvaluationService, "evaluate", counted_evaluate)
    monkeypatch.setattr(SalaryMinimumBatchAuditService, "audit", counted_audit)
    result = service().audit(gen(), date(2026, 6, 1))
    assert calls == {"evaluate": 1, "audit": 1}
    assert iterations == 2
    assert result.evaluated_contract_count == 2


def test_filtres_par_contract_id_et_employee_id():
    employee = str(uuid4())
    c1 = contract(person_id=employee, monthly_gross_salary_amount=Decimal("1990.00"))
    c2 = contract(person_id=employee)
    other = uuid4()
    result = audit([c1, c2])
    assert result.evaluations_for_employee(UUID(employee)) == result.evaluations
    assert result.issues_for_employee(UUID(employee)) == result.issues
    assert result.audit_result_for_contract(c1.id) is result.audit_results[0]
    assert result.audit_result_for_contract(other) is None
    assert result.issues_for_contract(other) == ()
    with pytest.raises(TypeError):
        result.evaluation_for_contract(str(c1.id))
    with pytest.raises(TypeError):
        result.evaluations_for_employee(employee)


def test_territoire_propre_secours_absence_et_groupe_annuel_refuse():
    own = contract(smic_territory=SmicTerritory.METROPOLITAN_FRANCE)
    fallback = contract(smic_territory=None)
    missing = contract(smic_territory=None)
    annual = contract(ccns_classification=group(7))
    with_fallback = audit([own, fallback], territory=SmicTerritory.MAYOTTE)
    assert with_fallback.evaluations[0].resolved_territory is SmicTerritory.METROPOLITAN_FRANCE
    assert with_fallback.evaluations[1].resolved_territory is SmicTerritory.MAYOTTE
    without_fallback = audit([missing, annual])
    assert [failure.reason for failure in without_fallback.failures] == [
        ContractSalaryEvaluationFailureReason.MISSING_TERRITORY,
        ContractSalaryEvaluationFailureReason.ANNUAL_CCNS_MINIMUM_NOT_SUPPORTED,
    ]


def test_types_entrees_doublons_et_immutabilite_refuses():
    svc = service()
    with pytest.raises(TypeError):
        ContractSalaryBatchAuditService("bad", SalaryMinimumBatchAuditService(SalaryMinimumAuditService()))
    with pytest.raises(TypeError):
        ContractSalaryBatchAuditService(batch_evaluation_service(), "bad")
    with pytest.raises(TypeError):
        svc.audit([object()], date(2026, 6, 1))
    with pytest.raises(TypeError):
        svc.audit([contract()], datetime(2026, 6, 1))
    with pytest.raises(TypeError):
        svc.audit([contract()], date(2026, 6, 1), territory="metro")
    c = contract()
    with pytest.raises(ValueError, match="Un même contrat"):
        svc.audit([c, contract(id=c.id)], date(2026, 6, 1))
    result = audit([c])
    with pytest.raises(FrozenInstanceError):
        result.id = uuid4()


def test_incoherences_resultat_refusees():
    c1 = contract()
    c2 = contract()
    evaluation_result = batch_evaluation_service().evaluate([c1, c2], date(2026, 6, 1))
    items = evaluation_result.to_salary_minimum_audit_items()
    audit_result = SalaryMinimumBatchAuditService(SalaryMinimumAuditService()).audit(items)
    with pytest.raises(TypeError):
        ContractSalaryBatchAuditResult("bad", audit_result)
    with pytest.raises(TypeError):
        ContractSalaryBatchAuditResult(evaluation_result, "bad")
    with pytest.raises(TypeError):
        ContractSalaryBatchAuditResult(evaluation_result, audit_result, id=str(uuid4()))
    missing_item_batch = SalaryMinimumBatchAuditResult(audit_result.items[:1], audit_result.audit_results[:1], (), True, 1, 0, Decimal("0.00"))
    with pytest.raises(ValueError, match="nombre"):
        ContractSalaryBatchAuditResult(evaluation_result, missing_item_batch)
    reversed_batch = SalaryMinimumBatchAuditService(SalaryMinimumAuditService()).audit(tuple(reversed(items)))
    with pytest.raises(ValueError, match="instance|UUID"):
        ContractSalaryBatchAuditResult(evaluation_result, reversed_batch)
    wrong_item = SalaryMinimumAuditItem(items[0].compliance_result, employee_id=uuid4(), contract_id=items[0].contract_id)
    wrong_audit = SalaryMinimumBatchAuditService(SalaryMinimumAuditService()).audit((wrong_item, items[1]))
    with pytest.raises(ValueError, match="UUID"):
        ContractSalaryBatchAuditResult(evaluation_result, wrong_audit)
