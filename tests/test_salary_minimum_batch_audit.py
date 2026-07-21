from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.convention import (
    ApplicableSalaryMinimumService,
    CCNSClassification,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumAuditItem,
    SalaryMinimumAuditResult,
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


def item(amount, *, employee_id=None, contract_id=None):
    return SalaryMinimumAuditItem(evaluate(amount), employee_id=employee_id, contract_id=contract_id)


def service():
    return SalaryMinimumBatchAuditService(SalaryMinimumAuditService())


def test_item_valide_references_uuid_statuts_deficit_et_immutabilite():
    employee_id = uuid4()
    contract_id = uuid4()
    compliant = SalaryMinimumAuditItem(evaluate("2000.00"), employee_id=employee_id, contract_id=contract_id)
    non_compliant = SalaryMinimumAuditItem(evaluate("1999.99"), id=uuid4())

    assert compliant.has_employee_reference()
    assert compliant.has_contract_reference()
    assert compliant.is_compliant()
    assert not compliant.is_non_compliant()
    assert compliant.shortfall_amount() == Decimal("0.00")
    assert non_compliant.employee_id is None
    assert non_compliant.contract_id is None
    assert not non_compliant.has_employee_reference()
    assert not non_compliant.has_contract_reference()
    assert non_compliant.is_non_compliant()
    assert non_compliant.shortfall_amount() == Decimal("0.01")
    assert type(compliant.id) is UUID
    with pytest.raises(FrozenInstanceError):
        compliant.employee_id = uuid4()


@pytest.mark.parametrize("bad", ["uuid", 1, True])
def test_item_refuse_uuid_invalides_et_mauvais_resultat(bad):
    result = evaluate("2000.00")
    with pytest.raises(TypeError):
        SalaryMinimumAuditItem(result, employee_id=bad)
    with pytest.raises(TypeError):
        SalaryMinimumAuditItem(result, contract_id=bad)
    with pytest.raises(TypeError):
        SalaryMinimumAuditItem(result, id=bad)
    with pytest.raises(TypeError):
        SalaryMinimumAuditItem("bad")


@pytest.mark.parametrize("factory", [tuple, list, lambda values: (value for value in values)])
def test_service_accepte_tuple_liste_generateur_et_conserve_ordre(factory):
    employee_id = uuid4()
    items = (item("2000.00", employee_id=employee_id), item("1999.00", employee_id=employee_id), item("2100.00"))

    result = service().audit(factory(items))

    assert result.items == items
    assert tuple(audit.compliance_result for audit in result.audit_results) == tuple(i.compliance_result for i in items)
    assert result.audit_results[0].is_valid()
    assert not result.audit_results[1].is_valid()
    assert result.audit_results[2].is_valid()
    assert result.issues == result.audit_results[1].issues
    assert not result.is_valid()
    assert result.has_issues()
    assert result.item_count() == 3
    assert result.issue_count() == 1
    assert result.compliant_count == 2
    assert result.non_compliant_count == 1
    assert result.total_shortfall_amount == Decimal("1.00")
    assert result.compliance_rate() == Decimal("0.6667")
    assert result.results_for_employee(employee_id) == result.audit_results[:2]
    assert result.issues_for_employee(employee_id) == result.audit_results[1].issues


def test_service_un_seul_element_conforme_et_un_seul_non_conforme():
    compliant = service().audit((item("2000.00"),))
    assert compliant.is_valid()
    assert compliant.all_compliant()
    assert not compliant.has_non_compliant_items()
    assert compliant.total_shortfall_amount == Decimal("0.00")
    assert compliant.compliance_rate() == Decimal("1.0000")

    non_compliant = service().audit((item("1900.00"),))
    assert not non_compliant.is_valid()
    assert non_compliant.has_non_compliant_items()
    assert non_compliant.compliant_count == 0
    assert non_compliant.non_compliant_count == 1
    assert non_compliant.total_shortfall_amount == Decimal("100.00")
    assert non_compliant.compliance_rate() == Decimal("0.0000")


def test_service_plusieurs_non_conformes_meme_salarie_et_meme_contrat_autorises_regroupements():
    employee_id = uuid4()
    contract_id = uuid4()
    other = uuid4()
    items = (item("1999.99", employee_id=employee_id, contract_id=contract_id), item("1999.98", employee_id=employee_id, contract_id=contract_id))

    result = service().audit(items)

    assert result.non_compliant_count == 2
    assert result.total_shortfall_amount == Decimal("0.03")
    assert result.results_for_contract(contract_id) == result.audit_results
    assert result.issues_for_contract(contract_id) == result.issues
    assert result.results_for_employee(other) == ()
    assert result.issues_for_employee(other) == ()
    assert result.results_for_contract(other) == ()
    assert result.issues_for_contract(other) == ()


def test_service_refuse_entrees_invalides_et_doublons():
    valid_item = item("2000.00")
    for bad in (None, "abc", b"abc", 123):
        with pytest.raises(TypeError):
            service().audit(bad)
    empty = service().audit(())
    assert empty.item_count() == empty.issue_count() == empty.compliant_count == empty.non_compliant_count == 0
    assert empty.total_shortfall_amount == Decimal("0.00")
    assert empty.is_valid()
    assert empty.compliance_rate() == Decimal("0.0000")
    with pytest.raises(TypeError):
        service().audit((valid_item, "bad"))
    with pytest.raises(ValueError, match="Un même résultat de conformité ne peut pas être audité plusieurs fois dans le même lot."):
        service().audit((valid_item, SalaryMinimumAuditItem(valid_item.compliance_result)))


def test_generateur_materialise_une_seule_fois_et_service_individuel_appele_une_fois_par_item(monkeypatch):
    items = (item("2000.00"), item("1999.00"))
    iter_calls = 0
    calls = []

    class SinglePass:
        def __iter__(self):
            nonlocal iter_calls
            iter_calls += 1
            if iter_calls > 1:
                raise AssertionError("itéré deux fois")
            return iter(items)

    original = SalaryMinimumAuditService.audit

    def spy(self, compliance_result, *, employee_id=None, contract_id=None):
        calls.append((compliance_result, employee_id, contract_id))
        return original(self, compliance_result, employee_id=employee_id, contract_id=contract_id)

    monkeypatch.setattr(SalaryMinimumAuditService, "audit", spy)

    result = service().audit(SinglePass())

    assert iter_calls == 1
    assert len(calls) == 2
    assert tuple(call[0] for call in calls) == tuple(i.compliance_result for i in items)
    assert result.item_count() == 2


def test_resultat_global_valide_filtre_uuid_et_refuse_incoherences():
    employee_id = uuid4()
    contract_id = uuid4()
    batch_item = item("1999.99", employee_id=employee_id, contract_id=contract_id)
    audit_result = SalaryMinimumAuditService().audit(batch_item.compliance_result, employee_id=employee_id, contract_id=contract_id)
    result = SalaryMinimumBatchAuditResult((batch_item,), (audit_result,), audit_result.issues, False, 0, 1, Decimal("0.01"), id=uuid4())

    assert type(result.id) is UUID
    assert result.results_for_employee(employee_id) == (audit_result,)
    assert result.results_for_contract(contract_id) == (audit_result,)
    with pytest.raises(TypeError):
        result.results_for_employee(str(employee_id))
    with pytest.raises(TypeError):
        result.issues_for_contract(str(contract_id))
    with pytest.raises(FrozenInstanceError):
        result.valid = True

    with pytest.raises(ValueError, match="valid"):
        SalaryMinimumBatchAuditResult((batch_item,), (audit_result,), audit_result.issues, True, 0, 1, Decimal("0.01"))
    with pytest.raises(ValueError, match="concaténation"):
        SalaryMinimumBatchAuditResult((batch_item,), (audit_result,), (), False, 0, 1, Decimal("0.01"))
    with pytest.raises(ValueError, match="total_shortfall_amount"):
        SalaryMinimumBatchAuditResult((batch_item,), (audit_result,), audit_result.issues, False, 0, 1, Decimal("0.02"))
    with pytest.raises(TypeError):
        SalaryMinimumBatchAuditResult((batch_item,), (audit_result,), audit_result.issues, False, True, 0, Decimal("0.01"))
    with pytest.raises(TypeError):
        SalaryMinimumBatchAuditResult((batch_item,), (audit_result,), audit_result.issues, False, 0, 1, Decimal("0.01"), id=str(uuid4()))


def test_constructeur_service_refuse_mauvais_service_individuel():
    with pytest.raises(TypeError):
        SalaryMinimumBatchAuditService("bad")
