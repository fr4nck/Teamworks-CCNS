from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.contracts import (
    Contract,
    ContractSalaryBatchAuditResult,
    ContractSalaryBatchAuditService,
    ContractSalaryControlProjection,
    ContractSalaryControlProjectionService,
    ContractSalaryControlRow,
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
    from domain.contracts import ContractSalaryBatchEvaluationService
    return ContractSalaryBatchAuditService(ContractSalaryBatchEvaluationService(ContractSalaryEvaluationService(engine)), SalaryMinimumBatchAuditService(SalaryMinimumAuditService()))


def contract(**overrides):
    data = dict(
        id=uuid4(), person_id=str(uuid4()), contract_type=ContractType.CDI,
        start_date=date(2026, 1, 1), ccns_classification=group(1),
        monthly_gross_salary_amount=Decimal("2100.00"), salary_unit="monthly",
        weekly_hours=Decimal("35.00"), smic_territory=SmicTerritory.METROPOLITAN_FRANCE,
    )
    data.update(overrides)
    return Contract(**data)


def audit(contracts):
    return audit_service().audit(contracts, date(2026, 6, 1))


def project(result):
    return ContractSalaryControlProjectionService().project(result)


def test_projection_vide_compteurs_validite_total_et_immutabilite():
    projection = project(audit([]))
    assert projection.rows == ()
    assert projection.total_count == projection.compliant_count == projection.non_compliant_count == projection.not_evaluated_count == 0
    assert projection.total_shortfall_amount == Decimal("0.00")
    assert projection.valid is True
    with pytest.raises(FrozenInstanceError):
        projection.id = uuid4()


def test_contrat_conforme_reprise_exacte_sans_echec_ni_anomalie():
    c = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    result = audit([c])
    row = project(result).rows[0]
    minimum = result.evaluations[0].result()
    assert row.status is ContractSalaryControlStatus.COMPLIANT
    assert row.contract_id == c.id and row.employee_id == UUID(c.person_id)
    assert row.classification_code == "G1"
    assert row.remuneration_amount == minimum.remuneration_amount == Decimal("2100.00")
    assert row.applicable_minimum_amount == minimum.required_minimum_amount == Decimal("2000.00")
    assert row.minimum_source is minimum.source
    assert row.territory is minimum.territory is SmicTerritory.METROPOLITAN_FRANCE
    assert row.shortfall_amount == Decimal("0.00")
    assert row.failure_reason is row.failure_message is row.issue_code is row.issue_message is None


def test_contrat_non_conforme_reprise_anomalie_shortfall_et_aucun_echec():
    c = contract(monthly_gross_salary_amount=Decimal("1999.99"))
    result = audit([c])
    row = project(result).rows[0]
    issue = result.issues[0]
    assert result.audit_results[0].issue_count() == 1
    assert row.status is ContractSalaryControlStatus.NON_COMPLIANT
    assert row.shortfall_amount == result.audit_results[0].shortfall_amount() == Decimal("0.01")
    assert row.issue_code == issue.code
    assert row.issue_message == issue.message
    assert row.failure_reason is row.failure_message is None


def test_contrat_non_evalue_reprise_motif_message_et_aucun_audit():
    c = contract(smic_territory=None)
    result = audit([c])
    row = project(result).rows[0]
    assert result.audit_result_for_contract(c.id) is None
    assert row.status is ContractSalaryControlStatus.NOT_EVALUATED
    assert row.failure_reason is ContractSalaryEvaluationFailureReason.MISSING_TERRITORY
    assert row.failure_message == result.failures[0].message
    assert row.shortfall_amount == Decimal("0.00")
    assert row.remuneration_amount is row.applicable_minimum_amount is row.minimum_source is row.issue_code is row.issue_message is None


def test_melange_des_trois_statuts_ordre_une_ligne_compteurs_valid_false_total():
    ok = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    ko = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    failed = contract(smic_territory=None)
    projection = project(audit([ok, ko, failed]))
    assert [row.contract_id for row in projection.rows] == [ok.id, ko.id, failed.id]
    assert projection.total_count == 3
    assert len({row.contract_id for row in projection.rows}) == 3
    assert projection.compliant_count == projection.non_compliant_count == projection.not_evaluated_count == 1
    assert projection.total_shortfall_amount == Decimal("10.00")
    assert projection.valid is False
    assert [row.status for row in projection.rows] == [ContractSalaryControlStatus.COMPLIANT, ContractSalaryControlStatus.NON_COMPLIANT, ContractSalaryControlStatus.NOT_EVALUATED]


def test_valid_false_avec_non_conformite_et_avec_refus_metier_valid_true_tous_conformes():
    assert project(audit([contract(), contract()])).valid is True
    assert project(audit([contract(monthly_gross_salary_amount=Decimal("1990.00"))])).valid is False
    assert project(audit([contract(smic_territory=None)])).valid is False


def test_recherches_par_contrat_salarie_et_statut_conservent_ordre():
    employee = str(uuid4())
    c1 = contract(person_id=employee)
    c2 = contract(person_id=employee, monthly_gross_salary_amount=Decimal("1990.00"))
    c3 = contract()
    projection = project(audit([c1, c2, c3]))
    assert projection.row_for_contract(c2.id) is projection.rows[1]
    assert projection.row_for_contract(uuid4()) is None
    assert projection.rows_for_employee(UUID(employee)) == projection.rows[:2]
    assert projection.rows_for_status(ContractSalaryControlStatus.NON_COMPLIANT) == (projection.rows[1],)
    with pytest.raises(TypeError):
        projection.row_for_contract(str(c1.id))
    with pytest.raises(TypeError):
        projection.rows_for_employee(employee)
    with pytest.raises(TypeError):
        projection.rows_for_status("compliant")


def test_types_stricts_uuid_date_datetime_decimal_et_status_champs_refuses():
    base = project(audit([contract()])).rows[0]
    with pytest.raises(TypeError):
        replace(base, contract_id=str(base.contract_id))
    with pytest.raises(TypeError):
        replace(base, reference_date=datetime(2026, 6, 1))
    with pytest.raises(TypeError):
        replace(base, remuneration_amount="2100.00")
    with pytest.raises(ValueError):
        replace(base, remuneration_amount=Decimal("2100.001"))
    with pytest.raises(ValueError):
        replace(base, shortfall_amount=Decimal("-0.01"))
    with pytest.raises(ValueError):
        replace(base, issue_code=" ")
    with pytest.raises(ValueError):
        replace(base, status=ContractSalaryControlStatus.NON_COMPLIANT, shortfall_amount=Decimal("0.00"), issue_code="X", issue_message="Y")
    with pytest.raises(TypeError):
        ContractSalaryControlProjectionService().project("bad")


def test_projection_refuse_date_incoherente_doublon_et_mauvais_types():
    row = project(audit([contract()])).rows[0]
    with pytest.raises(ValueError):
        ContractSalaryControlProjection(date(2026, 7, 1), (row,))
    with pytest.raises(ValueError):
        ContractSalaryControlProjection(row.reference_date, (row, row))
    with pytest.raises(TypeError):
        ContractSalaryControlProjection(row.reference_date, [row])
    with pytest.raises(TypeError):
        ContractSalaryControlProjection(row.reference_date, (object(),))
    with pytest.raises(TypeError):
        ContractSalaryControlProjection(datetime(2026, 6, 1), ())


def test_service_ne_modifie_aucune_instance_source():
    c1 = contract()
    c2 = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    source = audit([c1, c2])
    before = (source.evaluations, source.audit_results, source.issues, source.failures)
    projection = project(source)
    after = (source.evaluations, source.audit_results, source.issues, source.failures)
    assert after == before
    assert projection.rows[0].remuneration_amount == source.evaluations[0].result().remuneration_amount


def test_ligne_immutable():
    row = project(audit([contract()])).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.status = ContractSalaryControlStatus.NOT_EVALUATED
