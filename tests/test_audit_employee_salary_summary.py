from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from application.presentation import ContractSalaryControlDetailPresenter, ContractSalaryControlRowViewModel
from domain.contracts import ContractSalaryControlStatus
from teamworks.CcnsCore.audit_employee_salary_summary import employee_salary_summary_from_audit_rows
from teamworks.CcnsCore.audit_filters import filter_audit_rows
from teamworks.CcnsCore.audit_sorting import sort_audit_rows_by_salary

D = date(2026, 7, 1)


def salary_row(employee_id, contract_label):
    return ContractSalaryControlRowViewModel(
        id=uuid4(), contract_id=uuid4(), contract_id_label=contract_label, employee_id=employee_id, employee_id_label=str(employee_id), reference_date=D, reference_date_label="01/07/2026",
        status=ContractSalaryControlStatus.COMPLIANT, status_label="Conforme", classification_code="G3", classification_code_label="G3", remuneration_amount=Decimal("2100.00"), remuneration_amount_label="2 100,00 €",
        applicable_minimum_amount=Decimal("1997.87"), applicable_minimum_amount_label="1 997,87 €", shortfall_amount=Decimal("0.00"), shortfall_amount_label="0,00 €",
        minimum_source=None, minimum_source_label="Non disponible", territory=None, territory_label="Non renseigné", failure_reason=None, failure_reason_label="", failure_message=None, failure_message_label="", issue_code=None, issue_code_label="", issue_message=None, issue_message_label="",
    )


def test_construction_depuis_audit_rows_exclut_sans_detail_et_ne_lit_pas(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("accès base ou contrôle interdit")
    monkeypatch.setattr("teamworks.CcnsCore.audit_contracts_ccns.audit_contracts", forbidden)
    monkeypatch.setattr("infrastructure.persistence.ccns_data_reader.CcnsDataReader.lire_contrats", forbidden)
    employee_id = uuid4()
    r1 = salary_row(employee_id, "1")
    r2 = salary_row(employee_id, "2")
    summary = employee_salary_summary_from_audit_rows(({"salary_control_row": r1}, {"IDcontrat": 99}, type("AuditLike", (), {"salary_control_row": r2})()), employee_id)
    assert summary.rows == (r1, r2)


def test_lignes_completes_avant_filtre_visuel_et_tris_sans_perte_de_rattachement():
    employee_id = uuid4()
    r1 = salary_row(employee_id, "1")
    r2 = salary_row(employee_id, "2")
    rows = [
        {"IDcontrat": 1, "classification": "G3", "type_contrat": "CDI", "salaire_base": 2100.0, "anomalies": [], "salary_control_status": r1.status, "shortfall_amount": r1.shortfall_amount, "salary_control_row": r1},
        {"IDcontrat": 2, "classification": "G4", "type_contrat": "CDD", "salaire_base": 2100.0, "anomalies": [], "salary_control_status": r2.status, "shortfall_amount": r2.shortfall_amount, "salary_control_row": r2},
    ]
    filtered = filter_audit_rows(rows, classification_filter="G3")
    sorted_rows = sort_audit_rows_by_salary(filtered, "shortfall_amount")
    assert sorted_rows[0]["salary_control_row"] is r1
    summary = employee_salary_summary_from_audit_rows(rows, employee_id)
    assert summary.rows == (r1, r2)
    detail = ContractSalaryControlDetailPresenter().present(summary.rows[0])
    assert detail.contract_id is r1.contract_id


def test_comportement_sans_identifiant_salarie():
    with pytest.raises(TypeError):
        employee_salary_summary_from_audit_rows((), None)
