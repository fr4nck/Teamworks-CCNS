#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations


def filter_audit_rows(
    rows,
    anomalies_only=False,
    classification_filter="",
    contract_type_filter="",
    min_salary=None,
    max_salary=None,
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
        filtered.append(row)
    return filtered
