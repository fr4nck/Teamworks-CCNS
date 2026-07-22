from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from application.control import ConsultContractSalaryControlQuery, ConsultContractSalaryControlUseCase
from domain.contracts import (
    Contract,
    ContractSalaryBatchAuditService,
    ContractSalaryBatchEvaluationService,
    ContractSalaryControlConsultationService,
    ContractSalaryControlProjectionService,
    ContractSalaryControlQueryService,
    ContractSalaryControlService,
    ContractType,
    ContractSalaryEvaluationService,
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
from infrastructure.repositories import ContractRepository, ContractRepositorySalaryControlProvider

D = date(2026, 6, 1)


def group(number=1):
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


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


def repository_with(*contracts):
    repo = ContractRepository()
    for item in contracts:
        repo.add(item)
    return repo


def provider_with(*contracts):
    return ContractRepositorySalaryControlProvider(repository_with(*contracts))


def listed(provider, **filters):
    return list(provider.list_for_salary_control(**filters))


def consultation_service():
    grid = SalaryGridVersion(
        "G",
        "Grille",
        date(2026, 1, 1),
        (SalaryGridEntry(group(1), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),),
    )
    smics = (SmicVersion("S-M", "SMIC", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, Decimal("10.00"), Decimal("1800.00"), Decimal("35.00"), "test"),)
    engine = ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog((grid,))), SmicCatalog(smics))
    control = ContractSalaryControlService(
        ContractSalaryBatchAuditService(
            ContractSalaryBatchEvaluationService(ContractSalaryEvaluationService(engine)),
            SalaryMinimumBatchAuditService(SalaryMinimumAuditService()),
        ),
        ContractSalaryControlProjectionService(),
    )
    return ContractSalaryControlConsultationService(control, ContractSalaryControlQueryService())


def test_repository_vide():
    assert listed(provider_with()) == []


def test_recupere_tous_les_contrats_sans_filtre_en_preservant_ordre_et_instances():
    first, second, third = contract(), contract(), contract()
    result = listed(provider_with(first, second, third))
    assert result == [first, second, third]
    assert result[0] is first and result[1] is second and result[2] is third


def test_filtre_par_un_identifiant_de_contrat():
    first, second = contract(), contract()
    assert listed(provider_with(first, second), contract_ids=(second.id,)) == [second]


def test_filtre_par_plusieurs_identifiants_de_contrats_dans_l_ordre_du_depot():
    first, second, third = contract(), contract(), contract()
    result = listed(provider_with(first, second, third), contract_ids=(third.id, first.id))
    assert result == [first, third]


def test_filtre_par_un_identifiant_de_salarie():
    employee_id = uuid4()
    first = contract(person_id=str(employee_id))
    second = contract()
    assert listed(provider_with(first, second), employee_ids=(employee_id,)) == [first]


def test_filtre_par_plusieurs_salaries():
    employee_a, employee_b = uuid4(), uuid4()
    first = contract(person_id=str(employee_a))
    second = contract()
    third = contract(person_id=str(employee_b))
    assert listed(provider_with(first, second, third), employee_ids=(employee_b, employee_a)) == [first, third]


def test_intersection_contract_ids_et_employee_ids():
    employee_a, employee_b = uuid4(), uuid4()
    first = contract(person_id=str(employee_a))
    second = contract(person_id=str(employee_b))
    third = contract(person_id=str(employee_a))
    result = listed(provider_with(first, second, third), contract_ids=(second.id, third.id), employee_ids=(employee_a,))
    assert result == [third]


def test_identifiants_sans_correspondance_retournent_vide():
    assert listed(provider_with(contract()), contract_ids=(uuid4(),), employee_ids=(uuid4(),)) == []


def test_absence_de_doublons_meme_si_le_depot_contient_deux_fois_le_meme_contrat():
    item = contract()
    repo = ContractRepository()
    repo.replace_all((item, item))
    assert listed(ContractRepositorySalaryControlProvider(repo), contract_ids=(item.id,)) == [item]


def test_appel_unique_a_list_all(monkeypatch):
    repo = repository_with(contract(), contract())
    provider = ContractRepositorySalaryControlProvider(repo)
    calls = 0
    original = repo.list_all

    def counted():
        nonlocal calls
        calls += 1
        return original()

    monkeypatch.setattr(repo, "list_all", counted)
    listed(provider, contract_ids=(uuid4(),))
    assert calls == 1


def test_validations_strictes_repository_tuples_uuid_et_doublons():
    item = contract()
    provider = provider_with(item)
    with pytest.raises(TypeError, match="ContractRepository"):
        ContractRepositorySalaryControlProvider(object())
    with pytest.raises(TypeError, match="tuple"):
        listed(provider, contract_ids=[item.id])
    with pytest.raises(TypeError, match="UUID"):
        listed(provider, contract_ids=(str(item.id),))
    with pytest.raises(TypeError, match="UUID"):
        listed(provider, employee_ids=(str(uuid4()),))
    with pytest.raises(ValueError, match="doublons"):
        listed(provider, contract_ids=(item.id, item.id))
    employee_id = UUID(item.person_id)
    with pytest.raises(ValueError, match="doublons"):
        listed(provider, employee_ids=(employee_id, employee_id))


def test_frontiere_conversion_historique_explicite_et_erreurs_documentees():
    contract_id = uuid4()
    employee_id = uuid4()
    item = contract(id=str(contract_id), person_id=str(employee_id))
    assert listed(provider_with(item), contract_ids=(contract_id,), employee_ids=(employee_id,)) == [item]
    with pytest.raises(ValueError, match="contrat"):
        listed(provider_with(contract(id="contrat-historique")), contract_ids=(uuid4(),))
    with pytest.raises(ValueError, match="salarié"):
        listed(provider_with(contract(person_id="personne-historique")), employee_ids=(uuid4(),))


def test_adaptateur_immuable_et_sans_etat_mutable():
    provider = provider_with(contract())
    with pytest.raises(FrozenInstanceError):
        provider.contracts_repository = ContractRepository()
    assert not hasattr(provider, "_cache")


def test_integration_use_case_sur_lot_minimal():
    ok = contract()
    ko = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    provider = provider_with(ok, ko)
    result = ConsultContractSalaryControlUseCase(provider, consultation_service()).execute(
        ConsultContractSalaryControlQuery(reference_date=D, contract_ids=(ko.id,))
    )
    assert result.global_total_count == 1
    assert result.rows[0].contract_id == ko.id


def test_propage_les_erreurs_du_repository(monkeypatch):
    repo = ContractRepository()
    provider = ContractRepositorySalaryControlProvider(repo)

    def broken():
        raise RuntimeError("stockage indisponible")

    monkeypatch.setattr(repo, "list_all", broken)
    with pytest.raises(RuntimeError, match="stockage"):
        listed(provider)
