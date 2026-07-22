#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from uuid import UUID

from application.presentation import (
    ContractSalaryControlEmployeeSummaryPresenter,
    ContractSalaryControlRowViewModel,
)


def employee_salary_summary_from_audit_rows(rows, employee_id):
    """Construit une synthèse salariale depuis les lignes d'audit déjà chargées."""
    if type(employee_id) is not UUID:
        raise TypeError("employee_id doit être un UUID strict.")
    salary_rows = []
    for row in rows:
        if isinstance(row, dict):
            salary_row = row.get("salary_control_row")
        else:
            salary_row = getattr(row, "salary_control_row", None)
        if salary_row is None:
            continue
        if type(salary_row) is not ContractSalaryControlRowViewModel:
            raise TypeError("salary_control_row doit être un ContractSalaryControlRowViewModel strict.")
        salary_rows.append(salary_row)
    return ContractSalaryControlEmployeeSummaryPresenter().present(tuple(salary_rows), employee_id)
