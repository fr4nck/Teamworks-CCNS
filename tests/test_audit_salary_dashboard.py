from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from application.presentation import ContractSalaryControlRowViewModel
from domain.contracts import ContractSalaryControlStatus
from teamworks.CcnsCore.audit_filters import filter_audit_rows
from teamworks.CcnsCore.audit_salary_dashboard import salary_dashboard_from_audit_rows

D = date(2026, 7, 1)


def salary_row(status, shortfall=Decimal("0.00")):
    return ContractSalaryControlRowViewModel(
        id=uuid4(), contract_id=uuid4(), contract_id_label="c", employee_id=uuid4(), employee_id_label="e", reference_date=D, reference_date_label="01/07/2026",
        status=status, status_label=status.value, classification_code="G3", classification_code_label="G3", remuneration_amount=Decimal("2100.00"), remuneration_amount_label="2 100,00 €",
        applicable_minimum_amount=Decimal("1997.87"), applicable_minimum_amount_label="1 997,87 €", shortfall_amount=shortfall, shortfall_amount_label="0,00 €",
        minimum_source=None, minimum_source_label="Non disponible", territory=None, territory_label="Non renseigné", failure_reason=None, failure_reason_label="", failure_message=None, failure_message_label="", issue_code=None, issue_code_label="", issue_message=None, issue_message_label="",
    )


def test_adaptation_depuis_audit_rows_ignore_sans_controle_et_ne_recalcule_pas(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("appel interdit")
    monkeypatch.setattr("teamworks.CcnsCore.audit_contracts_ccns.audit_contracts", forbidden)
    monkeypatch.setattr("infrastructure.persistence.ccns_data_reader.CcnsDataReader.lire_contrats", forbidden)
    r1 = salary_row(ContractSalaryControlStatus.COMPLIANT)
    r2 = salary_row(ContractSalaryControlStatus.NON_COMPLIANT, Decimal("10.00"))
    dashboard = salary_dashboard_from_audit_rows(({"salary_control_row": r1}, {"IDcontrat": 99}, type("AuditLike", (), {"salary_control_row": r2})()))
    assert dashboard.total_contracts == 2
    assert dashboard.non_compliant_contracts == 1
    assert dashboard.total_shortfall_amount == Decimal("10.00")


def test_tableau_de_bord_compatible_avec_filtres_existants():
    compliant = salary_row(ContractSalaryControlStatus.COMPLIANT)
    non_compliant = salary_row(ContractSalaryControlStatus.NON_COMPLIANT, Decimal("8.50"))
    rows = [
        {"IDcontrat": 1, "classification": "G3", "type_contrat": "CDI", "salaire_base": 2100.0, "anomalies": [], "salary_control_status": compliant.status, "shortfall_amount": compliant.shortfall_amount, "salary_control_row": compliant},
        {"IDcontrat": 2, "classification": "G3", "type_contrat": "CDI", "salaire_base": 1800.0, "anomalies": ["A"], "salary_control_status": non_compliant.status, "shortfall_amount": non_compliant.shortfall_amount, "salary_control_row": non_compliant},
    ]
    filtered = filter_audit_rows(rows, salary_control_status=ContractSalaryControlStatus.NON_COMPLIANT)
    dashboard = salary_dashboard_from_audit_rows(filtered)
    assert dashboard.total_contracts == 1
    assert dashboard.non_compliant_contracts == 1
    assert dashboard.total_shortfall_amount == Decimal("8.50")


def test_rejette_salary_control_row_invalide():
    with pytest.raises(TypeError):
        salary_dashboard_from_audit_rows(({"salary_control_row": object()},))
