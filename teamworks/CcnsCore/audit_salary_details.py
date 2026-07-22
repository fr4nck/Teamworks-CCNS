#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from decimal import Decimal

from application.presentation import format_euro_amount
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus


CSV_HEADERS = (
    "Nom",
    "Gravite",
    "IDcontrat",
    "Classification",
    "Type contrat",
    "Salaire base",
    "Statut salarial",
    "Rémunération contrôlée",
    "Minimum applicable",
    "Source",
    "Écart",
    "Nb anomalies",
    "Anomalies",
    "Messages",
)


def audit_row_to_dict(row):
    """Adapte une AuditRow à l'écran sans convertir ses Decimal."""
    return {
        "IDcontrat": row.IDcontrat,
        "nom_complet": row.nom_complet,
        "classification": row.classification or "",
        "type_contrat": row.type_contrat or "",
        "salaire_base": row.salaire_base,
        "anomalies": row.anomalies,
        "messages": row.messages,
        "reference_date": row.reference_date,
        "salary_control_status": row.salary_control_status,
        "salary_control_status_label": row.salary_control_status_label or "",
        "remuneration_amount": row.remuneration_amount,
        "remuneration_amount_label": row.remuneration_amount_label or "",
        "applicable_minimum_amount": row.applicable_minimum_amount,
        "applicable_minimum_amount_label": row.applicable_minimum_amount_label or "",
        "shortfall_amount": row.shortfall_amount,
        "shortfall_amount_label": row.shortfall_amount_label or "",
        "minimum_source": row.minimum_source,
        "minimum_source_label": row.minimum_source_label or "",
        "salary_control_row": row.salary_control_row,
    }


def summarize_salary_control_rows(rows):
    compliant = 0
    non_compliant = 0
    not_evaluated = 0
    total_shortfall = Decimal("0.00")

    for row in rows:
        status = row.get("salary_control_status")
        if status is ContractSalaryControlStatus.COMPLIANT:
            compliant += 1
        elif status is ContractSalaryControlStatus.NON_COMPLIANT:
            non_compliant += 1
        elif status is ContractSalaryControlStatus.NOT_EVALUATED:
            not_evaluated += 1
        amount = row.get("shortfall_amount")
        if amount is not None:
            if type(amount) is not Decimal:
                raise TypeError("shortfall_amount doit rester un Decimal strict.")
            total_shortfall += amount

    return {
        "compliant_count": compliant,
        "non_compliant_count": non_compliant,
        "not_evaluated_count": not_evaluated,
        "total_shortfall_amount": total_shortfall,
        "total_shortfall_amount_label": format_euro_amount(total_shortfall),
    }


def write_audit_csv(file_object, rows):
    """Exporte les lignes déjà filtrées sans relancer ni recalculer l'audit."""
    writer = csv.writer(file_object, delimiter=";")
    writer.writerow(CSV_HEADERS)
    severity_labels = {"blocking": "Bloquant", "warning": "A revoir", "ok": "OK"}
    for row in rows:
        writer.writerow((
            row["nom_complet"],
            severity_labels.get(row.get("severity_label", "ok"), ""),
            row["IDcontrat"],
            row["classification"],
            row["type_contrat"],
            row["salaire_base"] if row["salaire_base"] is not None else "",
            row.get("salary_control_status_label", ""),
            row.get("remuneration_amount_label", ""),
            row.get("applicable_minimum_amount_label", ""),
            row.get("minimum_source_label", ""),
            row.get("shortfall_amount_label", ""),
            len(row["anomalies"]),
            ", ".join(row["anomalies"]),
            " | ".join(row["messages"]),
        ))
