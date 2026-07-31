#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations


def build_ccns_tree_nodes(IDpersonne):
    # Import différé : les fonctions de formatage de ce module doivent rester
    # importables même lorsque le moteur de synthèse CCNS n'est pas disponible.
    from teamworks.CcnsCore.audit_person_summary import build_person_ccns_summary

    summary = build_person_ccns_summary(IDpersonne)

    nodes = []
    if summary["nb_contracts"] == 0:
        return nodes

    if summary["nb_blocking"] > 0:
        nodes.append({
            "type": "ccns_blocking",
            "label": u"%d alerte(s) CCNS bloquante(s)" % summary["nb_blocking"],
            "severity": "blocking",
            "contract_ids": [
                row["IDcontrat"] for row in summary["rows"]
                if row.get("severity_label") == "blocking"
            ],
        })

    if summary["nb_warning"] > 0:
        nodes.append({
            "type": "ccns_warning",
            "label": u"%d contrat(s) CCNS à revoir" % summary["nb_warning"],
            "severity": "warning",
            "contract_ids": [
                row["IDcontrat"] for row in summary["rows"]
                if row.get("severity_label") == "warning"
            ],
        })

    if summary["nb_ok"] > 0:
        nodes.append({
            "type": "ccns_ok",
            "label": u"%d contrat(s) CCNS sans anomalie détectée" % summary["nb_ok"],
            "severity": "ok",
            "contract_ids": [
                row["IDcontrat"] for row in summary["rows"]
                if row.get("severity_label") == "ok"
            ],
        })

    all_contract_ids = [row["IDcontrat"] for row in summary["rows"]]
    nodes.append({
        "type": "ccns_summary",
        "label": u"Synthèse CCNS : %s" % _format_global_status(summary["global_status"]),
        "severity": _map_global_severity(summary["global_status"]),
        "contract_ids": all_contract_ids,
    })

    return nodes


def _format_global_status(status):
    return {
        "BLOQUANT": u"bloquant",
        "A_REVOIR": u"à revoir",
        "OK": u"ok",
        "AUCUN_CONTRAT": u"aucun contrat",
    }.get(status, status)


def _map_global_severity(status):
    return {
        "BLOQUANT": "blocking",
        "A_REVOIR": "warning",
        "OK": "ok",
        "AUCUN_CONTRAT": "neutral",
    }.get(status, "neutral")
