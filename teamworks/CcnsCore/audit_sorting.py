#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations


BLOCKING_CODES = {
    "CONTRAT_SANS_CLASSIFICATION",
    "CONTRAT_SANS_GRILLE",
    "CEE_DEPASSEMENT_80_JOURS",
    "REGLE_INTROUVABLE",
    "REMUNERATION_BELOW_APPLICABLE_MINIMUM",
    "CONTROLE_SALARIAL_NON_EVALUABLE_MISSING_CLASSIFICATION",
    "CONTROLE_SALARIAL_NON_EVALUABLE_MISSING_REMUNERATION",
}

WARNING_CODES = {
    "MINIMUM_CCNS_NON_ATTEINT",
    "ANCIENNETE_OUBLIEE",
    "ANCIENNETE_INFERIEURE_THEORIQUE",
    "ANCIENNETE_APPLIQUEE_A_TORT",
    "REMUNERATION_BASE_ABSENTE",
    "MINIMUM_THEORIQUE_NON_CALCULABLE",
}


def compute_row_severity(row):
    anomalies = row.get("anomalies") or []
    if any(code in BLOCKING_CODES for code in anomalies):
        return "blocking", 0
    if anomalies:
        return "warning", 1
    return "ok", 2


def sort_audit_rows_by_person_and_severity(rows):
    def key(row):
        nom = (row.get("nom_complet") or "").strip().upper()
        severity_label, severity_rank = compute_row_severity(row)
        contract_id = row.get("IDcontrat") or 0
        return (nom, severity_rank, contract_id)

    return sorted(rows, key=key)
