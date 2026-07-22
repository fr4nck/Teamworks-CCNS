from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from application.bootstrap import ContractSalaryControlControllerFactory
from application.control import (
    ContractSalaryControlController,
    ContractSalaryControlControllerErrorCode,
    ContractSalaryControlControllerRequest,
    ContractSalaryControlControllerResult,
)
from application.presentation import ContractSalaryControlPresentationStatus
from domain.contracts import Contract, ContractSalaryControlStatus, ContractType
from domain.convention import (
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
from infrastructure.repositories import ContractRepository, ContractRepositorySalaryControlProvider

D = date(2026, 6, 1)


def group(number=1):
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def salary_grid_catalog():
    return SalaryGridCatalog((SalaryGridVersion(
        "G",
        "Grille",
        date(2026, 1, 1),
        (SalaryGridEntry(group(1), Decimal("2000.00"), SalaryMinimumPeriodicity.MONTHLY),),
    ),))


def smic_catalog():
    return SmicCatalog((SmicVersion(
        "S-M",
        "SMIC",
        SmicTerritory.METROPOLITAN_FRANCE,
        date(2026, 1, 1),
        None,
        Decimal("10.00"),
        Decimal("1800.00"),
        Decimal("35.00"),
        "test",
    ),))


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


def create_controller(repo=None, grid=None, smic=None):
    return ContractSalaryControlControllerFactory().create(
        contracts_repository=repo or ContractRepository(),
        salary_grid_catalog=grid or salary_grid_catalog(),
        smic_catalog=smic or smic_catalog(),
    )


def dependencies(controller):
    provider = controller.use_case.contract_provider
    consultation = controller.use_case.consultation_service
    control = consultation.contract_salary_control_service
    batch_audit = control.contract_salary_batch_audit_service
    batch_eval = batch_audit.contract_salary_batch_evaluation_service
    evaluation = batch_eval.contract_salary_evaluation_service
    applicable = evaluation.applicable_salary_minimum_service
    compliance = applicable.salary_minimum_compliance_service
    return provider, consultation, control, batch_audit, batch_eval, evaluation, applicable, compliance


def test_creation_reussie_type_exact_et_instances_racines_preservees():
    repo = ContractRepository()
    grid = salary_grid_catalog()
    smic = smic_catalog()
    controller = create_controller(repo, grid, smic)
    provider, _, _, _, _, _, applicable, compliance = dependencies(controller)
    assert type(controller) is ContractSalaryControlController
    assert type(provider) is ContractRepositorySalaryControlProvider
    assert provider.contracts_repository is repo
    assert compliance.salary_grid_catalog is grid
    assert applicable.smic_catalog is smic


def test_deux_controleurs_independants_sans_singleton_ni_cache_global():
    repo = ContractRepository()
    grid = salary_grid_catalog()
    smic = smic_catalog()
    first = create_controller(repo, grid, smic)
    second = create_controller(repo, grid, smic)
    assert first is not second
    assert first.use_case is not second.use_case
    assert first.presenter is not second.presenter
    for left, right in zip(dependencies(first), dependencies(second)):
        assert left is not right
    assert dependencies(first)[0].contracts_repository is repo
    assert dependencies(second)[0].contracts_repository is repo
    assert dependencies(first)[7].salary_grid_catalog is grid
    assert dependencies(second)[7].salary_grid_catalog is grid
    assert dependencies(first)[6].smic_catalog is smic
    assert dependencies(second)[6].smic_catalog is smic
    assert not hasattr(ContractSalaryControlControllerFactory, "_cache")
    assert not hasattr(first, "_cache")


@pytest.mark.parametrize("field,bad,match", [
    ("contracts_repository", object(), "ContractRepository"),
    ("salary_grid_catalog", object(), "SalaryGridCatalog"),
    ("smic_catalog", object(), "SmicCatalog"),
    ("contracts_repository", None, "ContractRepository"),
    ("salary_grid_catalog", None, "SalaryGridCatalog"),
    ("smic_catalog", None, "SmicCatalog"),
])
def test_validation_stricte_des_dependances_racines(field, bad, match):
    values = dict(
        contracts_repository=ContractRepository(),
        salary_grid_catalog=salary_grid_catalog(),
        smic_catalog=smic_catalog(),
    )
    values[field] = bad
    with pytest.raises(TypeError, match=match):
        ContractSalaryControlControllerFactory().create(**values)


def test_propage_erreur_de_construction_interne(monkeypatch):
    def broken_post_init(self):
        raise RuntimeError("invariant interne visible")

    monkeypatch.setattr(SalaryMinimumComplianceService, "__post_init__", broken_post_init)
    with pytest.raises(RuntimeError, match="invariant interne"):
        create_controller()


def test_la_fabrique_est_immutable_et_ne_lance_pas_de_controle(monkeypatch):
    factory = ContractSalaryControlControllerFactory()
    with pytest.raises((FrozenInstanceError, TypeError)):
        factory.extra = object()
    calls = []
    monkeypatch.setattr(ContractRepository, "list_all", lambda self: calls.append(self) or [])
    controller = create_controller()
    assert type(controller) is ContractSalaryControlController
    assert calls == []


def test_execution_consultation_vide_avec_controleur_construit():
    result = create_controller().execute(ContractSalaryControlControllerRequest(reference_date=D))
    assert result.successful is True
    assert result.view_model.returned_count == 0
    assert result.view_model.presentation_status is ContractSalaryControlPresentationStatus.EMPTY


def test_execution_contrat_conforme_non_conforme_et_presentation_finale():
    repo = ContractRepository()
    ok = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    ko = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    repo.add(ok)
    repo.add(ko)
    result = create_controller(repo).execute(ContractSalaryControlControllerRequest(reference_date=D))
    assert result.successful is True
    assert result.view_model.filtered_total_count == 2
    assert result.view_model.filtered_total_shortfall_amount == Decimal("10.00")
    assert result.view_model.filtered_total_shortfall_amount_label == "10,00 €"
    assert result.view_model.presentation_status is ContractSalaryControlPresentationStatus.ERROR
    assert {row.status for row in result.view_model.rows} == {
        ContractSalaryControlStatus.COMPLIANT,
        ContractSalaryControlStatus.NON_COMPLIANT,
    }


def test_erreurs_de_requete_du_controleur_fonctionnent():
    result = create_controller().execute(ContractSalaryControlControllerRequest(reference_date=D, limit=0))
    assert result.successful is False
    assert result.errors[0].code is ContractSalaryControlControllerErrorCode.INVALID_PAGINATION


def test_absence_de_mutation_des_dependances_racines():
    repo = ContractRepository()
    item = contract()
    repo.add(item)
    before_contracts = repo.list_all()
    grid = salary_grid_catalog()
    smic = smic_catalog()
    grid_versions = grid.versions
    smic_versions = smic.versions
    controller = create_controller(repo, grid, smic)
    assert repo.list_all() == before_contracts
    assert grid.versions is grid_versions
    assert smic.versions is smic_versions
    controller.execute(ContractSalaryControlControllerRequest(reference_date=D))
    assert repo.list_all() == before_contracts
    assert grid.versions is grid_versions
    assert smic.versions is smic_versions


def test_integration_appelant_assemble_uniquement_repository_catalogues_et_fabrique():
    repo = ContractRepository()
    item = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    repo.add(item)
    result = ContractSalaryControlControllerFactory().create(
        contracts_repository=repo,
        salary_grid_catalog=salary_grid_catalog(),
        smic_catalog=smic_catalog(),
    ).execute(ContractSalaryControlControllerRequest(reference_date=D, contract_ids=(item.id,)))
    assert type(result) is ContractSalaryControlControllerResult
    assert result.successful is True
    assert result.view_model.rows[0].contract_id == item.id
    assert result.view_model.rows[0].employee_id == UUID(item.person_id)
    assert result.view_model.rows[0].status is ContractSalaryControlStatus.NON_COMPLIANT
    assert result.view_model.rows[0].remuneration_amount == Decimal("1990.00")
    assert result.view_model.rows[0].applicable_minimum_amount == Decimal("2000.00")
    assert result.view_model.rows[0].shortfall_amount == Decimal("10.00")
