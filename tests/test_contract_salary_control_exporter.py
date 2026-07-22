from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
import json
from uuid import UUID

import pytest

from application.presentation import (
    ContractSalaryControlCsvExporter,
    ContractSalaryControlExport,
    ContractSalaryControlExporter,
    ContractSalaryControlExportFormat,
    ContractSalaryControlJsonExporter,
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
        global_compliant_count=1,
        global_non_compliant_count=1,
        global_not_evaluated_count=0,
        filtered_total_count=len(rows),
        returned_count=len(rows),
        filtered_total_shortfall_amount=Decimal("10.00"),
        filtered_total_shortfall_amount_label="10,00 €",
        global_valid=False,
        filtered_valid=False,
        presentation_status=ContractSalaryControlPresentationStatus.WARNING,
        summary_title="Contrôle salarial à vérifier",
        summary_message="Résumé",
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


def _row(identifier, status):
    return ContractSalaryControlRowViewModel(
        id=UUID(identifier),
        contract_id=UUID(identifier),
        contract_id_label=identifier,
        employee_id=None,
        employee_id_label="Non renseigné",
        reference_date=date(2026, 6, 1),
        reference_date_label="01/06/2026",
        status=status,
        status_label="Statut",
        classification_code="G4",
        classification_code_label="G4",
        remuneration_amount=Decimal("1990.00"),
        remuneration_amount_label="1 990,00 €",
        applicable_minimum_amount=Decimal("2000.00"),
        applicable_minimum_amount_label="2 000,00 €",
        shortfall_amount=Decimal("10.00"),
        shortfall_amount_label="10,00 €",
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
        issue_message=None,
        issue_message_label="",
    )


def test_export_csv_via_facade_conserve_exactement_export_specialise_et_ordre_des_lignes():
    rows = (
        _row("11111111-1111-1111-1111-111111111111", ContractSalaryControlStatus.NON_COMPLIANT),
        _row("22222222-2222-2222-2222-222222222222", ContractSalaryControlStatus.COMPLIANT),
    )
    vm = _view_model(rows)

    expected = ContractSalaryControlCsvExporter().export(vm)
    result = ContractSalaryControlExporter().export(vm, ContractSalaryControlExportFormat.CSV)

    assert result.content == expected.content
    assert result.suggested_filename == expected.suggested_filename
    assert result.mime_type == expected.mime_type
    assert result.format is ContractSalaryControlExportFormat.CSV
    assert result.content.index(str(rows[0].contract_id)) < result.content.index(str(rows[1].contract_id))


def test_export_json_via_facade_conserve_exactement_export_specialise_et_ordre_des_lignes():
    rows = (
        _row("11111111-1111-1111-1111-111111111111", ContractSalaryControlStatus.NON_COMPLIANT),
        _row("22222222-2222-2222-2222-222222222222", ContractSalaryControlStatus.COMPLIANT),
    )
    vm = _view_model(rows)

    expected = ContractSalaryControlJsonExporter().export(vm)
    result = ContractSalaryControlExporter().export(vm, ContractSalaryControlExportFormat.JSON)
    data = json.loads(result.content)

    assert result.content == expected.content
    assert result.suggested_filename == expected.suggested_filename
    assert result.mime_type == expected.mime_type
    assert result.format is ContractSalaryControlExportFormat.JSON
    assert [row["contract_id"] for row in data["rows"]] == [str(row.contract_id) for row in rows]


def test_export_refuse_un_view_model_invalide_et_un_format_invalide():
    exporter = ContractSalaryControlExporter()
    with pytest.raises(TypeError):
        exporter.export(object(), ContractSalaryControlExportFormat.CSV)
    with pytest.raises(TypeError):
        exporter.export(_view_model(), "csv")


def test_resultat_generique_immuable_et_valide_strictement_ses_champs():
    result = ContractSalaryControlExport("contenu", "controle.csv", "text/plain", ContractSalaryControlExportFormat.CSV)
    with pytest.raises(FrozenInstanceError):
        result.content = "x"
    with pytest.raises(ValueError):
        ContractSalaryControlExport("", "controle.csv", "text/plain", ContractSalaryControlExportFormat.CSV)
    with pytest.raises(ValueError):
        ContractSalaryControlExport("contenu", " ", "text/plain", ContractSalaryControlExportFormat.CSV)
    with pytest.raises(ValueError):
        ContractSalaryControlExport("contenu", "controle.csv", " ", ContractSalaryControlExportFormat.CSV)
    with pytest.raises(TypeError):
        ContractSalaryControlExport("contenu", "controle.csv", "text/plain", "csv")


def test_injection_des_exporteurs_specialises_est_conservee_et_validee():
    csv_exporter = ContractSalaryControlCsvExporter()
    json_exporter = ContractSalaryControlJsonExporter()
    facade = ContractSalaryControlExporter(csv_exporter=csv_exporter, json_exporter=json_exporter)

    assert facade.csv_exporter is csv_exporter
    assert facade.json_exporter is json_exporter
    with pytest.raises(TypeError):
        ContractSalaryControlExporter(csv_exporter=object())
    with pytest.raises(TypeError):
        ContractSalaryControlExporter(json_exporter=object())


def test_import_public_application_presentation_sans_erreur():
    import application.presentation as presentation

    assert presentation.ContractSalaryControlExportFormat is ContractSalaryControlExportFormat
    assert presentation.ContractSalaryControlExport is ContractSalaryControlExport
    assert presentation.ContractSalaryControlExporter is ContractSalaryControlExporter
