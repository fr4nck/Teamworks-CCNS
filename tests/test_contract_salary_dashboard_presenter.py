from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from application.presentation import ContractSalaryDashboardPresenter, ContractSalaryControlRowViewModel
from domain.contracts import ContractSalaryControlStatus

D = date(2026, 7, 1)


def row(status=ContractSalaryControlStatus.COMPLIANT, shortfall=Decimal("0.00"), contract_id=None, ref=D):
    return ContractSalaryControlRowViewModel(
        id=uuid4(), contract_id=contract_id or uuid4(), contract_id_label="c", employee_id=uuid4(), employee_id_label="e",
        reference_date=ref, reference_date_label="01/07/2026", status=status, status_label=status.value,
        classification_code="G3", classification_code_label="G3", remuneration_amount=Decimal("2100.00"), remuneration_amount_label="2 100,00 €",
        applicable_minimum_amount=Decimal("1997.87"), applicable_minimum_amount_label="1 997,87 €", shortfall_amount=shortfall, shortfall_amount_label="0,00 €",
        minimum_source=None, minimum_source_label="Non disponible", territory=None, territory_label="Non renseigné", failure_reason=None, failure_reason_label="",
        failure_message=None, failure_message_label="", issue_code=None, issue_code_label="", issue_message=None, issue_message_label="",
    )


def test_audit_vide_compteurs_zero_labels_decimal_et_message_explicite():
    dashboard = ContractSalaryDashboardPresenter().present(())
    assert dashboard.total_contracts == 0
    assert dashboard.compliant_contracts == 0
    assert dashboard.non_compliant_contracts == 0
    assert dashboard.not_evaluated_contracts == 0
    assert dashboard.compliant_percentage == Decimal("0.00")
    assert dashboard.non_compliant_percentage == Decimal("0.00")
    assert dashboard.total_shortfall_amount == Decimal("0.00")
    assert type(dashboard.total_shortfall_amount) is Decimal
    assert dashboard.total_shortfall_amount_label == "0,00 €"
    assert dashboard.valid is False
    assert "Aucun contrat salarial contrôlé" in dashboard.summary_label


def test_audit_entierement_conforme_100_pourcent_valide_sans_recalcul(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("appel interdit")
    monkeypatch.setattr("domain.contracts.contract_salary_control.ContractSalaryControlService.control", forbidden)
    dashboard = ContractSalaryDashboardPresenter().present((row(), row()))
    assert dashboard.total_contracts == 2
    assert dashboard.compliant_contracts == 2
    assert dashboard.compliant_percentage == Decimal("100.00")
    assert dashboard.non_compliant_percentage == Decimal("0.00")
    assert dashboard.total_shortfall_amount == Decimal("0.00")
    assert dashboard.valid is True


def test_audit_mixte_compteurs_pourcentages_et_somme_exacte():
    rows = (
        row(ContractSalaryControlStatus.COMPLIANT, Decimal("0.00")),
        row(ContractSalaryControlStatus.NON_COMPLIANT, Decimal("67.02")),
        row(ContractSalaryControlStatus.NON_COMPLIANT, Decimal("12.23")),
        row(ContractSalaryControlStatus.NOT_EVALUATED, Decimal("0.00")),
    )
    dashboard = ContractSalaryDashboardPresenter().present(rows)
    assert dashboard.compliant_contracts == 1
    assert dashboard.non_compliant_contracts == 2
    assert dashboard.not_evaluated_contracts == 1
    assert dashboard.compliant_percentage == Decimal("25.00")
    assert dashboard.non_compliant_percentage == Decimal("50.00")
    assert dashboard.total_shortfall_amount == Decimal("79.25")
    assert dashboard.reference_date is rows[0].reference_date
    assert dashboard.valid is False


def test_pourcentages_arrondis_en_decimal_sans_float():
    dashboard = ContractSalaryDashboardPresenter().present((row(), row(ContractSalaryControlStatus.NON_COMPLIANT, Decimal("1.00")), row(ContractSalaryControlStatus.NOT_EVALUATED)))
    assert dashboard.compliant_percentage == Decimal("33.33")
    assert dashboard.non_compliant_percentage == Decimal("33.33")
    assert type(dashboard.compliant_percentage) is Decimal


def test_rejets_types_invalides_doublons_dates_et_immuabilite():
    presenter = ContractSalaryDashboardPresenter()
    with pytest.raises(TypeError):
        presenter.present([])
    with pytest.raises(TypeError):
        presenter.present((object(),))
    duplicate_id = uuid4()
    with pytest.raises(ValueError, match="dupliqué"):
        presenter.present((row(contract_id=duplicate_id), row(contract_id=duplicate_id)))
    with pytest.raises(ValueError, match="date"):
        presenter.present((row(), row(ref=date(2026, 8, 1))))
    dashboard = presenter.present((row(),))
    with pytest.raises(FrozenInstanceError):
        dashboard.total_contracts = 9
