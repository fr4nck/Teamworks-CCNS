#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import GestionDB

from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts
from teamworks.CcnsCore.audit_sorting import compute_row_severity


def build_ccns_home_gadgets(limit=5000):
    rows = audit_contracts(limit=limit)

    nb_contracts = len(rows)
    nb_anomalies = 0
    nb_blocking_contracts = 0
    nb_warning_contracts = 0
    people_with_issues = set()
    blocking_people = set()
    warning_people = set()

    for row in rows:
        nb_anomalies += len(row.anomalies)
        severity_label, _severity_rank = compute_row_severity({
            "anomalies": row.anomalies,
        })
        person_key = (row.nom_complet or "").strip().upper() or ("CONTRAT_%s" % row.IDcontrat)

        if severity_label == "blocking":
            nb_blocking_contracts += 1
            people_with_issues.add(person_key)
            blocking_people.add(person_key)
        elif severity_label == "warning":
            nb_warning_contracts += 1
            people_with_issues.add(person_key)
            warning_people.add(person_key)

    return [
        {
            "code": "ccns_contracts_total",
            "label": u"Contrats audités CCNS",
            "value": nb_contracts,
            "severity": "neutral",
        },
        {
            "code": "ccns_anomalies_total",
            "label": u"Anomalies CCNS détectées",
            "value": nb_anomalies,
            "severity": "warning" if nb_anomalies > 0 else "ok",
        },
        {
            "code": "ccns_blocking_contracts",
            "label": u"Contrats CCNS bloquants",
            "value": nb_blocking_contracts,
            "severity": "blocking" if nb_blocking_contracts > 0 else "ok",
        },
        {
            "code": "ccns_warning_contracts",
            "label": u"Contrats CCNS à revoir",
            "value": nb_warning_contracts,
            "severity": "warning" if nb_warning_contracts > 0 else "ok",
        },
        {
            "code": "ccns_people_with_issues",
            "label": u"Individus avec alertes CCNS",
            "value": len(people_with_issues),
            "severity": "warning" if people_with_issues else "ok",
        },
        {
            "code": "ccns_people_blocking",
            "label": u"Individus avec blocages CCNS",
            "value": len(blocking_people),
            "severity": "blocking" if blocking_people else "ok",
        },
    ]


def build_ccns_home_alert_lines(limit=5000, max_lines=12):
    rows = audit_contracts(limit=limit)
    prepared = []

    for row in rows:
        severity_label, severity_rank = compute_row_severity({
            "anomalies": row.anomalies,
        })
        if severity_label == "ok":
            continue

        prepared.append({
            "IDcontrat": row.IDcontrat,
            "nom_complet": row.nom_complet,
            "classification": row.classification or "",
            "type_contrat": row.type_contrat or "",
            "severity_label": severity_label,
            "severity_rank": severity_rank,
            "anomalies": row.anomalies,
        })

    prepared.sort(key=lambda item: (
        item["severity_rank"],
        (item["nom_complet"] or "").strip().upper(),
        item["IDcontrat"],
    ))

    result = []
    for item in prepared[:max_lines]:
        label_severity = {
            "blocking": u"Bloquant",
            "warning": u"A revoir",
        }.get(item["severity_label"], item["severity_label"])
        result.append({
            "label": u"%s - contrat %s - %s" % (
                item["nom_complet"] or u"(sans nom)",
                item["IDcontrat"],
                label_severity,
            ),
            "severity": item["severity_label"],
            "contract_id": item["IDcontrat"],
            "details": u", ".join(item["anomalies"]),
        })
    return result
