#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import time

from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts
from teamworks.CcnsCore.audit_sorting import compute_row_severity

_CACHE_TTL_SECONDS = 45.0
_cache_home_data = {}
_LOGGER = logging.getLogger(__name__)


def clear_ccns_home_cache():
    """Vide explicitement le cache mémoire des données d'accueil CCNS."""
    _cache_home_data.clear()


def _cache_key(limit, max_lines):
    return (int(limit) if limit is not None else None, int(max_lines))


def _build_stats(rows):
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


def _build_alert_lines(rows, max_lines=12):
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


def build_ccns_home_data(limit=5000, max_lines=12, force_refresh=False):
    """Construit les statistiques et alertes CCNS avec un seul audit.

    Le résultat est conservé en mémoire pendant une courte durée. Le cache est
    volontairement simple, non persistant et invalidable via ``force_refresh``
    ou ``clear_ccns_home_cache``.
    """
    key = _cache_key(limit, max_lines)
    now = time.monotonic()
    cached = _cache_home_data.get(key)
    if not force_refresh and cached and now - cached["created_at"] < _CACHE_TTL_SECONDS:
        return cached["data"]

    start = time.perf_counter()
    rows = audit_contracts(limit=limit)
    data = {
        "stats": _build_stats(rows),
        "alerts": _build_alert_lines(rows, max_lines=max_lines),
    }
    _cache_home_data[key] = {"created_at": time.monotonic(), "data": data}
    _LOGGER.debug("Données accueil CCNS construites en %.3fs", time.perf_counter() - start)
    return data


def refresh_ccns_home_data(limit=5000, max_lines=12):
    """Renouvelle explicitement les données d'accueil CCNS."""
    return build_ccns_home_data(limit=limit, max_lines=max_lines, force_refresh=True)


def build_ccns_home_gadgets(limit=5000, force_refresh=False):
    return build_ccns_home_data(limit=limit, force_refresh=force_refresh)["stats"]


def build_ccns_home_alert_lines(limit=5000, max_lines=12, force_refresh=False):
    return build_ccns_home_data(limit=limit, max_lines=max_lines, force_refresh=force_refresh)["alerts"]
