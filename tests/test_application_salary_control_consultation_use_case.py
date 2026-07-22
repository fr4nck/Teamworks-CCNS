from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from application.control import (
    ConsultContractSalaryControlQuery,
    ConsultContractSalaryControlUseCase,
    ContractSalaryControlConsultationApplicationResult,
)
from domain.contracts import (
    Contract,
    ContractSalaryBatchAuditService,
    ContractSalaryBatchEvaluationService,
    ContractSalaryControlConsultationService,
    ContractSalaryControlProjectionService,
    ContractSalaryControlQuery,
    ContractSalaryControlQueryService,
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


def consultation_service():
    grid = SalaryGridVersion(
        "G",
        "Grille",
        date(2026, 1, 1),
        (SalaryGridEntry(group(1), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),),
    )
    smics = (
        SmicVersion("S-M", "SMIC", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, Decimal("10.00"), Decimal("1800.00"), Decimal("35.00"), "test"),
        SmicVersion("S-Y", "SMIC", SmicTerritory.MAYOTTE, date(2026, 1, 1), None, Decimal("10.00"), Decimal("1500.00"), Decimal("35.00"), "test"),
    )
    engine = ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid,))), SmicCatalog(smics))
    control = ContractSalaryControlService(
        ContractSalaryBatchAuditService(
            ContractSalaryBatchEvaluationService(ContractSalaryEvaluationService(engine)),
            SalaryMinimumBatchAuditService(SalaryMinimumAuditService()),
        ),
        ContractSalaryControlProjectionService(),
    )
    return ContractSalaryControlConsultationService(control, ContractSalaryControlQueryService())


def contract(**overrides):
    data = dict(
        id=uuid4(),
        person_id=str(uuid4()),
        contract_type=ContractType.CDI,
        start_date=date(2026, 1, 1),
        ccns_classification=group(1),
        monthly_gross_salary_amount=Decimal("2100.00"),
        salary_unit="monthly",
        weekly_hours=Decimal("35.00"),
        smic_territory=SmicTerritory.METROPOLITAN_FRANCE,
    )
    data.update(overrides)
    return Contract(**data)


class Provider:
    def __init__(self, contracts):
        self.contracts = contracts
        self.calls = []

    def list_for_salary_control(self, *, contract_ids=(), employee_ids=()):
        self.calls.append((contract_ids, employee_ids))
        if contract_ids or employee_ids:
            return (
                item
                for item in self.contracts
                if (not contract_ids or item.id in contract_ids)
                and (not employee_ids or UUID(item.person_id) in employee_ids)
            )
        return (item for item in self.contracts)


def execute(contracts, query=None):
    provider = Provider(contracts)
    result = ConsultContractSalaryControlUseCase(provider, consultation_service()).execute(
        query or ConsultContractSalaryControlQuery(reference_date=D)
    )
    return provider, result


def ids(result):
    return [row.contract_id for row in result.rows]


def test_consultation_vide():
    provider, result = execute([])
    assert provider.calls == [((), ())]
    assert result.reference_date == D
    assert result.global_total_count == result.filtered_total_count == result.returned_count == 0
    assert result.rows == ()
    assert result.filtered_total_shortfall_amount == Decimal("0.00")
    assert result.global_valid is True and result.filtered_valid is True
    assert result.has_next_page is False and result.has_previous_page is False


def test_lot_conforme_non_conforme_non_evaluable_sans_recalcul():
    ok = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    ko = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    failed = contract(smic_territory=None)
    _, result = execute([ok, ko, failed])
    assert [row.status for row in result.rows] == [
        ContractSalaryControlStatus.COMPLIANT,
        ContractSalaryControlStatus.NON_COMPLIANT,
        ContractSalaryControlStatus.NOT_EVALUATED,
    ]
    assert result.global_total_count == result.filtered_total_count == result.returned_count == 3
    assert result.global_compliant_count == result.filtered_compliant_count == 1
    assert result.global_non_compliant_count == result.filtered_non_compliant_count == 1
    assert result.global_not_evaluated_count == result.filtered_not_evaluated_count == 1
    assert result.filtered_total_shortfall_amount == Decimal("10.00")
    assert result.global_valid is False and result.filtered_valid is False
    assert type(result.filtered_total_shortfall_amount) is Decimal


def test_transmet_date_territoire_selection_et_appelle_consult_une_fois(monkeypatch):
    ok = contract()
    selected = (ok.id,)
    employees = (UUID(ok.person_id),)
    provider = Provider([ok])
    service = consultation_service()
    calls = []
    original = ContractSalaryControlConsultationService.consult

    def counted(self, contracts, reference_date, query, *, territory=None):
        materialized = tuple(contracts)
        calls.append((materialized, reference_date, query, territory))
        return original(self, materialized, reference_date, query, territory=territory)

    monkeypatch.setattr(ContractSalaryControlConsultationService, "consult", counted)
    app_query = ConsultContractSalaryControlQuery(
        reference_date=D,
        territory=SmicTerritory.MAYOTTE,
        contract_ids=selected,
        employee_ids=employees,
    )
    result = ConsultContractSalaryControlUseCase(provider, service).execute(app_query)
    assert len(calls) == 1
    contracts, reference_date, domain_query, territory = calls[0]
    assert contracts == (ok,)
    assert reference_date is D
    assert territory is SmicTerritory.MAYOTTE
    assert domain_query.contract_ids == selected and domain_query.employee_ids == employees
    assert provider.calls == [(selected, employees)]
    assert result.reference_date is D


def test_filtres_tri_pagination_validite_globale_distincte_validite_filtree_et_ordre():
    ok = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    ko_high = contract(monthly_gross_salary_amount=Decimal("1980.00"))
    ko_low = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    failed = contract(smic_territory=None)
    query = ConsultContractSalaryControlQuery(
        reference_date=D,
        statuses=(ContractSalaryControlStatus.COMPLIANT,),
        search_text="G1",
        minimum_shortfall_amount=Decimal("0.00"),
        maximum_shortfall_amount=Decimal("0.00"),
        sort_field=ContractSalaryControlSortField.CONTRACT_ID,
        sort_direction=SortDirection.DESCENDING,
        offset=0,
        limit=2,
    )
    _, filtered = execute([ok, ko_high, ko_low, failed], query)
    assert ids(filtered) == sorted([ok.id], reverse=True)
    assert filtered.global_total_count == 4
    assert filtered.filtered_total_count == filtered.returned_count == 1
    assert filtered.global_valid is False
    assert filtered.filtered_valid is True
    assert filtered.filtered_total_shortfall_amount == Decimal("0.00")

    page_query = ConsultContractSalaryControlQuery(
        reference_date=D,
        statuses=(ContractSalaryControlStatus.NON_COMPLIANT,),
        sort_field=ContractSalaryControlSortField.SHORTFALL_AMOUNT,
        sort_direction=SortDirection.DESCENDING,
        offset=1,
        limit=1,
    )
    _, page = execute([ok, ko_high, ko_low, failed], page_query)
    assert ids(page) == [ko_low.id]
    assert page.filtered_total_count == 2 and page.returned_count == 1
    assert page.has_previous_page is True and page.has_next_page is False
    assert page.previous_offset == 0 and page.next_offset is None
    assert page.filtered_total_shortfall_amount == Decimal("30.00")


def test_requete_construit_la_requete_domaine_sans_dupliquer_ses_validations():
    q = ConsultContractSalaryControlQuery(reference_date=D, minimum_shortfall_amount=Decimal("1.001"))
    with pytest.raises(ValueError, match="quantifié"):
        q.to_domain_query()
    with pytest.raises(ValueError, match="offset"):
        ConsultContractSalaryControlQuery(reference_date=D, offset=-1).to_domain_query()


def test_validations_types_immutabilite_commande_resultat_et_resultat_domaine():
    with pytest.raises(TypeError):
        ConsultContractSalaryControlQuery(reference_date=datetime(2026, 6, 1))
    with pytest.raises(TypeError):
        ConsultContractSalaryControlQuery(reference_date=D, territory="bad")
    with pytest.raises(TypeError):
        ConsultContractSalaryControlQuery(reference_date=D, contract_ids=(str(uuid4()),))
    with pytest.raises(TypeError):
        ConsultContractSalaryControlQuery(reference_date=D, statuses=("bad",))
    with pytest.raises(TypeError):
        ConsultContractSalaryControlQuery(reference_date=D, minimum_shortfall_amount=1.0)
    with pytest.raises(TypeError):
        ConsultContractSalaryControlQuery(reference_date=D, sort_field="bad")
    with pytest.raises(TypeError):
        ConsultContractSalaryControlQuery(reference_date=D, limit="bad")
    with pytest.raises(TypeError):
        ConsultContractSalaryControlUseCase(object(), consultation_service())
    with pytest.raises(TypeError):
        ConsultContractSalaryControlUseCase(Provider([]), object())
    with pytest.raises(TypeError):
        ConsultContractSalaryControlUseCase(Provider([]), consultation_service()).execute(ContractSalaryControlQuery())
    with pytest.raises(TypeError):
        ContractSalaryControlConsultationApplicationResult.from_domain(object())

    query = ConsultContractSalaryControlQuery(reference_date=D)
    _, result = execute([contract()])
    with pytest.raises(FrozenInstanceError):
        query.offset = 1
    with pytest.raises(FrozenInstanceError):
        result.returned_count = 99


def test_propage_les_erreurs_techniques_des_dependances(monkeypatch):
    class BrokenProvider:
        def list_for_salary_control(self, *, contract_ids=(), employee_ids=()):
            raise RuntimeError("stockage indisponible")

    with pytest.raises(RuntimeError, match="stockage"):
        ConsultContractSalaryControlUseCase(BrokenProvider(), consultation_service()).execute(
            ConsultContractSalaryControlQuery(reference_date=D)
        )

    def broken_consult(self, contracts, reference_date, query, *, territory=None):
        raise RuntimeError("moteur indisponible")

    monkeypatch.setattr(ContractSalaryControlConsultationService, "consult", broken_consult)
    with pytest.raises(RuntimeError, match="moteur"):
        ConsultContractSalaryControlUseCase(Provider([contract()]), consultation_service()).execute(
            ConsultContractSalaryControlQuery(reference_date=D)
        )
