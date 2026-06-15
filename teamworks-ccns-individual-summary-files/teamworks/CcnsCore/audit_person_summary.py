#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import GestionDB

from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts
from teamworks.CcnsCore.audit_sorting import compute_row_severity


def get_person_contract_ids(IDpersonne):
    db = GestionDB.DB()
    req = "SELECT IDcontrat FROM contrats WHERE IDpersonne=%d ORDER BY IDcontrat;" % int(IDpersonne)
    db.ExecuterReq(req)
    rows = db.ResultatReq()
    db.Close()
    return [row[0] for row in rows]


def build_person_ccns_summary(IDpersonne):
    contract_ids = set(get_person_contract_ids(IDpersonne))
    all_rows = audit_contracts(limit=100000)

    rows = []
    for row in all_rows:
        if row.IDcontrat in contract_ids:
            rows.append({
                "IDcontrat": row.IDcontrat,
                "nom_complet": row.nom_complet,
                "classification": row.classification or "",
                "type_contrat": row.type_contrat or "",
                "salaire_base": row.salaire_base,
                "anomalies": row.anomalies,
                "messages": row.messages,
            })

    for row in rows:
        severity_label, severity_rank = compute_row_severity(row)
        row["severity_label"] = severity_label
        row["severity_rank"] = severity_rank

    nb_contracts = len(rows)
    nb_anomalies = sum(len(row.get("anomalies", [])) for row in rows)
    nb_blocking = sum(1 for row in rows if row.get("severity_label") == "blocking")
    nb_warning = sum(1 for row in rows if row.get("severity_label") == "warning")
    nb_ok = sum(1 for row in rows if row.get("severity_label") == "ok")

    global_status = "OK"
    if nb_blocking > 0:
        global_status = "BLOQUANT"
    elif nb_warning > 0:
        global_status = "A_REVOIR"
    elif nb_contracts == 0:
        global_status = "AUCUN_CONTRAT"

    return {
        "IDpersonne": IDpersonne,
        "nb_contracts": nb_contracts,
        "nb_anomalies": nb_anomalies,
        "nb_blocking": nb_blocking,
        "nb_warning": nb_warning,
        "nb_ok": nb_ok,
        "global_status": global_status,
        "rows": rows,
    }
