import copy
from dataclasses import FrozenInstanceError, replace
from datetime import date
from decimal import Decimal
import json
from uuid import UUID

import pytest

from application.presentation import (
    ContractSalaryControlEmptyStateViewModel,
    ContractSalaryControlJsonExport,
    ContractSalaryControlJsonExporter,
    ContractSalaryControlPaginationViewModel,
    ContractSalaryControlPresentationStatus,
    ContractSalaryControlRowViewModel,
    ContractSalaryControlViewModel,
)
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory


def _pagination():
    return ContractSalaryControlPaginationViewModel(10, 2, True, True, 8, 12, 11, 12, 42, "11 à 12 sur 42")


def _view_model(rows=(), *, empty_state=None):
    return ContractSalaryControlViewModel(
        reference_date=date(2026, 6, 1),
        reference_date_label="01/06/2026",
        rows=tuple(rows),
        global_total_count=3,
        global_compliant_count=1,
        global_non_compliant_count=1,
        global_not_evaluated_count=1,
        filtered_total_count=42,
        returned_count=len(rows),
        filtered_total_shortfall_amount=Decimal("1234.50"),
        filtered_total_shortfall_amount_label="1 234,50 €",
        global_valid=False,
        filtered_valid=False,
        presentation_status=ContractSalaryControlPresentationStatus.WARNING,
        summary_title="Contrôle salarial à vérifier",
        summary_message="Résumé avec accents éèà",
        pagination=_pagination(),
        empty_state=empty_state,
    )


def _row(identifier, status):
    return ContractSalaryControlRowViewModel(
        id=UUID(identifier),
        contract_id=UUID("11111111-1111-1111-1111-111111111111"),
        contract_id_label="11111111-1111-1111-1111-111111111111",
        employee_id=UUID("22222222-2222-2222-2222-222222222222"),
        employee_id_label="22222222-2222-2222-2222-222222222222",
        reference_date=date(2026, 6, 1),
        reference_date_label="01/06/2026",
        status=status,
        status_label="Non conforme",
        classification_code="G4 confirmé",
        classification_code_label="G4 confirmé",
        remuneration_amount=Decimal("1999.90"),
        remuneration_amount_label="1 999,90 €",
        applicable_minimum_amount=Decimal("2000.00"),
        applicable_minimum_amount_label="2 000,00 €",
        shortfall_amount=Decimal("0.10"),
        shortfall_amount_label="0,10 €",
        minimum_source=ApplicableSalaryMinimumSource.CCNS,
        minimum_source_label="CCNS",
        territory=SmicTerritory.METROPOLITAN_FRANCE,
        territory_label="France métropolitaine",
        failure_reason=ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION,
        failure_reason_label="Rémunération manquante",
        failure_message='Message avec "guillemets"\net retour',
        failure_message_label='Message avec "guillemets"\net retour',
        issue_code=None,
        issue_code_label="",
        issue_message="Écart détecté",
        issue_message_label="Écart détecté",
    )


def _export(vm):
    result = ContractSalaryControlJsonExporter().export(vm)
    return result, json.loads(result.content)


def test_export_vide_nom_mime_json_valide_empty_state_absent_et_accents():
    result, data = _export(_view_model())
    assert result.suggested_filename == "controle-salarial-2026-06-01.json"
    assert result.mime_type == "application/json; charset=utf-8"
    assert result.content.endswith("\n")
    assert data["reference_date"] == "2026-06-01"
    assert data["status"] == "warning"
    assert data["empty_state"] is None
    assert data["rows"] == []
    assert "éèà" in result.content


def test_export_lignes_preserve_ordre_valeurs_brutes_dates_uuid_enums_decimal_none_et_echappement():
    first = _row("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", ContractSalaryControlStatus.NON_COMPLIANT)
    second = _row("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", ContractSalaryControlStatus.COMPLIANT)
    second = replace(second, employee_id=None, remuneration_amount=None, issue_message='Texte "cité"\nligne')
    result, data = _export(_view_model((first, second)))

    assert all("id" not in row for row in data["rows"])
    assert [row["status"] for row in data["rows"]] == ["non_compliant", "compliant"]
    assert data["rows"][0]["contract_id"] == "11111111-1111-1111-1111-111111111111"
    assert data["rows"][0]["reference_date"] == "2026-06-01"
    assert data["rows"][0]["minimum_source"] == "ccns"
    assert data["rows"][0]["territory"] == "metropolitan_france"
    assert data["rows"][0]["failure_reason"] == "missing_remuneration"
    assert data["rows"][0]["remuneration_amount"] == "1999.90"
    assert data["rows"][0]["shortfall_amount"] == "0.10"
    assert data["rows"][1]["employee_id"] is None
    assert data["rows"][1]["remuneration_amount"] is None
    assert '\\"cité\\"\\nligne' in result.content


def test_export_pagination_complete_et_empty_state_present():
    empty_state = ContractSalaryControlEmptyStateViewModel("Aucun résultat", "Aucune ligne filtrée")
    _, data = _export(_view_model(empty_state=empty_state))
    assert data["pagination"] == {
        "offset": 10,
        "limit": 2,
        "has_previous_page": True,
        "has_next_page": True,
        "previous_offset": 8,
        "next_offset": 12,
        "first_displayed_index": 11,
        "last_displayed_index": 12,
        "total_filtered_count": 42,
    }
    assert data["empty_state"] == {"title": "Aucun résultat", "message": "Aucune ligne filtrée"}


def test_export_refuse_un_type_incorrect_et_resultat_immuable():
    with pytest.raises(TypeError):
        ContractSalaryControlJsonExporter().export(object())
    export = ContractSalaryControlJsonExport("{}\n", "controle-salarial-2026-06-01.json")
    with pytest.raises(FrozenInstanceError):
        export.content = "x"


def test_export_ne_mute_pas_le_view_model_et_import_package_sans_cycle():
    vm = _view_model((_row("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", ContractSalaryControlStatus.NON_COMPLIANT),))
    before = copy.deepcopy(vm)
    ContractSalaryControlJsonExporter().export(vm)
    assert vm == before
    import application.presentation as presentation

    assert presentation.ContractSalaryControlJsonExporter is ContractSalaryControlJsonExporter
