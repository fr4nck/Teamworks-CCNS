from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from application.control import (
    ConsultContractSalaryControlQuery,
    ConsultContractSalaryControlUseCase,
    ContractSalaryControlController,
    ContractSalaryControlControllerError,
    ContractSalaryControlControllerErrorCode,
    ContractSalaryControlControllerRequest,
    ContractSalaryControlControllerResult,
)
from application.presentation import ContractSalaryControlPresenter, ContractSalaryControlViewModel
from domain.contracts import ContractSalaryControlSortField, ContractSalaryControlStatus, SortDirection
from domain.convention.smic import SmicTerritory
from tests.test_application_salary_control_consultation_use_case import contract, consultation_service

D = date(2026, 6, 1)


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


def controller(contracts):
    provider = Provider(contracts)
    return provider, ContractSalaryControlController(
        ConsultContractSalaryControlUseCase(provider, consultation_service()),
        ContractSalaryControlPresenter(),
    )


def request(**overrides):
    data = dict(reference_date=D)
    data.update(overrides)
    return ContractSalaryControlControllerRequest(**data)


def assert_request_error(result, code):
    assert result.successful is False
    assert result.view_model is None
    assert len(result.errors) == 1
    assert result.errors[0].code is code
    assert result.errors[0].message
    assert result.errors[0].technical_error_type in {"TypeError", "ValueError"}


def test_consultation_vide_reussie_et_view_model_conserve(monkeypatch):
    _, ctl = controller([])
    presented = []
    original = ContractSalaryControlPresenter.present

    def counted(self, result):
        view_model = original(self, result)
        presented.append(view_model)
        return view_model

    monkeypatch.setattr(ContractSalaryControlPresenter, "present", counted)
    result = ctl.execute(request())
    assert result.successful is True
    assert result.errors == ()
    assert result.view_model is presented[0]
    assert result.view_model.empty_state is not None
    assert result.view_model.returned_count == 0


def test_consultation_avec_resultats_conformes_et_non_conformes():
    ok = contract(monthly_gross_salary_amount=Decimal("2100.00"))
    ko = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    _, ctl = controller([ok, ko])
    result = ctl.execute(request(sort_field=ContractSalaryControlSortField.CONTRACT_ID))
    assert result.successful is True
    assert result.view_model.filtered_total_count == 2
    assert {row.status for row in result.view_model.rows} == {
        ContractSalaryControlStatus.COMPLIANT,
        ContractSalaryControlStatus.NON_COMPLIANT,
    }
    assert result.view_model.filtered_valid is False


def test_transmission_exacte_de_tous_les_criteres_et_appels_uniques(monkeypatch):
    ok = contract()
    selected = (ok.id,)
    employees = (UUID(ok.person_id),)
    provider, ctl = controller([ok])
    use_case_calls = []
    presenter_calls = []
    original_execute = ConsultContractSalaryControlUseCase.execute
    original_present = ContractSalaryControlPresenter.present

    def counted_execute(self, query):
        use_case_calls.append(query)
        return original_execute(self, query)

    def counted_present(self, result):
        presenter_calls.append(result)
        return original_present(self, result)

    monkeypatch.setattr(ConsultContractSalaryControlUseCase, "execute", counted_execute)
    monkeypatch.setattr(ContractSalaryControlPresenter, "present", counted_present)
    result = ctl.execute(request(
        territory=SmicTerritory.MAYOTTE,
        contract_ids=selected,
        employee_ids=employees,
        statuses=(ContractSalaryControlStatus.COMPLIANT,),
        search_text="G1",
        minimum_shortfall_amount=Decimal("0.00"),
        maximum_shortfall_amount=Decimal("0.00"),
        sort_field=ContractSalaryControlSortField.SHORTFALL_AMOUNT,
        sort_direction=SortDirection.DESCENDING,
        offset=0,
        limit=5,
    ))
    assert result.successful is True
    assert len(use_case_calls) == 1
    assert len(presenter_calls) == 1
    q = use_case_calls[0]
    assert type(q) is ConsultContractSalaryControlQuery
    assert q.reference_date is D
    assert q.territory is SmicTerritory.MAYOTTE
    assert q.contract_ids == selected and q.employee_ids == employees
    assert q.statuses == (ContractSalaryControlStatus.COMPLIANT,)
    assert q.search_text == "G1"
    assert q.minimum_shortfall_amount == Decimal("0.00")
    assert q.maximum_shortfall_amount == Decimal("0.00")
    assert q.sort_field is ContractSalaryControlSortField.SHORTFALL_AMOUNT
    assert q.sort_direction is SortDirection.DESCENDING
    assert q.offset == 0 and q.limit == 5
    assert provider.calls == [(selected, employees)]


@pytest.mark.parametrize("kwargs, code", [
    ({"reference_date": datetime(2026, 6, 1)}, ContractSalaryControlControllerErrorCode.INVALID_REFERENCE_DATE),
    ({"contract_ids": (str(uuid4()),)}, ContractSalaryControlControllerErrorCode.INVALID_CONTRACT_IDS),
    ({"employee_ids": (str(uuid4()),)}, ContractSalaryControlControllerErrorCode.INVALID_EMPLOYEE_IDS),
    ({"contract_ids": (UUID('00000000-0000-0000-0000-000000000001'), UUID('00000000-0000-0000-0000-000000000001'))}, ContractSalaryControlControllerErrorCode.INVALID_CONTRACT_IDS),
    ({"employee_ids": (UUID('10000000-0000-0000-0000-000000000001'), UUID('10000000-0000-0000-0000-000000000001'))}, ContractSalaryControlControllerErrorCode.INVALID_EMPLOYEE_IDS),
    ({"statuses": ("bad",)}, ContractSalaryControlControllerErrorCode.INVALID_STATUSES),
    ({"minimum_shortfall_amount": Decimal("1.001")}, ContractSalaryControlControllerErrorCode.INVALID_SHORTFALL_RANGE),
    ({"minimum_shortfall_amount": Decimal("2.00"), "maximum_shortfall_amount": Decimal("1.00")}, ContractSalaryControlControllerErrorCode.INVALID_SHORTFALL_RANGE),
    ({"sort_field": "bad"}, ContractSalaryControlControllerErrorCode.INVALID_SORT),
    ({"sort_direction": "bad"}, ContractSalaryControlControllerErrorCode.INVALID_SORT),
    ({"offset": -1}, ContractSalaryControlControllerErrorCode.INVALID_PAGINATION),
    ({"limit": 0}, ContractSalaryControlControllerErrorCode.INVALID_PAGINATION),
    ({"search_text": "   "}, ContractSalaryControlControllerErrorCode.INVALID_SEARCH_TEXT),
])
def test_erreurs_de_requete_attendues_sans_appel_presentateur(monkeypatch, kwargs, code):
    _, ctl = controller([contract()])
    presenter_calls = []
    monkeypatch.setattr(ContractSalaryControlPresenter, "present", lambda self, result: presenter_calls.append(result))
    result = ctl.execute(request(**kwargs))
    assert_request_error(result, code)
    assert presenter_calls == []


def test_first_page_retourne_une_nouvelle_requete_immutable():
    original = request(offset=40, limit=20, search_text="G1")
    reset = original.first_page()
    assert reset is not original
    assert original.offset == 40
    assert reset.offset == 0 and reset.limit == 20 and reset.search_text == "G1"


def test_invariants_et_immutabilite_des_modeles_controller():
    _, ctl = controller([])
    success = ctl.execute(request())
    error = ContractSalaryControlControllerError(
        ContractSalaryControlControllerErrorCode.INVALID_REQUEST,
        None,
        "Demande invalide.",
    )
    with pytest.raises(FrozenInstanceError):
        success.successful = False
    with pytest.raises(FrozenInstanceError):
        error.message = "x"
    with pytest.raises(FrozenInstanceError):
        request().offset = 1
    with pytest.raises(ValueError):
        ContractSalaryControlControllerResult(True, success.view_model, (error,))
    with pytest.raises(ValueError):
        ContractSalaryControlControllerResult(True, None, ())
    with pytest.raises(ValueError):
        ContractSalaryControlControllerResult(False, success.view_model, (error,))
    with pytest.raises(ValueError):
        ContractSalaryControlControllerResult(False, None, ())
    with pytest.raises(TypeError):
        ContractSalaryControlControllerResult(True, object(), ())


def test_propage_erreurs_repository_et_service_salarial(monkeypatch):
    class BrokenProvider:
        def list_for_salary_control(self, *, contract_ids=(), employee_ids=()):
            raise RuntimeError("repository indisponible")

    bad_repository = ContractSalaryControlController(
        ConsultContractSalaryControlUseCase(BrokenProvider(), consultation_service()),
        ContractSalaryControlPresenter(),
    )
    with pytest.raises(RuntimeError, match="repository"):
        bad_repository.execute(request())

    def broken_consult(self, contracts, reference_date, query, *, territory=None):
        raise RuntimeError("moteur salarial indisponible")

    monkeypatch.setattr(type(consultation_service()), "consult", broken_consult)
    _, ctl = controller([contract()])
    with pytest.raises(RuntimeError, match="moteur salarial"):
        ctl.execute(request())


def test_type_strict_request_et_dependances():
    _, ctl = controller([])
    with pytest.raises(TypeError):
        ctl.execute(object())
    with pytest.raises(TypeError):
        ContractSalaryControlController(object(), ContractSalaryControlPresenter())
    with pytest.raises(TypeError):
        ContractSalaryControlController(ctl.use_case, object())


def test_controller_ne_filtre_ne_trie_ne_pagine_ne_formate_pas_lui_meme():
    low = contract(monthly_gross_salary_amount=Decimal("1990.00"))
    high = contract(monthly_gross_salary_amount=Decimal("1980.00"))
    _, ctl = controller([low, high])
    result = ctl.execute(request(
        statuses=(ContractSalaryControlStatus.NON_COMPLIANT,),
        sort_field=ContractSalaryControlSortField.SHORTFALL_AMOUNT,
        sort_direction=SortDirection.DESCENDING,
        limit=1,
    ))
    assert result.view_model.returned_count == 1
    assert result.view_model.filtered_total_count == 2
    assert result.view_model.rows[0].contract_id == high.id
    assert result.view_model.rows[0].shortfall_amount_label == "20,00 €"
    assert type(result.view_model) is ContractSalaryControlViewModel
