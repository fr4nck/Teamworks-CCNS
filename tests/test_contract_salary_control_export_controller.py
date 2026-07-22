from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from application.control import (
    ContractSalaryControlExportController,
    ContractSalaryControlExportRequest,
    ContractSalaryControlExportResponse,
)
from application.presentation import (
    ContractSalaryControlExport,
    ContractSalaryControlExporter,
    ContractSalaryControlExportFormat,
    ContractSalaryControlPaginationViewModel,
    ContractSalaryControlPresentationStatus,
    ContractSalaryControlViewModel,
)


def _view_model() -> ContractSalaryControlViewModel:
    return ContractSalaryControlViewModel(
        reference_date=date(2026, 6, 1),
        reference_date_label="01/06/2026",
        rows=(),
        global_total_count=0,
        global_compliant_count=0,
        global_non_compliant_count=0,
        global_not_evaluated_count=0,
        filtered_total_count=0,
        returned_count=0,
        filtered_total_shortfall_amount=Decimal("0.00"),
        filtered_total_shortfall_amount_label="0,00 €",
        global_valid=True,
        filtered_valid=True,
        presentation_status=ContractSalaryControlPresentationStatus.EMPTY,
        summary_title="Aucun résultat",
        summary_message="Aucun contrat ne correspond aux critères de consultation.",
        pagination=ContractSalaryControlPaginationViewModel(
            offset=0,
            limit=None,
            has_previous_page=False,
            has_next_page=False,
            previous_offset=None,
            next_offset=None,
            first_displayed_index=None,
            last_displayed_index=None,
            total_filtered_count=0,
            range_label="Aucun résultat",
        ),
        empty_state=None,
    )


@pytest.mark.parametrize(
    "format",
    [ContractSalaryControlExportFormat.CSV, ContractSalaryControlExportFormat.JSON],
)
def test_export_csv_et_json_identique_a_la_facade(format):
    view_model = _view_model()
    exporter = ContractSalaryControlExporter()
    expected = exporter.export(view_model, format)

    response = ContractSalaryControlExportController(exporter).execute(
        ContractSalaryControlExportRequest(view_model, format)
    )

    assert response.content == expected.content
    assert response.suggested_filename == expected.suggested_filename
    assert response.mime_type == expected.mime_type
    assert response.format is format


def test_delegation_unique_et_propagation_exacte_sans_modifier_le_contenu(monkeypatch):
    view_model = _view_model()
    content = "\ufeffligne 1\r\nligne 2,é\n"
    produced = ContractSalaryControlExport(
        content,
        "controle-original.csv",
        "text/csv; charset=utf-8",
        ContractSalaryControlExportFormat.CSV,
    )
    calls = []

    def export(self, received_view_model, received_format):
        calls.append((self, received_view_model, received_format))
        return produced

    monkeypatch.setattr(ContractSalaryControlExporter, "export", export)
    exporter = ContractSalaryControlExporter()
    response = ContractSalaryControlExportController(exporter).execute(
        ContractSalaryControlExportRequest(view_model, ContractSalaryControlExportFormat.CSV)
    )

    assert calls == [(exporter, view_model, ContractSalaryControlExportFormat.CSV)]
    assert response.content is produced.content
    assert response.suggested_filename is produced.suggested_filename
    assert response.mime_type is produced.mime_type
    assert response.format is produced.format


def test_validation_stricte_de_la_requete_du_controleur_et_de_sa_dependance():
    view_model = _view_model()
    with pytest.raises(TypeError):
        ContractSalaryControlExportRequest(object(), ContractSalaryControlExportFormat.CSV)
    with pytest.raises(TypeError):
        ContractSalaryControlExportRequest(view_model, "csv")
    with pytest.raises(TypeError):
        ContractSalaryControlExportController(object())
    with pytest.raises(TypeError):
        ContractSalaryControlExportController().execute(object())


@pytest.mark.parametrize(
    "values,error",
    [
        ((object(), "controle.csv", "text/csv", ContractSalaryControlExportFormat.CSV), TypeError),
        (("", "controle.csv", "text/csv", ContractSalaryControlExportFormat.CSV), ValueError),
        (("contenu", object(), "text/csv", ContractSalaryControlExportFormat.CSV), TypeError),
        (("contenu", " ", "text/csv", ContractSalaryControlExportFormat.CSV), ValueError),
        (("contenu", "controle.csv", object(), ContractSalaryControlExportFormat.CSV), TypeError),
        (("contenu", "controle.csv", " ", ContractSalaryControlExportFormat.CSV), ValueError),
        (("contenu", "controle.csv", "text/csv", "csv"), TypeError),
    ],
)
def test_validation_stricte_de_la_reponse(values, error):
    with pytest.raises(error):
        ContractSalaryControlExportResponse(*values)


def test_requete_reponse_et_controleur_sont_immuables_et_sans_dict():
    request = ContractSalaryControlExportRequest(
        _view_model(),
        ContractSalaryControlExportFormat.JSON,
    )
    response = ContractSalaryControlExportController().execute(request)
    controller = ContractSalaryControlExportController()

    with pytest.raises(FrozenInstanceError):
        request.format = ContractSalaryControlExportFormat.CSV
    with pytest.raises(FrozenInstanceError):
        response.content = "modifié"
    with pytest.raises(FrozenInstanceError):
        controller.exporter = ContractSalaryControlExporter()
    assert not hasattr(request, "__dict__")
    assert not hasattr(response, "__dict__")
    assert not hasattr(controller, "__dict__")


def test_import_public_application_control_sans_erreur():
    import application.control as control

    assert control.ContractSalaryControlExportController is ContractSalaryControlExportController
    assert control.ContractSalaryControlExportRequest is ContractSalaryControlExportRequest
    assert control.ContractSalaryControlExportResponse is ContractSalaryControlExportResponse
