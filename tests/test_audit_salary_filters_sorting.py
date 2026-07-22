from copy import deepcopy
from decimal import Decimal

import pytest

from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.convention import ApplicableSalaryMinimumSource
from teamworks.CcnsCore.audit_filters import filter_audit_rows
from teamworks.CcnsCore.audit_salary_details import summarize_salary_control_rows
from teamworks.CcnsCore.audit_sorting import sort_audit_rows_by_salary


def _row(identifier, status, source, remuneration, minimum, shortfall, **extra):
    row = {
        "IDcontrat": identifier,
        "classification": "G3",
        "type_contrat": "CDI",
        "salaire_base": 2000.0,
        "anomalies": [],
        "salary_control_status": status,
        "minimum_source": source,
        "remuneration_amount": remuneration,
        "applicable_minimum_amount": minimum,
        "shortfall_amount": shortfall,
    }
    row.update(extra)
    return row


ROWS = [
    _row(1, ContractSalaryControlStatus.COMPLIANT, ApplicableSalaryMinimumSource.CCNS, Decimal("2100.00"), Decimal("1997.87"), Decimal("0.00")),
    _row(2, ContractSalaryControlStatus.NON_COMPLIANT, ApplicableSalaryMinimumSource.SMIC, Decimal("1800.00"), Decimal("1867.02"), Decimal("67.02"), anomalies=["A"]),
    _row(3, ContractSalaryControlStatus.COMPLIANT, ApplicableSalaryMinimumSource.EQUAL, Decimal("1867.02"), Decimal("1867.02"), Decimal("0.00"), type_contrat="CDD"),
    _row(4, ContractSalaryControlStatus.NOT_EVALUATED, None, None, None, Decimal("0.00")),
]


@pytest.mark.parametrize(("argument", "value", "expected"), [
    ("salary_control_status", ContractSalaryControlStatus.COMPLIANT, [1, 3]),
    ("salary_control_status", ContractSalaryControlStatus.NON_COMPLIANT, [2]),
    ("salary_control_status", ContractSalaryControlStatus.NOT_EVALUATED, [4]),
    ("minimum_source", ApplicableSalaryMinimumSource.CCNS, [1]),
    ("minimum_source", ApplicableSalaryMinimumSource.SMIC, [2]),
    ("minimum_source", ApplicableSalaryMinimumSource.EQUAL, [3]),
    ("minimum_source", "unavailable", [4]),
    ("positive_shortfall_only", True, [2]),
])
def test_filtres_salariaux(argument, value, expected):
    assert [row["IDcontrat"] for row in filter_audit_rows(ROWS, **{argument: value})] == expected


def test_combinaison_avec_filtres_historiques_et_total_decimal_exact():
    filtered = filter_audit_rows(
        ROWS,
        anomalies_only=True,
        classification_filter="G3",
        salary_control_status=ContractSalaryControlStatus.NON_COMPLIANT,
        positive_shortfall_only=True,
    )
    summary = summarize_salary_control_rows(filtered)
    assert [row["IDcontrat"] for row in filtered] == [2]
    assert summary["total_shortfall_amount"] == Decimal("67.02")
    assert type(summary["total_shortfall_amount"]) is Decimal


@pytest.mark.parametrize("field", [
    "salary_control_status", "remuneration_amount", "applicable_minimum_amount", "minimum_source", "shortfall_amount",
])
def test_tris_salariaux_ascendants_descendants_stables_absents_en_dernier(field):
    rows = [dict(row) for row in ROWS]
    rows.append(dict(rows[0], IDcontrat=5))
    before = deepcopy(rows)

    ascending = sort_audit_rows_by_salary(rows, field)
    descending = sort_audit_rows_by_salary(rows, field, descending=True)

    missing_ids = [row["IDcontrat"] for row in rows if row.get(field) is None]
    if missing_ids:
        assert [row["IDcontrat"] for row in ascending[-len(missing_ids):]] == missing_ids
        assert [row["IDcontrat"] for row in descending[-len(missing_ids):]] == missing_ids
    expected_equal_ids = [row["IDcontrat"] for row in rows if row.get(field) == rows[0].get(field)]
    assert [row["IDcontrat"] for row in ascending if row.get(field) == rows[0].get(field)] == expected_equal_ids
    assert [row["IDcontrat"] for row in descending if row.get(field) == rows[0].get(field)] == expected_equal_ids
    assert rows == before


def test_tri_refuse_un_champ_inconnu():
    with pytest.raises(ValueError):
        sort_audit_rows_by_salary(ROWS, "salaire_recalcule")
