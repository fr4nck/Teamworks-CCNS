from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from application.presentation import ContractSalaryControlEmployeeSummaryPresenter, ContractSalaryControlRowViewModel
from domain.contracts import ContractSalaryControlStatus

D = date(2026, 7, 1)


def row(employee_id=None, status=ContractSalaryControlStatus.COMPLIANT, shortfall=Decimal("0.00"), contract_id=None, ref=D):
    employee_id = employee_id or uuid4()
    return ContractSalaryControlRowViewModel(
        id=uuid4(), contract_id=contract_id or uuid4(), contract_id_label="c", employee_id=employee_id, employee_id_label=str(employee_id),
        reference_date=ref, reference_date_label="01/07/2026", status=status, status_label=status.value,
        classification_code="G3", classification_code_label="G3", remuneration_amount=Decimal("2100.00"), remuneration_amount_label="2 100,00 €",
        applicable_minimum_amount=Decimal("1997.87"), applicable_minimum_amount_label="1 997,87 €", shortfall_amount=shortfall,
        shortfall_amount_label="0,00 €", minimum_source=None, minimum_source_label="Non disponible", territory=None, territory_label="Non renseigné",
        failure_reason=None, failure_reason_label="", failure_message=None, failure_message_label="", issue_code=None, issue_code_label="", issue_message=None, issue_message_label="",
    )


def test_salarie_avec_un_contrat_conforme_sans_recalcul(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("appel interdit")
    monkeypatch.setattr("domain.contracts.contract_salary_control.ContractSalaryControlService.control", forbidden)
    employee_id = uuid4()
    r = row(employee_id)
    summary = ContractSalaryControlEmployeeSummaryPresenter().present((r,), employee_id)
    assert summary.rows == (r,)
    assert summary.total_count == 1
    assert summary.compliant_count == 1
    assert summary.total_shortfall_amount == Decimal("0.00")
    assert summary.valid is True
    assert summary.empty is False


def test_plusieurs_contrats_mixtes_compteurs_somme_ordre_et_instances():
    employee_id = uuid4()
    rows = (
        row(employee_id, ContractSalaryControlStatus.COMPLIANT, Decimal("0.00")),
        row(uuid4(), ContractSalaryControlStatus.NON_COMPLIANT, Decimal("99.99")),
        row(employee_id, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("67.02")),
        row(employee_id, ContractSalaryControlStatus.NOT_EVALUATED, Decimal("0.00")),
    )
    summary = ContractSalaryControlEmployeeSummaryPresenter().present(rows, employee_id)
    assert summary.rows == (rows[0], rows[2], rows[3])
    assert summary.rows[0] is rows[0]
    assert summary.total_count == 3
    assert summary.compliant_count == 1
    assert summary.non_compliant_count == 1
    assert summary.not_evaluated_count == 1
    assert summary.total_shortfall_amount == Decimal("67.02")
    assert summary.valid is False


def test_uniquement_non_evaluable_et_absent():
    employee_id = uuid4()
    summary = ContractSalaryControlEmployeeSummaryPresenter().present((row(employee_id, ContractSalaryControlStatus.NOT_EVALUATED),), employee_id)
    assert summary.not_evaluated_count == 1
    assert summary.total_shortfall_amount == Decimal("0.00")
    assert summary.valid is False
    empty = ContractSalaryControlEmployeeSummaryPresenter().present((row(uuid4()),), employee_id)
    assert empty.empty is True
    assert empty.total_count == 0
    assert empty.total_shortfall_amount == Decimal("0.00")


def test_rejets_et_immuabilite():
    employee_id = uuid4()
    with pytest.raises(TypeError):
        ContractSalaryControlEmployeeSummaryPresenter().present([], employee_id)
    with pytest.raises(TypeError):
        ContractSalaryControlEmployeeSummaryPresenter().present((object(),), employee_id)
    with pytest.raises(TypeError):
        ContractSalaryControlEmployeeSummaryPresenter().present((), str(employee_id))
    contract_id = uuid4()
    with pytest.raises(ValueError, match="dupliqué"):
        ContractSalaryControlEmployeeSummaryPresenter().present((row(employee_id, contract_id=contract_id), row(employee_id, contract_id=contract_id)), employee_id)
    with pytest.raises(ValueError, match="date"):
        ContractSalaryControlEmployeeSummaryPresenter().present((row(employee_id), row(employee_id, ref=date(2026, 8, 1))), employee_id)
    summary = ContractSalaryControlEmployeeSummaryPresenter().present((row(employee_id),), employee_id)
    with pytest.raises(FrozenInstanceError):
        summary.total_count = 9
