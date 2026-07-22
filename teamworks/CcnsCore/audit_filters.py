#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.convention import ApplicableSalaryMinimumSource


def filter_audit_rows(
    rows,
    anomalies_only=False,
    classification_filter="",
    contract_type_filter="",
    min_salary=None,
    max_salary=None,
    salary_control_status=None,
    minimum_source=None,
    positive_shortfall_only=False,
):
    classification_filter = (classification_filter or "").strip().upper()
    contract_type_filter = (contract_type_filter or "").strip().upper()

    filtered = []
    for row in rows:
        classification = (row.get("classification") or "").upper()
        contract_type = (row.get("type_contrat") or "").upper()
        anomalies = row.get("anomalies") or []
        salary = row.get("salaire_base")

        if anomalies_only and not anomalies:
            continue
        if classification_filter and classification != classification_filter:
            continue
        if contract_type_filter and contract_type != contract_type_filter:
            continue
        if min_salary is not None and salary is not None and float(salary) < float(min_salary):
            continue
        if max_salary is not None and salary is not None and float(salary) > float(max_salary):
            continue
        if salary_control_status is not None and row.get("salary_control_status") is not salary_control_status:
            continue
        if minimum_source == "unavailable":
            if row.get("minimum_source") is not None:
                continue
        elif minimum_source is not None and row.get("minimum_source") is not minimum_source:
            continue
        if positive_shortfall_only:
            shortfall = row.get("shortfall_amount")
            if shortfall is None or shortfall <= 0:
                continue
        filtered.append(row)
    return filtered


SALARY_STATUS_FILTERS = {
    "Conforme": ContractSalaryControlStatus.COMPLIANT,
    "Non conforme": ContractSalaryControlStatus.NON_COMPLIANT,
    "Non évaluable": ContractSalaryControlStatus.NOT_EVALUATED,
}

MINIMUM_SOURCE_FILTERS = {
    "CCNS": ApplicableSalaryMinimumSource.CCNS,
    "SMIC": ApplicableSalaryMinimumSource.SMIC,
    "CCNS et SMIC": ApplicableSalaryMinimumSource.EQUAL,
    "Non disponible": "unavailable",
}
