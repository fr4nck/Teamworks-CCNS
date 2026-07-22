from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.contracts import (
    Contract,
    ContractSalaryBatchAuditService,
    ContractSalaryBatchEvaluationService,
    ContractSalaryControlProjection,
    ContractSalaryControlProjectionService,
    ContractSalaryControlResult,
    ContractSalaryControlService,
    ContractSalaryControlStatus,
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
    SalaryMinimumAuditService,
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
        (SalaryGridEntry(group(1), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),),
    )


def smic(territory=SmicTerritory.METROPOLITAN_FRANCE, amount="1800.00"):
    return SmicVersion(f"S-{territory.value}", "SMIC", territory, date(2026, 1, 1), None, Decimal("10.00"), Decimal(amount), Decimal("35.00"), "test")


def audit_service():
    engine = ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid(),))), SmicCatalog((smic(), smic(SmicTerritory.MAYOTTE, "1500.00"))))
    return ContractSalaryBatchAuditService(ContractSalaryBatchEvaluationService(ContractSalaryEvaluationService(engine)), SalaryMinimumBatchAuditService(SalaryMinimumAuditService()))


def service():
    return ContractSalaryControlService(audit_service(), ContractSalaryControlProjectionService())


def contract(**overrides):
    data = dict(
        id=uuid4(), person_id=str(uuid4()), contract_type=ContractType.CDI,
        start_date=date(2026, 1, 1), ccns_classification=group(1),
        monthly_gross_salary_amount=Decimal("2100.00"), salary_unit="monthly",
        weekly_hours=Decimal("35.00"), smic_territory=SmicTerritory.METROPOLITAN_FRANCE,
    )
    data.update(overrides)
    return Contract(**data)


def control(contracts, *, territory=None):
    return service().control(contracts, date(2026, 6, 1), territory=territory)


def test_lot_vide_coherent():
    result = control([])
    assert result.rows == ()
    assert result.total_count == result.compliant_count == result.non_compliant_count == result.not_evaluated_count == 0
    assert result.total_shortfall_amount == Decimal("0.00")
    assert result.valid is True


def test_conforme_non_conforme_non_evalue_et_melange_ordre():
    ok = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    ko = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    failed = contract(smic_territory=None)
    result = control([ok, ko, failed])
    assert [row.contract_id for row in result.rows] == [ok.id, ko.id, failed.id]
    assert [row.status for row in result.rows] == [ContractSalaryControlStatus.COMPLIANT, ContractSalaryControlStatus.NON_COMPLIANT, ContractSalaryControlStatus.NOT_EVALUATED]
    assert result.compliant_count == result.non_compliant_count == result.not_evaluated_count == 1
    assert result.total_shortfall_amount == Decimal("10.00")
    assert result.valid is False
    assert result.rows[2].failure_reason is ContractSalaryEvaluationFailureReason.MISSING_TERRITORY


def test_services_appeles_une_fois_instances_et_lignes_conservees(monkeypatch):
    calls = {"audit": 0, "project": 0}
    captured = {}
    original_audit = ContractSalaryBatchAuditService.audit
    original_project = ContractSalaryControlProjectionService.project

    def counted_audit(self, contracts, reference_date, *, territory=None):
        calls["audit"] += 1
        assert territory is SmicTerritory.MAYOTTE
        captured["audit_result"] = original_audit(self, contracts, reference_date, territory=territory)
        return captured["audit_result"]

    def counted_project(self, audit_result):
        calls["project"] += 1
        assert audit_result is captured["audit_result"]
        captured["projection"] = original_project(self, audit_result)
        return captured["projection"]

    monkeypatch.setattr(ContractSalaryBatchAuditService, "audit", counted_audit)
    monkeypatch.setattr(ContractSalaryControlProjectionService, "project", counted_project)
    result = control([contract(smic_territory=None)], territory=SmicTerritory.MAYOTTE)
    assert calls == {"audit": 1, "project": 1}
    assert result.batch_audit_result is captured["audit_result"]
    assert result.projection is captured["projection"]
    assert result.projection.rows[0] is result.rows[0]
    assert result.batch_audit_result.evaluations[0].resolved_territory is SmicTerritory.MAYOTTE


def test_generateur_consomme_une_seule_fois():
    contracts = [contract(), contract(monthly_gross_salary_amount=Decimal("1999.00"))]
    iterations = 0

    def gen():
        nonlocal iterations
        for c in contracts:
            iterations += 1
            yield c

    result = control(gen())
    assert iterations == 2
    assert result.total_count == 2


def test_territoire_contrat_prioritaire_et_absence_non_evalue():
    own = contract(smic_territory=SmicTerritory.METROPOLITAN_FRANCE)
    fallback = contract(smic_territory=None)
    with_fallback = control([own, fallback], territory=SmicTerritory.MAYOTTE)
    assert with_fallback.batch_audit_result.evaluations[0].resolved_territory is SmicTerritory.METROPOLITAN_FRANCE
    assert with_fallback.batch_audit_result.evaluations[1].resolved_territory is SmicTerritory.MAYOTTE
    without = control([contract(smic_territory=None)])
    assert without.rows[0].status is ContractSalaryControlStatus.NOT_EVALUATED


def test_types_entree_services_date_territoire_uuid_et_immutabilite_refuses():
    with pytest.raises(TypeError):
        ContractSalaryControlService("bad", ContractSalaryControlProjectionService())
    with pytest.raises(TypeError):
        ContractSalaryControlService(audit_service(), "bad")
    with pytest.raises(TypeError):
        service().control([contract()], datetime(2026, 6, 1))
    with pytest.raises(TypeError):
        service().control([contract()], date(2026, 6, 1), territory="metro")
    valid = control([contract()])
    with pytest.raises(TypeError):
        ContractSalaryControlResult(valid.batch_audit_result, valid.projection, id=str(uuid4()))
    with pytest.raises(FrozenInstanceError):
        valid.id = uuid4()


def test_delegations_compteurs_filtres_recherches_total_valid_decimal():
    employee = str(uuid4())
    c1 = contract(person_id=employee, monthly_gross_salary_amount=Decimal("2100.00"))
    c2 = contract(person_id=employee, monthly_gross_salary_amount=Decimal("1999.99"))
    result = control([c1, c2])
    assert result.reference_date == date(2026, 6, 1)
    assert result.total_count == 2
    assert result.compliant_rows() == (result.rows[0],)
    assert result.non_compliant_rows() == result.rows_for_status(ContractSalaryControlStatus.NON_COMPLIANT) == (result.rows[1],)
    assert result.not_evaluated_rows() == ()
    assert result.row_for_contract(c2.id) is result.rows[1]
    assert result.rows_for_employee(UUID(employee)) == result.rows
    assert result.total_shortfall_amount == Decimal("0.01")
    assert type(result.total_shortfall_amount) is Decimal
    assert result.valid is False


def test_resultat_refuse_mauvais_types_et_incoherences():
    valid = control([contract(), contract(monthly_gross_salary_amount=Decimal("1999.99")), contract(smic_territory=None)])
    with pytest.raises(TypeError):
        ContractSalaryControlResult("bad", valid.projection)
    with pytest.raises(TypeError):
        ContractSalaryControlResult(valid.batch_audit_result, "bad")
    with pytest.raises(ValueError, match="date"):
        ContractSalaryControlResult(valid.batch_audit_result, ContractSalaryControlProjection(date(2026, 7, 1), valid.rows))
    with pytest.raises(ValueError, match="nombre"):
        ContractSalaryControlResult(valid.batch_audit_result, ContractSalaryControlProjection(valid.reference_date, valid.rows[:1]))
    reversed_rows = tuple(reversed(valid.rows))
    with pytest.raises(ValueError, match="ordre"):
        ContractSalaryControlResult(valid.batch_audit_result, ContractSalaryControlProjection(valid.reference_date, reversed_rows))
    wrong_employee = replace(valid.rows[0], employee_id=uuid4())
    with pytest.raises(ValueError, match="employee_id"):
        ContractSalaryControlResult(valid.batch_audit_result, ContractSalaryControlProjection(valid.reference_date, (wrong_employee,) + valid.rows[1:]))
    wrong_success = replace(valid.rows[0], status=ContractSalaryControlStatus.NOT_EVALUATED, remuneration_amount=None, applicable_minimum_amount=None, minimum_source=None, territory=None, failure_reason=ContractSalaryEvaluationFailureReason.MISSING_TERRITORY, failure_message="x")
    with pytest.raises(ValueError, match="réussie"):
        ContractSalaryControlResult(valid.batch_audit_result, ContractSalaryControlProjection(valid.reference_date, (wrong_success,) + valid.rows[1:]))
    wrong_failure = replace(valid.rows[2], status=ContractSalaryControlStatus.COMPLIANT, remuneration_amount=Decimal("2000.00"), applicable_minimum_amount=Decimal("2000.00"), minimum_source=valid.rows[0].minimum_source, territory=SmicTerritory.METROPOLITAN_FRANCE, failure_reason=None, failure_message=None)
    with pytest.raises(ValueError, match="échec"):
        ContractSalaryControlResult(valid.batch_audit_result, ContractSalaryControlProjection(valid.reference_date, valid.rows[:2] + (wrong_failure,)))


def test_aucune_modification_des_instances_source():
    result = control([contract(), contract(monthly_gross_salary_amount=Decimal("1990.00"))])
    before = (result.batch_audit_result.evaluations, result.batch_audit_result.audit_results, result.projection.rows)
    assert result.compliant_rows()
    after = (result.batch_audit_result.evaluations, result.batch_audit_result.audit_results, result.projection.rows)
    assert after == before
