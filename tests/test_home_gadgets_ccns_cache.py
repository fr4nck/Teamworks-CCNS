import sys
import types
from pathlib import Path

sys.modules.setdefault("wx", types.SimpleNamespace())
sys.modules.setdefault("GestionDB", types.SimpleNamespace(DB=object))
seniority = types.ModuleType("domain.engine.seniority")
seniority.check_ccns_seniority_amount = lambda *args, **kwargs: (types.SimpleNamespace(readable_message=""), None)
sys.modules.setdefault("domain.engine.seniority", seniority)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "teamworks"))

from teamworks.CcnsCore.audit_contracts_ccns import AuditRow
from teamworks.CcnsCore import home_gadgets_ccns as home
from teamworks.CcnsCore.audit_sorting import compute_row_severity


def _rows():
    return [
        AuditRow(1, "Alice Martin", "G3", "CDI", 1800.0, ["CONTRAT_SANS_GRILLE"], ["m1"]),
        AuditRow(2, "Bob Durant", "G4", "CDD", 2200.0, ["MINIMUM_CCNS_NON_ATTEINT"], ["m2"]),
        AuditRow(3, "Alice Martin", "G3", "CDI", 2500.0, [], ["m3"]),
    ]


def _anciennes_stats(rows):
    nb_anomalies = 0
    nb_blocking_contracts = 0
    nb_warning_contracts = 0
    people_with_issues = set()
    blocking_people = set()
    warning_people = set()
    for row in rows:
        nb_anomalies += len(row.anomalies)
        severity_label, _severity_rank = compute_row_severity({"anomalies": row.anomalies})
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
        {"code": "ccns_contracts_total", "label": "Contrats audités CCNS", "value": len(rows), "severity": "neutral"},
        {"code": "ccns_anomalies_total", "label": "Anomalies CCNS détectées", "value": nb_anomalies, "severity": "warning" if nb_anomalies > 0 else "ok"},
        {"code": "ccns_blocking_contracts", "label": "Contrats CCNS bloquants", "value": nb_blocking_contracts, "severity": "blocking" if nb_blocking_contracts > 0 else "ok"},
        {"code": "ccns_warning_contracts", "label": "Contrats CCNS à revoir", "value": nb_warning_contracts, "severity": "warning" if nb_warning_contracts > 0 else "ok"},
        {"code": "ccns_people_with_issues", "label": "Individus avec alertes CCNS", "value": len(people_with_issues), "severity": "warning" if people_with_issues else "ok"},
        {"code": "ccns_people_blocking", "label": "Individus avec blocages CCNS", "value": len(blocking_people), "severity": "blocking" if blocking_people else "ok"},
    ]


def _anciennes_alertes(rows, max_lines=12):
    prepared = []
    for row in rows:
        severity_label, severity_rank = compute_row_severity({"anomalies": row.anomalies})
        if severity_label == "ok":
            continue
        prepared.append({"IDcontrat": row.IDcontrat, "nom_complet": row.nom_complet, "severity_label": severity_label, "severity_rank": severity_rank, "anomalies": row.anomalies})
    prepared.sort(key=lambda item: (item["severity_rank"], (item["nom_complet"] or "").strip().upper(), item["IDcontrat"]))
    result = []
    for item in prepared[:max_lines]:
        label_severity = {"blocking": "Bloquant", "warning": "A revoir"}.get(item["severity_label"], item["severity_label"])
        result.append({
            "label": "%s - contrat %s - %s" % (item["nom_complet"] or "(sans nom)", item["IDcontrat"], label_severity),
            "severity": item["severity_label"],
            "contract_id": item["IDcontrat"],
            "details": ", ".join(item["anomalies"]),
        })
    return result


def setup_function(_function):
    home.clear_ccns_home_cache()


def test_construction_complete_un_seul_appel_audit(monkeypatch):
    appels = []
    monkeypatch.setattr(home, "audit_contracts", lambda limit=None: appels.append(limit) or _rows())

    data = home.build_ccns_home_data(limit=5000, max_lines=12)

    assert appels == [5000]
    assert data["stats"]
    assert data["alerts"]


def test_reutilisation_du_cache(monkeypatch):
    appels = []
    monkeypatch.setattr(home, "audit_contracts", lambda limit=None: appels.append(limit) or _rows())

    first = home.build_ccns_home_data(limit=5000, max_lines=12)
    second = home.build_ccns_home_data(limit=5000, max_lines=12)

    assert appels == [5000]
    assert second is first


def test_invalidation_forcee(monkeypatch):
    appels = []
    monkeypatch.setattr(home, "audit_contracts", lambda limit=None: appels.append(limit) or _rows())

    home.build_ccns_home_data(limit=5000, max_lines=12)
    home.build_ccns_home_data(limit=5000, max_lines=12, force_refresh=True)

    assert appels == [5000, 5000]


def test_resultats_identiques_aux_calculs_precedents(monkeypatch):
    rows = _rows()
    monkeypatch.setattr(home, "audit_contracts", lambda limit=None: rows)

    data = home.build_ccns_home_data(limit=5000, max_lines=12)

    assert data["stats"] == _anciennes_stats(rows)
    assert data["alerts"] == _anciennes_alertes(rows)
