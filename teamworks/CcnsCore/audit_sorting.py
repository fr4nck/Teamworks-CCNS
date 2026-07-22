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

SALARY_SORT_FIELDS = {
    "Statut salarial": "salary_control_status",
    "Rémunération contrôlée": "remuneration_amount",
    "Minimum applicable": "applicable_minimum_amount",
    "Source": "minimum_source",
    "Écart": "shortfall_amount",
}

_STATUS_RANK = {"compliant": 0, "non_compliant": 1, "not_evaluated": 2}
_SOURCE_RANK = {"ccns": 0, "smic": 1, "equal": 2}


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


def sort_audit_rows_by_salary(rows, field, descending=False):
    """Trie une copie des lignes, avec les valeurs absentes toujours à la fin."""
    if field not in SALARY_SORT_FIELDS.values():
        raise ValueError("Champ de tri salarial inconnu : %s" % field)

    available = [row for row in rows if row.get(field) is not None]
    missing = [row for row in rows if row.get(field) is None]

    def key(row):
        value = row[field]
        raw_value = getattr(value, "value", value)
        if field == "salary_control_status":
            return _STATUS_RANK.get(raw_value, len(_STATUS_RANK))
        if field == "minimum_source":
            return _SOURCE_RANK.get(raw_value, len(_SOURCE_RANK))
        return value

    return sorted(available, key=key, reverse=descending) + missing
