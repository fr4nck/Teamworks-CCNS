#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from datetime import date

import GestionDB


CCNS_CLASSIFICATIONS = [
    {"code": "G1", "label": "Groupe 1", "family": "ccns", "level": "1"},
    {"code": "G2", "label": "Groupe 2", "family": "ccns", "level": "2"},
    {"code": "G3", "label": "Groupe 3", "family": "ccns", "level": "3"},
    {"code": "G4", "label": "Groupe 4", "family": "ccns", "level": "4"},
    {"code": "G5", "label": "Groupe 5", "family": "ccns", "level": "5"},
    {"code": "G6", "label": "Groupe 6", "family": "ccns", "level": "6"},
    {"code": "G7", "label": "Groupe 7", "family": "ccns", "level": "7"},
    {"code": "G8", "label": "Groupe 8", "family": "ccns", "level": "8"},
    {"code": "APPRENTI", "label": "Apprenti", "family": "ccns", "level": None},
]

LEGACY_CONTRACT_TYPES = [
    {"nom": "CDI", "nom_abrege": "CDI", "duree_indeterminee": "oui"},
    {"nom": "CDD", "nom_abrege": "CDD", "duree_indeterminee": "non"},
    {"nom": "CDII", "nom_abrege": "CDII", "duree_indeterminee": "oui"},
    {"nom": "APPRENTISSAGE", "nom_abrege": "APP", "duree_indeterminee": "non"},
    {"nom": "CEE", "nom_abrege": "CEE", "duree_indeterminee": "non"},
    {"nom": "AUTRE", "nom_abrege": "AUT", "duree_indeterminee": "non"},
]

TW_CONTRACT_TYPES = [
    {"code": "CDI", "label": "CDI"},
    {"code": "CDD", "label": "CDD"},
    {"code": "CDII", "label": "CDII"},
    {"code": "APPRENTICESHIP", "label": "Apprentissage"},
    {"code": "CEE", "label": "CEE"},
    {"code": "OTHER", "label": "Autre"},
]

TW_EMPLOYMENT_REGIMES = [
    {"code": "CCNS_STANDARD", "label": "CCNS standard"},
    {"code": "CCNS_MODULATION", "label": "CCNS modulation"},
    {"code": "CCNS_CDII", "label": "CCNS CDII"},
    {"code": "APPRENTICE", "label": "Apprenti"},
    {"code": "CEE", "label": "CEE"},
]

TW_TIME_ORGANIZATIONS = [
    {"code": "WEEKLY_CONSTANT", "label": "Hebdomadaire constante"},
    {"code": "ANNUALIZATION", "label": "Annualisation"},
    {"code": "MODULATION", "label": "Modulation"},
    {"code": "INTERMITTENCE", "label": "Intermittence"},
    {"code": "DAILY_CEE", "label": "Journalier CEE"},
]

SALARY_GRID = {
    "code": "CCNS-2026-01",
    "label": "CCNS 2026 - 1er janvier",
    "convention_code": "CCNS",
    "effective_date": "2026-01-01",
    "source_reference": "CCNS 1er mars 2026",
}

SALARY_GRID_LINES = [
    {"classification_code": "G1", "minimum_type": "MONTHLY", "amount": 1848.42, "unit": "EUR"},
    {"classification_code": "G2", "minimum_type": "MONTHLY", "amount": 1885.14, "unit": "EUR"},
    {"classification_code": "G3", "minimum_type": "MONTHLY", "amount": 1997.87, "unit": "EUR"},
    {"classification_code": "G4", "minimum_type": "MONTHLY", "amount": 2099.37, "unit": "EUR"},
    {"classification_code": "G5", "minimum_type": "MONTHLY", "amount": 2333.99, "unit": "EUR"},
    {"classification_code": "G6", "minimum_type": "MONTHLY", "amount": 2865.97, "unit": "EUR"},
    {"classification_code": "G7", "minimum_type": "ANNUAL", "amount": 40597.94, "unit": "EUR"},
    {"classification_code": "G8", "minimum_type": "ANNUAL", "amount": 46833.81, "unit": "EUR"},
    {"classification_code": "APPRENTI", "minimum_type": "MONTHLY", "amount": 800.0, "unit": "EUR",
     "age_min": 18, "age_max": 20, "execution_year_min": 2, "execution_year_max": 2,
     "notes": "Ligne de bootstrap de travail"},
]

DEFAULT_RULES = [
    {
        "code": "TP_COURT_LE_10H",
        "label": "Majoration temps partiel court jusqu'à 10h",
        "family": "SHORT_PART_TIME",
        "context": "contract",
        "target_object": "contract",
        "effective_date": "2026-01-01",
        "priority": 10,
        "parameters_json": json.dumps({
            "threshold_hours_min": 0.0,
            "threshold_hours_max": 10.0,
            "multiplier": 1.05,
        }, ensure_ascii=False),
    },
    {
        "code": "TP_COURT_LT_24H",
        "label": "Majoration temps partiel court au-delà de 10h et sous 24h",
        "family": "SHORT_PART_TIME",
        "context": "contract",
        "target_object": "contract",
        "effective_date": "2026-01-01",
        "priority": 20,
        "parameters_json": json.dumps({
            "threshold_hours_min": 10.0001,
            "threshold_hours_max": 23.9999,
            "multiplier": 1.02,
        }, ensure_ascii=False),
    },
    {
        "code": "CEE_MAX_80J",
        "label": "Plafond CEE 80 jours sur 12 mois",
        "family": "CEE",
        "context": "counter",
        "target_object": "contract",
        "effective_date": "2026-01-01",
        "priority": 10,
        "parameters_json": json.dumps({
            "rolling_period_months": 12,
            "max_days": 80,
        }, ensure_ascii=False),
    },
]


def _fetch_value(db, req):
    db.ExecuterReq(req)
    rows = db.ResultatReq()
    return rows[0][0] if rows else None


def _exists(db, table_name, where_sql):
    req = "SELECT COUNT(*) FROM %s WHERE %s;" % (table_name, where_sql)
    value = _fetch_value(db, req)
    return bool(value and value > 0)


def _insert_if_missing(db, table_name, unique_where_sql, payload):
    if _exists(db, table_name, unique_where_sql):
        return False
    db.ReqInsert(table_name, list(payload.items()))
    return True


def seed_teamworks_reference_data(sync_legacy_tables=True):
    db = GestionDB.DB()

    created = {
        "legacy_classifications": 0,
        "legacy_contract_types": 0,
        "tw_classifications": 0,
        "tw_contract_types": 0,
        "tw_employment_regimes": 0,
        "tw_time_organizations": 0,
        "tw_salary_grids": 0,
        "tw_salary_grid_lines": 0,
        "tw_rules": 0,
    }

    if sync_legacy_tables:
        for item in CCNS_CLASSIFICATIONS:
            if _insert_if_missing(
                db,
                "contrats_class",
                "nom='%s'" % item["code"].replace("'", "''"),
                {"nom": item["code"]},
            ):
                created["legacy_classifications"] += 1

        for item in LEGACY_CONTRACT_TYPES:
            if _insert_if_missing(
                db,
                "contrats_types",
                "nom='%s'" % item["nom"].replace("'", "''"),
                item,
            ):
                created["legacy_contract_types"] += 1

    for item in CCNS_CLASSIFICATIONS:
        payload = {
            "code": item["code"],
            "label": item["label"],
            "family": item["family"],
            "level": item["level"],
            "effective_date": "2026-01-01",
            "active": 1,
        }
        if _insert_if_missing(
            db,
            "tw_ccns_classifications",
            "code='%s'" % item["code"].replace("'", "''"),
            payload,
        ):
            created["tw_classifications"] += 1

    for item in TW_CONTRACT_TYPES:
        if _insert_if_missing(
            db,
            "tw_contract_types",
            "code='%s'" % item["code"].replace("'", "''"),
            item,
        ):
            created["tw_contract_types"] += 1

    for item in TW_EMPLOYMENT_REGIMES:
        if _insert_if_missing(
            db,
            "tw_employment_regimes",
            "code='%s'" % item["code"].replace("'", "''"),
            item,
        ):
            created["tw_employment_regimes"] += 1

    for item in TW_TIME_ORGANIZATIONS:
        if _insert_if_missing(
            db,
            "tw_time_organizations",
            "code='%s'" % item["code"].replace("'", "''"),
            item,
        ):
            created["tw_time_organizations"] += 1

    if _insert_if_missing(
        db,
        "tw_salary_grids",
        "code='%s'" % SALARY_GRID["code"],
        dict(SALARY_GRID, active=1),
    ):
        created["tw_salary_grids"] += 1

    grid_id = _fetch_value(db, "SELECT IDtw_salary_grid FROM tw_salary_grids WHERE code='%s';" % SALARY_GRID["code"])

    for line in SALARY_GRID_LINES:
        unique_where = "IDtw_salary_grid=%d AND classification_code='%s' AND minimum_type='%s'" % (
            grid_id,
            line["classification_code"].replace("'", "''"),
            line["minimum_type"].replace("'", "''"),
        )
        payload = dict(line)
        payload["IDtw_salary_grid"] = grid_id
        if _insert_if_missing(db, "tw_salary_grid_lines", unique_where, payload):
            created["tw_salary_grid_lines"] += 1

    for rule in DEFAULT_RULES:
        payload = dict(rule, active=1)
        if _insert_if_missing(
            db,
            "tw_calculation_rules",
            "code='%s'" % rule["code"].replace("'", "''"),
            payload,
        ):
            created["tw_rules"] += 1

    db.Close()
    return created


if __name__ == "__main__":
    result = seed_teamworks_reference_data(sync_legacy_tables=True)
    print("Seed CCNS Teamworks termine")
    for key in sorted(result.keys()):
        print("- %s: %d" % (key, result[key]))
