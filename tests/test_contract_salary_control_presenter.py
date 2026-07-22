from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from application.control import ContractSalaryControlConsultationApplicationResult
from application.presentation import (
    ContractSalaryControlPresentationStatus,
    ContractSalaryControlPresenter,
    format_euro_amount,
)
from domain.contracts import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_projection import ContractSalaryControlRow
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory

D = date(2026, 1, 1)


def row(status=ContractSalaryControlStatus.COMPLIANT, *, shortfall=Decimal("0.00"), contract_id=None):
    contract_id = contract_id or uuid4()
    employee_id = uuid4()
    if status is ContractSalaryControlStatus.NOT_EVALUATED:
        return ContractSalaryControlRow(
            contract_id,
            employee_id,
            D,
            status,
            "G1",
            None,
            None,
            Decimal("0.00"),
            None,
            SmicTerritory.METROPOLITAN_FRANCE,
            ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION,
            "Rémunération manquante.",
            None,
            None,
        )
    return ContractSalaryControlRow(
        contract_id,
        employee_id,
        D,
        status,
        "G1",
        Decimal("1990.00") if status is ContractSalaryControlStatus.NON_COMPLIANT else Decimal("2100.00"),
        Decimal("2000.00"),
        shortfall,
        ApplicableSalaryMinimumSource.CCNS,
        SmicTerritory.METROPOLITAN_FRANCE,
        None,
        None,
        "SALARY_BELOW_MINIMUM" if status is ContractSalaryControlStatus.NON_COMPLIANT else None,
        "La rémunération est inférieure au minimum applicable." if status is ContractSalaryControlStatus.NON_COMPLIANT else None,
    )


def app(rows=(), *, global_rows=None, offset=0, limit=None, returned_rows=None):
    global_rows = rows if global_rows is None else global_rows
    returned_rows = rows if returned_rows is None else returned_rows
    return ContractSalaryControlConsultationApplicationResult(
        reference_date=D,
        rows=returned_rows,
        global_total_count=len(global_rows),
        global_compliant_count=sum(r.status is ContractSalaryControlStatus.COMPLIANT for r in global_rows),
        global_non_compliant_count=sum(r.status is ContractSalaryControlStatus.NON_COMPLIANT for r in global_rows),
        global_not_evaluated_count=sum(r.status is ContractSalaryControlStatus.NOT_EVALUATED for r in global_rows),
        filtered_total_count=len(rows),
        filtered_compliant_count=sum(r.status is ContractSalaryControlStatus.COMPLIANT for r in rows),
        filtered_non_compliant_count=sum(r.status is ContractSalaryControlStatus.NON_COMPLIANT for r in rows),
        filtered_not_evaluated_count=sum(r.status is ContractSalaryControlStatus.NOT_EVALUATED for r in rows),
        returned_count=len(returned_rows),
        offset=offset,
        limit=limit,
        has_previous_page=offset > 0,
        has_next_page=(offset + len(returned_rows)) < len(rows),
        previous_offset=max(0, offset - (limit or len(returned_rows))) if offset > 0 else None,
        next_offset=offset + len(returned_rows) if (offset + len(returned_rows)) < len(rows) else None,
        filtered_total_shortfall_amount=sum((r.shortfall_amount for r in rows), Decimal("0.00")),
        global_valid=all(r.status is ContractSalaryControlStatus.COMPLIANT for r in global_rows),
        filtered_valid=all(r.status is ContractSalaryControlStatus.COMPLIANT for r in rows),
    )


def present(result):
    return ContractSalaryControlPresenter().present(result)


def test_resultat_vide_et_pagination_vide():
    vm = present(app())
    assert vm.presentation_status is ContractSalaryControlPresentationStatus.EMPTY
    assert vm.empty_state is not None
    assert vm.summary_title == "Aucun résultat"
    assert vm.reference_date is D
    assert vm.reference_date_label == "01/01/2026"
    assert vm.pagination.range_label == "Résultats 0 à 0 sur 0"
    assert vm.pagination.first_displayed_index is None
    assert vm.filtered_total_shortfall_amount == Decimal("0.00")
    assert vm.filtered_total_shortfall_amount_label == "0,00 €"


def test_lot_entierement_conforme():
    vm = present(app((row(), row(),)))
    assert vm.presentation_status is ContractSalaryControlPresentationStatus.SUCCESS
    assert vm.summary_title == "Contrôle salarial conforme"
    assert "2 contrats contrôlés" in vm.summary_message
    assert [r.status_label for r in vm.rows] == ["Conforme", "Conforme"]


def test_une_ligne_non_conforme_et_libelles_metier():
    ko = row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.63"))
    vm = present(app((ko,)))
    assert vm.presentation_status is ContractSalaryControlPresentationStatus.ERROR
    assert vm.summary_message == "1 contrat non conforme ; aucun contrat non évaluable."
    line = vm.rows[0]
    assert line.status is ContractSalaryControlStatus.NON_COMPLIANT
    assert line.status_label == "Non conforme"
    assert line.shortfall_amount == Decimal("10.63")
    assert line.shortfall_amount_label == "10,63 €"
    assert line.issue_code_label == "SALARY_BELOW_MINIMUM"


def test_plusieurs_non_conformes_singulier_pluriel_et_montants_francais():
    rows = (row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00")), row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("2099.37")))
    vm = present(app(rows))
    assert vm.summary_message == "2 contrats non conformes ; aucun contrat non évaluable."
    assert vm.filtered_total_shortfall_amount == Decimal("2109.37")
    assert vm.filtered_total_shortfall_amount_label == "2 109,37 €"
    assert vm.rows[1].shortfall_amount_label == "2 099,37 €"


def test_lignes_non_evaluables_warning():
    vm = present(app((row(ContractSalaryControlStatus.NOT_EVALUATED),)))
    assert vm.presentation_status is ContractSalaryControlPresentationStatus.WARNING
    assert vm.rows[0].status_label == "Non évaluable"
    assert vm.rows[0].failure_reason_label == "Rémunération manquante"
    assert vm.rows[0].remuneration_amount_label == "Non disponible"


def test_libelle_contrat_historique_duree_determinee_sans_date_fin():
    historical = replace(
        row(ContractSalaryControlStatus.NOT_EVALUATED),
        failure_reason=ContractSalaryEvaluationFailureReason.HISTORICAL_FIXED_TERM_MISSING_END_DATE,
        failure_message="Le contrat historique à durée déterminée ne possède pas de date de fin.",
    )

    vm = present(app((historical,)))

    assert vm.presentation_status is ContractSalaryControlPresentationStatus.WARNING
    assert vm.rows[0].failure_reason is ContractSalaryEvaluationFailureReason.HISTORICAL_FIXED_TERM_MISSING_END_DATE
    assert vm.rows[0].failure_reason_label == "Contrat historique à durée déterminée sans date de fin"
    assert vm.rows[0].failure_message_label == "Le contrat historique à durée déterminée ne possède pas de date de fin."


def test_melange_des_trois_statuts():
    vm = present(app((row(), row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("5.00")), row(ContractSalaryControlStatus.NOT_EVALUATED))))
    assert vm.global_compliant_count == 1
    assert vm.global_non_compliant_count == 1
    assert vm.global_not_evaluated_count == 1
    assert vm.presentation_status is ContractSalaryControlPresentationStatus.ERROR
    assert vm.summary_message == "1 contrat non conforme ; 1 contrat non évaluable."


def test_validite_globale_distincte_validite_filtree():
    ok = row()
    ko = row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00"))
    vm = present(app((ok,), global_rows=(ok, ko)))
    assert vm.global_valid is False
    assert vm.filtered_valid is True
    assert vm.presentation_status is ContractSalaryControlPresentationStatus.WARNING
    assert vm.summary_title == "Page filtrée conforme"


def test_resultat_filtre_vide_lot_global_invalide():
    ko = row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00"))
    vm = present(app((), global_rows=(ko,)))
    assert vm.presentation_status is ContractSalaryControlPresentationStatus.EMPTY
    assert vm.summary_title == "Aucun résultat filtré"
    assert "lot global comporte encore des anomalies" in vm.empty_state.message


def test_formatage_montants_nuls_negatifs_dates_sources_territoires():
    assert format_euro_amount(Decimal("0.00")) == "0,00 €"
    assert format_euro_amount(Decimal("-12.30")) == "-12,30 €"
    vm = present(app((row(),)))
    line = vm.rows[0]
    assert line.reference_date_label == "01/01/2026"
    assert line.minimum_source_label == "CCNS"
    assert line.territory_label == "France métropolitaine"


def test_premiere_page_page_intermediaire_derniere_page_partielle_et_sans_limite():
    rows = tuple(row(contract_id=uuid4()) for _ in range(5))
    first = present(app(rows, offset=0, limit=2, returned_rows=rows[:2])).pagination
    assert first.range_label == "Résultats 1 à 2 sur 5"
    assert first.has_next_page is True and first.next_offset == 2
    middle = present(app(rows, offset=2, limit=2, returned_rows=rows[2:4])).pagination
    assert middle.range_label == "Résultats 3 à 4 sur 5"
    assert middle.previous_offset == 0 and middle.next_offset == 4
    last = present(app(rows, offset=4, limit=2, returned_rows=rows[4:])).pagination
    assert last.range_label == "Résultats 5 à 5 sur 5"
    assert last.has_next_page is False
    no_limit = present(app(rows, offset=0, limit=None, returned_rows=rows)).pagination
    assert no_limit.limit is None
    assert no_limit.range_label == "Résultats 1 à 5 sur 5"


def test_offset_superieur_ou_egal_total_filtre():
    rows = (row(),)
    vm = present(app(rows, offset=2, limit=2, returned_rows=()))
    assert vm.pagination.range_label == "Résultats 0 à 0 sur 1"
    assert vm.pagination.first_displayed_index is None


def test_conservation_ordre_uuid_decimal_et_absence_mutation_resultat():
    r1 = row(shortfall=Decimal("0.00"))
    r2 = row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00"))
    result = app((r1, r2))
    before = result
    vm = present(result)
    assert [line.contract_id for line in vm.rows] == [r1.contract_id, r2.contract_id]
    assert vm.rows[0].id == r1.id
    assert vm.rows[1].shortfall_amount is r2.shortfall_amount
    assert result == before


def test_validation_stricte_type_entree_et_immutabilite_modeles():
    with pytest.raises(TypeError):
        ContractSalaryControlPresenter().present(object())
    with pytest.raises(TypeError):
        format_euro_amount(1.2)
    with pytest.raises(TypeError):
        present(replace(app(), reference_date=datetime(2026, 1, 1)))
    vm = present(app((row(),)))
    with pytest.raises(FrozenInstanceError):
        vm.summary_title = "x"
    with pytest.raises(FrozenInstanceError):
        vm.rows[0].status_label = "x"
    with pytest.raises(FrozenInstanceError):
        vm.pagination.offset = 9


def test_absence_appel_repository_ou_service_metier(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("service métier appelé")

    monkeypatch.setattr("domain.contracts.contract_salary_control.ContractSalaryControlService.control", forbidden)
    vm = present(app((row(),)))
    assert vm.returned_count == 1
