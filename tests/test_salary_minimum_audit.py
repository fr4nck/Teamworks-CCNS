from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.convention import (
    ApplicableSalaryMinimumResult,
    ApplicableSalaryMinimumService,
    ApplicableSalaryMinimumSource,
    ApplicableSalaryMinimumStatus,
    CCNSClassification,
    SALARY_MINIMUM_AUDIT_CODE,
    SALARY_MINIMUM_AUDIT_MESSAGE,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumAuditIssue,
    SalaryMinimumAuditIssueType,
    SalaryMinimumAuditResult,
    SalaryMinimumAuditService,
    SalaryMinimumComplianceService,
    SalaryMinimumPeriodicity,
    SmicCatalog,
    SmicTerritory,
    SmicVersion,
)
from domain.engine.anomaly_level import AnomalyLevel
from teamworks.CcnsCore.audit_sorting import compute_row_severity


def group(number=1):
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def grid(g1="2000.00"):
    return SalaryGridVersion(
        "G",
        "G",
        date(2026, 1, 1),
        (SalaryGridEntry(group(1), Decimal(g1), SalaryMinimumPeriodicity.MONTHLY),),
    )


def smic(monthly="1800.00"):
    return SmicVersion("S", "S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, Decimal("10.00"), Decimal(monthly), Decimal("35.00"), "test")


def evaluate(amount, *, ccns="2000.00", smic_amount="1800.00"):
    svc = ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid(ccns),))), SmicCatalog((smic(smic_amount),)))
    return svc.evaluate(group(1), date(2026, 6, 1), SmicTerritory.METROPOLITAN_FRANCE, Decimal(amount), Decimal("35.00"))


def kwargs(result, **overrides):
    values = {name: getattr(result, name) for name in result.__dataclass_fields__ if name != "id"}
    values.update(overrides)
    return values


def test_conforme_ne_produit_aucune_anomalie_et_conserve_references():
    employee_id = uuid4()
    contract_id = uuid4()
    service = SalaryMinimumAuditService()
    for source_result in (
        evaluate("2000.00", ccns="2000.00", smic_amount="1800.00"),
        evaluate("2100.00", ccns="2000.00", smic_amount="1800.00"),
        evaluate("2000.00", ccns="1800.00", smic_amount="2000.00"),
        evaluate("2000.00", ccns="2000.00", smic_amount="2000.00"),
    ):
        result = service.audit(source_result, employee_id=employee_id, contract_id=contract_id)
        assert result.is_valid()
        assert not result.has_issues()
        assert result.issue_count() == 0
        assert result.issues == ()
        assert result.employee_id == employee_id
        assert result.contract_id == contract_id
        assert result.has_employee_reference()
        assert result.has_contract_reference()
        assert result.shortfall_amount() == Decimal("0.00")
        assert result.applicable_source() is source_result.source


@pytest.mark.parametrize(
    ("ccns", "smic_amount", "expected_source"),
    [
        ("2000.00", "1800.00", ApplicableSalaryMinimumSource.CCNS),
        ("1800.00", "2000.00", ApplicableSalaryMinimumSource.SMIC),
        ("2000.00", "2000.00", ApplicableSalaryMinimumSource.EQUAL),
    ],
)
def test_non_conforme_produit_une_anomalie_structuree(ccns, smic_amount, expected_source):
    employee_id = uuid4()
    contract_id = uuid4()
    source_result = evaluate("1900.00", ccns=ccns, smic_amount=smic_amount)

    result = SalaryMinimumAuditService().audit(source_result, employee_id=employee_id, contract_id=contract_id)

    assert not result.is_valid()
    assert result.has_issues()
    assert result.issue_count() == 1
    issue = result.issues[0]
    assert issue.issue_type is SalaryMinimumAuditIssueType.REMUNERATION_BELOW_APPLICABLE_MINIMUM
    assert issue.code == SALARY_MINIMUM_AUDIT_CODE
    assert issue.message == SALARY_MINIMUM_AUDIT_MESSAGE
    assert issue.level is AnomalyLevel.BLOCKING
    assert issue.shortfall_amount() == source_result.shortfall_amount()
    assert issue.details["required_minimum_amount"] == source_result.required_minimum_amount
    assert issue.details["remuneration_amount"] == Decimal("1900.00")
    assert issue.details["difference_amount"] == source_result.difference_amount
    assert issue.details["source"] is expected_source
    assert issue.details["employee_id"] == employee_id
    assert issue.details["contract_id"] == contract_id
    assert issue.person_id == str(employee_id)
    assert issue.object_id == str(contract_id)
    assert compute_row_severity({"anomalies": [SALARY_MINIMUM_AUDIT_CODE]}) == ("blocking", 0)


def test_absence_de_references_acceptee_pour_anomalie():
    result = SalaryMinimumAuditService().audit(evaluate("1999.99"))
    issue = result.issues[0]
    assert result.employee_id is None
    assert result.contract_id is None
    assert issue.details["employee_id"] is None
    assert issue.details["contract_id"] is None


@pytest.mark.parametrize("bad", ["uuid", 1, True])
def test_uuid_stricts_refusent_str_int_bool(bad):
    service = SalaryMinimumAuditService()
    source_result = evaluate("2000.00")
    with pytest.raises(TypeError):
        service.audit(source_result, employee_id=bad)
    with pytest.raises(TypeError):
        service.audit(source_result, contract_id=bad)


def test_entrees_strictes_et_uuid_acceptes():
    source_result = evaluate("2000.00")
    employee_id = uuid4()
    contract_id = uuid4()
    result = SalaryMinimumAuditService().audit(source_result, employee_id=employee_id, contract_id=contract_id)
    assert result.employee_id == employee_id
    assert result.contract_id == contract_id
    assert type(result.id) is UUID
    with pytest.raises(TypeError):
        SalaryMinimumAuditService().audit("bad")


def test_coherence_resultat_audit_et_immutabilite():
    compliant = evaluate("2000.00")
    non_compliant = evaluate("1990.00")
    issue = SalaryMinimumAuditService().audit(non_compliant).issues[0]
    with pytest.raises(ValueError, match="valid"):
        SalaryMinimumAuditResult(compliant, False, ())
    with pytest.raises(ValueError, match="conforme"):
        SalaryMinimumAuditResult(compliant, True, (issue,))
    with pytest.raises(ValueError, match="exactement"):
        SalaryMinimumAuditResult(non_compliant, False, ())
    with pytest.raises(ValueError, match="dupliquée"):
        SalaryMinimumAuditResult(non_compliant, False, (issue, issue))
    with pytest.raises(TypeError):
        SalaryMinimumAuditResult(non_compliant, False, [issue])
    explicit_id = uuid4()
    assert SalaryMinimumAuditResult(non_compliant, False, (issue,), id=explicit_id).id == explicit_id
    with pytest.raises(TypeError):
        SalaryMinimumAuditResult(non_compliant, False, (issue,), id=str(explicit_id))
    with pytest.raises(FrozenInstanceError):
        issue.code = "X"
    with pytest.raises(TypeError):
        issue.details["shortfall_amount"] = Decimal("1.00")


def test_coherence_anomalie_source_deficit_source_et_references():
    non_compliant = evaluate("1990.00", ccns="1800.00", smic_amount="2000.00")
    issue = SalaryMinimumAuditService().audit(non_compliant).issues[0]
    bad_details = dict(issue.details)
    bad_details["shortfall_amount"] = Decimal("9.99")
    with pytest.raises(ValueError, match="détails"):
        SalaryMinimumAuditIssue(**kwargs(issue, details=bad_details))
    with pytest.raises(ValueError, match="résultat source"):
        SalaryMinimumAuditResult(evaluate("1990.00", ccns="1800.00", smic_amount="2000.00"), False, (issue,))
    with pytest.raises(ValueError, match="références"):
        SalaryMinimumAuditResult(non_compliant, False, (issue,), employee_id=uuid4())
    with pytest.raises(ValueError, match="résultat non conforme"):
        SalaryMinimumAuditIssue(**kwargs(issue, compliance_result=evaluate("2000.00")))


def test_statut_applicable_source_et_pas_d_anomalie_sans_deficit():
    result = evaluate("2000.00")
    assert result.status is ApplicableSalaryMinimumStatus.COMPLIANT
    with pytest.raises(ValueError, match="statut"):
        ApplicableSalaryMinimumResult(**{**{n: getattr(result, n) for n in result.__dataclass_fields__ if n != "id"}, "status": ApplicableSalaryMinimumStatus.NON_COMPLIANT})
