from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from application.presentation import (
    ContractSalaryControlDetailPresenter,
    ContractSalaryControlRowViewModel,
    detail_from_audit_row,
)
from domain.contracts import ContractSalaryControlStatus
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory
from teamworks.CcnsCore.audit_contracts_ccns import AuditRow
from teamworks.CcnsCore.audit_filters import filter_audit_rows
from teamworks.CcnsCore.audit_sorting import sort_audit_rows_by_salary

D = date(2026, 7, 1)


def salary_row(status=ContractSalaryControlStatus.COMPLIANT, *, shortfall=Decimal("0.00")):
    kwargs = dict(
        id=uuid4(),
        contract_id=uuid4(),
        contract_id_label="42",
        employee_id=uuid4(),
        employee_id_label="101",
        reference_date=D,
        reference_date_label="01/07/2026",
        status=status,
        status_label={
            ContractSalaryControlStatus.COMPLIANT: "Conforme",
            ContractSalaryControlStatus.NON_COMPLIANT: "Non conforme",
            ContractSalaryControlStatus.NOT_EVALUATED: "Non évaluable",
        }[status],
        classification_code="G3",
        classification_code_label="G3",
        remuneration_amount=Decimal("1800.10"),
        remuneration_amount_label="1 800,10 €",
        applicable_minimum_amount=Decimal("1997.87"),
        applicable_minimum_amount_label="1 997,87 €",
        shortfall_amount=shortfall,
        shortfall_amount_label="197,77 €" if shortfall else "0,00 €",
        minimum_source=ApplicableSalaryMinimumSource.CCNS,
        minimum_source_label="CCNS",
        territory=SmicTerritory.METROPOLITAN_FRANCE,
        territory_label="France métropolitaine",
        failure_reason=None,
        failure_reason_label="",
        failure_message=None,
        failure_message_label="",
        issue_code=None,
        issue_code_label="",
        issue_message=None,
        issue_message_label="",
    )
    if status is ContractSalaryControlStatus.NON_COMPLIANT:
        kwargs.update(issue_code="REMUNERATION_BELOW_APPLICABLE_MINIMUM", issue_code_label="REMUNERATION_BELOW_APPLICABLE_MINIMUM", issue_message="La rémunération brute mensuelle est inférieure au minimum salarial applicable.", issue_message_label="La rémunération brute mensuelle est inférieure au minimum salarial applicable.")
    if status is ContractSalaryControlStatus.NOT_EVALUATED:
        kwargs.update(remuneration_amount=None, remuneration_amount_label="Non disponible", applicable_minimum_amount=None, applicable_minimum_amount_label="Non disponible", shortfall_amount=Decimal("0.00"), shortfall_amount_label="0,00 €", minimum_source=None, minimum_source_label="Non disponible", failure_reason=ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION, failure_reason_label="Rémunération manquante", failure_message="Le contrat ne possède pas de rémunération exploitable.", failure_message_label="Le contrat ne possède pas de rémunération exploitable.")
    return ContractSalaryControlRowViewModel(**kwargs)


def test_detail_conforme_conserve_valeurs_brutes_et_libelles_sans_recalcul(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("contrôleur ou repository appelé")

    monkeypatch.setattr("domain.contracts.contract_salary_control.ContractSalaryControlService.control", forbidden)
    row = salary_row()
    detail = ContractSalaryControlDetailPresenter().present(row)
    assert detail.contract_id is row.contract_id
    assert detail.employee_id is row.employee_id
    assert detail.reference_date is D
    assert detail.status is ContractSalaryControlStatus.COMPLIANT
    assert detail.remuneration_amount is row.remuneration_amount
    assert type(detail.remuneration_amount) is Decimal
    assert detail.shortfall_amount == Decimal("0.00")
    assert detail.issue_code is None


def test_detail_non_conforme_conserve_ecart_anomalie_source_territoire():
    row = salary_row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("197.77"))
    detail = ContractSalaryControlDetailPresenter().present(row)
    assert detail.status is ContractSalaryControlStatus.NON_COMPLIANT
    assert detail.shortfall_amount is row.shortfall_amount
    assert detail.minimum_source is ApplicableSalaryMinimumSource.CCNS
    assert detail.territory is SmicTerritory.METROPOLITAN_FRANCE
    assert detail.issue_code == "REMUNERATION_BELOW_APPLICABLE_MINIMUM"
    assert detail.issue_message == "La rémunération brute mensuelle est inférieure au minimum salarial applicable."


def test_detail_non_evaluable_conserve_motif_message_et_n_invente_pas_de_minimum():
    row = salary_row(ContractSalaryControlStatus.NOT_EVALUATED)
    detail = ContractSalaryControlDetailPresenter().present(row)
    assert detail.status is ContractSalaryControlStatus.NOT_EVALUATED
    assert detail.failure_reason is ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION
    assert detail.failure_message == "Le contrat ne possède pas de rémunération exploitable."
    assert detail.applicable_minimum_amount is None
    assert detail.minimum_source is None


def test_detail_refuse_type_invalide_et_modele_immutable():
    with pytest.raises(TypeError):
        ContractSalaryControlDetailPresenter().present(object())
    detail = ContractSalaryControlDetailPresenter().present(salary_row())
    with pytest.raises(FrozenInstanceError):
        detail.status_label = "x"


def test_audit_row_conserve_reference_correcte_et_compatibilite_positionnelle():
    row = salary_row()
    audit_row = AuditRow(1, "Ada Lovelace", "G3", "CDI", 2100.0, [], [], salary_control_row=row)
    assert audit_row.IDcontrat == 1
    assert audit_row.salary_control_row is row
    assert detail_from_audit_row(audit_row).contract_id is row.contract_id


def test_filtres_et_tris_conservent_le_lien_detail():
    row = salary_row(ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("197.77"))
    data = [{"IDcontrat": 1, "classification": "G3", "type_contrat": "CDI", "salaire_base": 1800.10, "anomalies": ["A"], "salary_control_status": row.status, "minimum_source": row.minimum_source, "shortfall_amount": row.shortfall_amount, "salary_control_row": row}]
    filtered = filter_audit_rows(data, salary_control_status=ContractSalaryControlStatus.NON_COMPLIANT)
    sorted_rows = sort_audit_rows_by_salary(filtered, "shortfall_amount")
    assert sorted_rows[0]["salary_control_row"] is row
    assert detail_from_audit_row(sorted_rows[0]).issue_code == "REMUNERATION_BELOW_APPLICABLE_MINIMUM"


def test_comportement_sans_detail_disponible():
    with pytest.raises(ValueError, match="Aucun détail salarial"):
        detail_from_audit_row({"IDcontrat": 1})
