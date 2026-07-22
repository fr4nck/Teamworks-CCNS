from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import StringIO
from types import SimpleNamespace
from uuid import uuid4

import pytest

from application.presentation import ContractSalaryControlRowViewModel
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.convention import ApplicableSalaryMinimumSource
from domain.repositories.ccns_data import CcnsContratRecord, CcnsGrilleRecord, CcnsLigneGrilleRecord
from teamworks.CcnsCore import audit_contracts_ccns as audit_module
from teamworks.CcnsCore.audit_contracts_ccns import AuditRow, audit_contracts
from teamworks.CcnsCore.audit_salary_details import audit_row_to_dict, summarize_salary_control_rows, write_audit_csv
from infrastructure.persistence.teamworks_contract_salary_control_provider import legacy_contract_uuid


REFERENCE_DATE = date(2026, 7, 1)


class Reader:
    def __init__(self, contracts, minimum=Decimal("1997.87")):
        self.contracts = contracts
        self.minimum = minimum
        self.calls = []

    def lire_contrats(self, limit=None):
        self.calls.append(("contrats", limit))
        return list(self.contracts)

    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return [CcnsGrilleRecord(7, "CCNS-2026", "Grille 2026", "CCNS", "standard", date(2026, 1, 1), None, "test")]

    def lire_lignes_grille(self, IDtw_salary_grid):
        self.calls.append(("lignes", IDtw_salary_grid))
        return [CcnsLigneGrilleRecord(8, 7, "G3", "monthly", self.minimum, "EUR", None, None, None, None, "")]


class ReaderWithoutGrid(Reader):
    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return []

    def lire_lignes_grille(self, IDtw_salary_grid):
        raise AssertionError("aucune ligne de grille ne doit être lue")


def contract(IDcontrat=1, salary=Decimal("2100.00")):
    return CcnsContratRecord(
        IDcontrat,
        100 + IDcontrat,
        date(2026, 1, 1),
        None,
        salary,
        Decimal("35.00"),
        Decimal("0.00"),
        "Ada",
        "Lovelace",
        "G3",
        "CDI",
    )


@pytest.mark.parametrize(
    ("minimum", "salary", "expected_source", "expected_source_label", "expected_minimum", "expected_status", "expected_shortfall"),
    (
        (Decimal("1997.87"), Decimal("2100.00"), ApplicableSalaryMinimumSource.CCNS, "CCNS", Decimal("1997.87"), ContractSalaryControlStatus.COMPLIANT, Decimal("0.00")),
        (Decimal("1800.00"), Decimal("2100.00"), ApplicableSalaryMinimumSource.SMIC, "SMIC", Decimal("1867.02"), ContractSalaryControlStatus.COMPLIANT, Decimal("0.00")),
        (Decimal("1867.02"), Decimal("2100.00"), ApplicableSalaryMinimumSource.EQUAL, "CCNS et SMIC", Decimal("1867.02"), ContractSalaryControlStatus.COMPLIANT, Decimal("0.00")),
        (Decimal("1997.87"), Decimal("1800.00"), ApplicableSalaryMinimumSource.CCNS, "CCNS", Decimal("1997.87"), ContractSalaryControlStatus.NON_COMPLIANT, Decimal("197.87")),
    ),
)
def test_audit_expose_minimum_source_statut_et_ecart_du_view_model(
    minimum,
    salary,
    expected_source,
    expected_source_label,
    expected_minimum,
    expected_status,
    expected_shortfall,
):
    row = audit_contracts(
        data_reader=Reader([contract(salary=salary)], minimum=minimum),
        reference_date=REFERENCE_DATE,
    )[0]

    assert row.reference_date == REFERENCE_DATE
    assert row.salary_control_status is expected_status
    assert row.remuneration_amount == salary
    assert type(row.remuneration_amount) is Decimal
    assert row.applicable_minimum_amount == expected_minimum
    assert type(row.applicable_minimum_amount) is Decimal
    assert row.minimum_source is expected_source
    assert row.minimum_source_label == expected_source_label
    assert row.shortfall_amount == expected_shortfall
    assert type(row.shortfall_amount) is Decimal
    assert row.salary_control_status_label in {"Conforme", "Non conforme"}
    assert row.remuneration_amount_label.endswith(" €")
    assert row.applicable_minimum_amount_label.endswith(" €")
    assert row.shortfall_amount_label.endswith(" €")


def test_audit_non_evaluable_et_base_sans_grille_exposent_les_libelles_attendus():
    missing_salary = audit_contracts(
        data_reader=Reader([contract(salary=None)]),
        reference_date=REFERENCE_DATE,
    )[0]
    no_grid = audit_contracts(
        data_reader=ReaderWithoutGrid([contract()]),
        reference_date=REFERENCE_DATE,
    )[0]

    assert missing_salary.salary_control_status is ContractSalaryControlStatus.NOT_EVALUATED
    assert missing_salary.salary_control_status_label == "Non évaluable"
    assert missing_salary.remuneration_amount is None
    assert missing_salary.remuneration_amount_label == "Non disponible"
    assert no_grid.anomalies[0] == "CONTRAT_SANS_GRILLE"
    assert no_grid.salary_control_status is ContractSalaryControlStatus.NOT_EVALUATED
    assert no_grid.salary_control_status_label == "Non évaluable"
    assert no_grid.applicable_minimum_amount is None
    assert no_grid.applicable_minimum_amount_label == "Non disponible"
    assert no_grid.minimum_source is None
    assert no_grid.minimum_source_label == "Non disponible"


def test_audit_copie_exactement_les_decimal_et_libelles_du_view_model_sans_second_controle(monkeypatch):
    record = contract()
    before = deepcopy(record)
    reader = Reader([record])
    control_row = ContractSalaryControlRowViewModel(
        id=uuid4(),
        contract_id=legacy_contract_uuid(record.IDcontrat),
        contract_id_label="contrat affiché",
        employee_id=None,
        employee_id_label="salarié affiché",
        reference_date=REFERENCE_DATE,
        reference_date_label="date affichée",
        status=ContractSalaryControlStatus.NON_COMPLIANT,
        status_label="statut affiché",
        classification_code="G3",
        classification_code_label="groupe affiché",
        remuneration_amount=Decimal("2000.101"),
        remuneration_amount_label="rémunération affichée",
        applicable_minimum_amount=Decimal("2000.302"),
        applicable_minimum_amount_label="minimum affiché",
        shortfall_amount=Decimal("0.201"),
        shortfall_amount_label="écart affiché",
        minimum_source=ApplicableSalaryMinimumSource.EQUAL,
        minimum_source_label="source affichée",
        territory=None,
        territory_label="territoire affiché",
        failure_reason=None,
        failure_reason_label="",
        failure_message=None,
        failure_message_label="",
        issue_code="ANOMALIE_TEST",
        issue_code_label="anomalie affichée",
        issue_message="Message test.",
        issue_message_label="message affiché",
    )
    execute_calls = []

    class Controller:
        def execute(self, request):
            execute_calls.append(request)
            return SimpleNamespace(successful=True, view_model=SimpleNamespace(rows=(control_row,)), errors=())

    monkeypatch.setattr(
        audit_module.ContractSalaryControlControllerFactory,
        "create_from_provider",
        lambda self, **kwargs: Controller(),
    )

    row = audit_contracts(data_reader=reader, reference_date=REFERENCE_DATE)[0]

    assert execute_calls and len(execute_calls) == 1
    assert reader.calls.count(("contrats", None)) == 1
    assert record == before
    assert row.remuneration_amount is control_row.remuneration_amount
    assert row.applicable_minimum_amount is control_row.applicable_minimum_amount
    assert row.shortfall_amount is control_row.shortfall_amount
    assert row.salary_control_status_label == "statut affiché"
    assert row.remuneration_amount_label == "rémunération affichée"
    assert row.applicable_minimum_amount_label == "minimum affiché"
    assert row.shortfall_amount_label == "écart affiché"
    assert row.minimum_source_label == "source affichée"


def test_audit_row_conserve_ses_sept_parametres_positionnels_historiques():
    row = AuditRow(1, "Ada Lovelace", "G3", "CDI", 2100.0, [], [])

    assert row.IDcontrat == 1
    assert row.messages == []
    assert row.reference_date is None
    assert row.salary_control_status is None
    assert row.remuneration_amount is None
    assert row.minimum_source is None


def test_resume_des_lignes_filtrees_totalise_les_ecarts_en_decimal_exact():
    rows = [
        {"salary_control_status": ContractSalaryControlStatus.COMPLIANT, "shortfall_amount": Decimal("0.00")},
        {"salary_control_status": ContractSalaryControlStatus.NON_COMPLIANT, "shortfall_amount": Decimal("10.10")},
        {"salary_control_status": ContractSalaryControlStatus.NOT_EVALUATED, "shortfall_amount": Decimal("0.00")},
        {"salary_control_status": ContractSalaryControlStatus.NON_COMPLIANT, "shortfall_amount": Decimal("0.20")},
    ]

    summary = summarize_salary_control_rows(rows[1:])

    assert summary["compliant_count"] == 0
    assert summary["non_compliant_count"] == 2
    assert summary["not_evaluated_count"] == 1
    assert summary["total_shortfall_amount"] == Decimal("10.30")
    assert type(summary["total_shortfall_amount"]) is Decimal
    assert summary["total_shortfall_amount_label"] == "10,30 €"


def test_export_csv_reprend_les_lignes_preparees_sans_relancer_audit(monkeypatch):
    row = AuditRow(
        1,
        "Ada Lovelace",
        "G3",
        "CDI",
        1800.0,
        ["REMUNERATION_BELOW_APPLICABLE_MINIMUM"],
        ["Message"],
        REFERENCE_DATE,
        ContractSalaryControlStatus.NON_COMPLIANT,
        "Non conforme",
        Decimal("1800.00"),
        "1 800,00 €",
        Decimal("1997.87"),
        "1 997,87 €",
        Decimal("197.87"),
        "197,87 €",
        ApplicableSalaryMinimumSource.CCNS,
        "CCNS",
    )
    prepared = audit_row_to_dict(row)
    prepared["severity_label"] = "blocking"
    monkeypatch.setattr(audit_module, "audit_contracts", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("audit relancé")))
    output = StringIO(newline="")

    write_audit_csv(output, [prepared])

    csv_text = output.getvalue()
    assert "Statut salarial;Rémunération contrôlée;Minimum applicable;Source;Écart" in csv_text
    assert "Non conforme;1 800,00 €;1 997,87 €;CCNS;197,87 €" in csv_text
    assert prepared["remuneration_amount"] == Decimal("1800.00")
    assert prepared["applicable_minimum_amount"] == Decimal("1997.87")
