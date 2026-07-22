from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.contracts import (
    Contract,
    ContractSalaryBatchAuditService,
    ContractSalaryBatchEvaluationService,
    ContractSalaryControlConsultationResult,
    ContractSalaryControlConsultationService,
    ContractSalaryControlPage,
    ContractSalaryControlProjection,
    ContractSalaryControlProjectionService,
    ContractSalaryControlQuery,
    ContractSalaryControlQueryService,
    ContractSalaryControlResult,
    ContractSalaryControlService,
    ContractSalaryControlSortField,
    ContractSalaryControlStatus,
    ContractSalaryEvaluationService,
    ContractType,
    SortDirection,
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

D = date(2026, 6, 1)


def group(number=1):
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def service():
    grid = SalaryGridVersion("G", "Grille", date(2026, 1, 1), (SalaryGridEntry(group(1), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),))
    smics = (SmicVersion("S-M", "SMIC", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, Decimal("10.00"), Decimal("1800.00"), Decimal("35.00"), "test"), SmicVersion("S-Y", "SMIC", SmicTerritory.MAYOTTE, date(2026, 1, 1), None, Decimal("10.00"), Decimal("1500.00"), Decimal("35.00"), "test"))
    engine = ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid,))), SmicCatalog(smics))
    control = ContractSalaryControlService(ContractSalaryBatchAuditService(ContractSalaryBatchEvaluationService(ContractSalaryEvaluationService(engine)), SalaryMinimumBatchAuditService(SalaryMinimumAuditService())), ContractSalaryControlProjectionService())
    return ContractSalaryControlConsultationService(control, ContractSalaryControlQueryService())


def contract(**overrides):
    data = dict(id=uuid4(), person_id=str(uuid4()), contract_type=ContractType.CDI, start_date=date(2026, 1, 1), ccns_classification=group(1), monthly_gross_salary_amount=Decimal("2100.00"), salary_unit="monthly", weekly_hours=Decimal("35.00"), smic_territory=SmicTerritory.METROPOLITAN_FRANCE)
    data.update(overrides)
    return Contract(**data)


def consult(contracts, query=ContractSalaryControlQuery(), *, territory=None):
    return service().consult(contracts, D, query, territory=territory)


def ids(result):
    return [row.contract_id for row in result.rows]


def test_lot_vide_requete_defaut():
    result = consult([])
    assert result.total_source_count == result.total_filtered_count == result.returned_count == 0
    assert result.rows == result.filtered_rows == ()
    assert result.total_shortfall_amount == Decimal("0.00")
    assert type(result.total_shortfall_amount) is Decimal
    assert result.valid is True and result.is_empty is True
    assert result.has_next_page is False and result.has_previous_page is False
    assert result.next_offset is None and result.previous_offset is None


def test_lots_conforme_non_conforme_non_evalue_melange_et_delegations():
    employee = str(uuid4())
    ok = contract(person_id=employee, monthly_gross_salary_amount=Decimal("2100.00"))
    ko = contract(person_id=employee, monthly_gross_salary_amount=Decimal("1990.00"))
    failed = contract(smic_territory=None)
    result = consult([ok, ko, failed])
    assert [r.status for r in result.rows] == [ContractSalaryControlStatus.COMPLIANT, ContractSalaryControlStatus.NON_COMPLIANT, ContractSalaryControlStatus.NOT_EVALUATED]
    assert result.total_source_count == result.total_filtered_count == result.returned_count == 3
    assert result.compliant_count == result.non_compliant_count == result.not_evaluated_count == 1
    assert result.total_shortfall_amount == Decimal("10.00")
    assert result.valid is False and result.control_result.valid is False
    assert result.row_for_contract(ko.id) is result.rows[1]
    assert result.rows_for_employee(UUID(employee)) == (result.rows[0], result.rows[1])
    assert result.rows_for_status(ContractSalaryControlStatus.NON_COMPLIANT) == (result.rows[1],)


def test_requetes_filtres_tri_pagination_et_validite_filtree():
    ok = contract(ccns_classification=group(1), monthly_gross_salary_amount=Decimal("2100.00"))
    ko = contract(ccns_classification=group(1), monthly_gross_salary_amount=Decimal("1990.00"))
    failed = contract(smic_territory=None)
    by_status = consult([ok, ko, failed], ContractSalaryControlQuery(statuses=(ContractSalaryControlStatus.NON_COMPLIANT,)))
    assert ids(by_status) == [ko.id]
    assert by_status.total_source_count == 3 and by_status.total_filtered_count == 1
    assert by_status.non_compliant_count == 1 and by_status.total_shortfall_amount == Decimal("10.00") and by_status.valid is False
    by_employee = consult([ok, ko, failed], ContractSalaryControlQuery(employee_ids=(UUID(ok.person_id),)))
    assert ids(by_employee) == [ok.id]
    by_contract = consult([ok, ko, failed], ContractSalaryControlQuery(contract_ids=(failed.id,)))
    assert ids(by_contract) == [failed.id]
    sorted_page = consult([ok, ko, failed], ContractSalaryControlQuery(sort_field=ContractSalaryControlSortField.CONTRACT_ID))
    assert ids(sorted_page) == sorted([ok.id, ko.id, failed.id])
    p = consult([ok, ko, failed], ContractSalaryControlQuery(sort_direction=SortDirection.ASCENDING, offset=1, limit=1))
    assert p.rows == (p.filtered_rows[1],) and p.has_next_page is True and p.has_previous_page is True
    assert p.next_offset == 2 and p.previous_offset == 0
    empty = consult([ok, ko], ContractSalaryControlQuery(statuses=(ContractSalaryControlStatus.NOT_EVALUATED,)))
    assert empty.total_source_count == 2 and empty.total_filtered_count == empty.returned_count == 0
    assert empty.valid is True and empty.total_shortfall_amount == Decimal("0.00")
    assert empty.control_result.valid is False


def test_ordre_appels_identites_iterable_reference_territory_query_projection_lignes(monkeypatch):
    calls = []
    captured = {}
    original_control = ContractSalaryControlService.control
    original_execute = ContractSalaryControlQueryService.execute

    def counted_control(self, contracts, reference_date, *, territory=None):
        calls.append("control")
        captured["contracts"] = contracts
        captured["reference_date"] = reference_date
        captured["territory"] = territory
        result = original_control(self, contracts, reference_date, territory=territory)
        captured["control_result"] = result
        return result

    def counted_execute(self, projection, query):
        calls.append("execute")
        assert projection is captured["control_result"].projection
        captured["query"] = query
        page = original_execute(self, projection, query)
        captured["page"] = page
        return page

    monkeypatch.setattr(ContractSalaryControlService, "control", counted_control)
    monkeypatch.setattr(ContractSalaryControlQueryService, "execute", counted_execute)
    contracts = [contract(smic_territory=None)]
    query = ContractSalaryControlQuery()
    result = service().consult(contracts, D, query, territory=SmicTerritory.MAYOTTE)
    assert calls == ["control", "execute"]
    assert captured["contracts"] is contracts and captured["reference_date"] is D and captured["territory"] is SmicTerritory.MAYOTTE
    assert captured["query"] is query and result.query is query
    assert result.control_result is captured["control_result"] and result.page is captured["page"]
    assert result.source_projection is result.control_result.projection
    assert result.rows[0] is result.control_result.projection.rows[0]


def test_generateur_consomme_une_seule_fois():
    contracts = [contract(), contract(monthly_gross_salary_amount=Decimal("1999.00"))]
    iterations = 0

    def gen():
        nonlocal iterations
        for item in contracts:
            iterations += 1
            yield item

    result = consult(gen())
    assert iterations == 2 and result.total_source_count == 2


def test_types_services_entrees_retours_uuid_immutabilite(monkeypatch):
    with pytest.raises(TypeError):
        ContractSalaryControlConsultationService("bad", ContractSalaryControlQueryService())
    with pytest.raises(TypeError):
        ContractSalaryControlConsultationService(service().contract_salary_control_service, "bad")
    with pytest.raises(TypeError):
        service().consult([contract()], datetime(2026, 6, 1), ContractSalaryControlQuery())
    with pytest.raises(TypeError):
        service().consult([contract()], D, "bad")
    with pytest.raises(TypeError):
        service().consult([contract()], D, ContractSalaryControlQuery(), territory="bad")
    valid = consult([contract()])
    with pytest.raises(TypeError):
        ContractSalaryControlConsultationResult("bad", valid.page)
    with pytest.raises(TypeError):
        ContractSalaryControlConsultationResult(valid.control_result, "bad")
    with pytest.raises(TypeError):
        ContractSalaryControlConsultationResult(valid.control_result, valid.page, id=str(uuid4()))
    with pytest.raises(FrozenInstanceError):
        valid.id = uuid4()

    monkeypatch.setattr(ContractSalaryControlService, "control", lambda *a, **k: "bad")
    with pytest.raises(TypeError):
        consult([contract()])
    monkeypatch.undo()
    monkeypatch.setattr(ContractSalaryControlQueryService, "execute", lambda *a, **k: "bad")
    with pytest.raises(TypeError):
        consult([contract()])


def test_incoherences_resultat_composite_refusees():
    valid = consult([contract(), contract(monthly_gross_salary_amount=Decimal("1990.00"))])
    other = ContractSalaryControlProjection(valid.reference_date, valid.control_result.projection.rows)
    with pytest.raises(ValueError, match="projection"):
        ContractSalaryControlConsultationResult(valid.control_result, replace(valid.page, source_projection=other))
    with pytest.raises(ValueError, match="total_source_count"):
        ContractSalaryControlConsultationResult(valid.control_result, replace(valid.page, total_source_count=99))
    foreign = replace(valid.rows[0], id=uuid4())
    with pytest.raises(ValueError, match="filtered_rows"):
        ContractSalaryControlConsultationResult(valid.control_result, replace(valid.page, filtered_rows=(foreign,), rows=(foreign,), total_filtered_count=1))
    with pytest.raises(ValueError, match="rows"):
        ContractSalaryControlConsultationResult(valid.control_result, replace(valid.page, rows=(foreign,)))
    with pytest.raises(ValueError, match="ordre"):
        ContractSalaryControlConsultationResult(valid.control_result, replace(valid.page, rows=tuple(reversed(valid.rows))))
    dup_page = replace(valid.page, filtered_rows=(valid.rows[0], valid.rows[0]), rows=(valid.rows[0], valid.rows[0]), total_filtered_count=2)
    with pytest.raises(ValueError, match="doublon"):
        ContractSalaryControlConsultationResult(valid.control_result, dup_page)


def test_aucune_instance_source_modifiee():
    result = consult([contract(), contract(monthly_gross_salary_amount=Decimal("1990.00"))], ContractSalaryControlQuery(limit=1))
    before = (result.control_result.batch_audit_result.evaluations, result.control_result.batch_audit_result.audit_results, result.source_projection.rows)
    assert result.filtered_rows and result.rows
    after = (result.control_result.batch_audit_result.evaluations, result.control_result.batch_audit_result.audit_results, result.source_projection.rows)
    assert after == before
