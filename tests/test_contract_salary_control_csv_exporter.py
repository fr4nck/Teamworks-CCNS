from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from application.presentation.salary_control_csv_exporter import ContractSalaryControlCsvExporter
from application.presentation.salary_control_presenter import (
    ContractSalaryControlPaginationViewModel,
    ContractSalaryControlPresentationStatus,
    ContractSalaryControlRowViewModel,
    ContractSalaryControlViewModel,
)
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus


def _view_model(rows=()):
    return ContractSalaryControlViewModel(
        reference_date=date(2026, 6, 1),
        reference_date_label="01/06/2026",
        rows=tuple(rows),
        global_total_count=len(rows),
        global_compliant_count=len(rows),
        global_non_compliant_count=0,
        global_not_evaluated_count=0,
        filtered_total_count=len(rows),
        returned_count=len(rows),
        filtered_total_shortfall_amount=Decimal("0.00"),
        filtered_total_shortfall_amount_label="0,00 €",
        global_valid=True,
        filtered_valid=True,
        presentation_status=ContractSalaryControlPresentationStatus.SUCCESS,
        summary_title="Contrôle salarial conforme",
        summary_message="",
        pagination=ContractSalaryControlPaginationViewModel(
            offset=0,
            limit=None,
            has_previous_page=False,
            has_next_page=False,
            previous_offset=None,
            next_offset=None,
            first_displayed_index=1 if rows else None,
            last_displayed_index=len(rows) if rows else None,
            total_filtered_count=len(rows),
            range_label="",
        ),
        empty_state=None,
    )


def _row():
    contract_id = UUID("11111111-1111-1111-1111-111111111111")
    return ContractSalaryControlRowViewModel(
        id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        contract_id=contract_id,
        contract_id_label=str(contract_id),
        employee_id=None,
        employee_id_label="Non renseigné",
        reference_date=date(2026, 6, 1),
        reference_date_label="01/06/2026",
        status=ContractSalaryControlStatus.COMPLIANT,
        status_label="Conforme",
        classification_code="G4; confirmé",
        classification_code_label="G4; confirmé",
        remuneration_amount=Decimal("2000.00"),
        remuneration_amount_label="2 000,00 €",
        applicable_minimum_amount=Decimal("1900.00"),
        applicable_minimum_amount_label="1 900,00 €",
        shortfall_amount=Decimal("0.00"),
        shortfall_amount_label="0,00 €",
        minimum_source=None,
        minimum_source_label="Non disponible",
        territory=None,
        territory_label="Non renseigné",
        failure_reason=None,
        failure_reason_label="",
        failure_message=None,
        failure_message_label="",
        issue_code=None,
        issue_code_label="",
        issue_message='Texte avec "guillemets"\net retour',
        issue_message_label='Texte avec "guillemets"\net retour',
    )


def test_export_vide_est_deterministe():
    result = ContractSalaryControlCsvExporter().export(_view_model())
    assert result.suggested_filename == "controle-salarial-2026-06-01.csv"
    assert result.mime_type == "text/csv; charset=utf-8"
    assert result.content.count("\r\n") == 1


def test_export_preserve_ordre_valeurs_brutes_et_echappement():
    result = ContractSalaryControlCsvExporter().export(_view_model((_row(),)))
    assert "2026-06-01;11111111-1111-1111-1111-111111111111;__ABSENT__;COMPLIANT" in result.content
    assert '"G4; confirmé"' in result.content
    assert '"Texte avec ""guillemets""\net retour"' in result.content


def test_export_refuse_un_type_incorrect():
    with pytest.raises(TypeError):
        ContractSalaryControlCsvExporter().export(object())
