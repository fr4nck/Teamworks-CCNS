#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from application.presentation import ContractSalaryControlRowViewModel, ContractSalaryDashboardPresenter


def salary_dashboard_from_audit_rows(rows):
    """Construit le tableau de bord salarial depuis les lignes d'audit déjà chargées."""
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
    return ContractSalaryDashboardPresenter().present(tuple(salary_rows))
