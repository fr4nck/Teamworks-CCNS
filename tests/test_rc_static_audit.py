import json
from functools import lru_cache
from pathlib import Path

from scripts.audit_rc_risks import audit


ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _report():
    # Un seul ratissage complet par processus pytest : le rapport est partagé
    # entre les gardes afin de ne pas rescanner 500+ fichiers à chaque test.
    report = audit(ROOT / "teamworks")

    # La CI archive déjà runtime-risk-audit.json après pytest. On enrichit ce
    # diagnostic existant plutôt que de créer un second mécanisme d'artefact.
    # En exécution locale, l'absence du fichier est normale et n'a aucun effet.
    runtime_report = ROOT / "runtime-risk-audit.json"
    if runtime_report.is_file():
        try:
            payload = json.loads(runtime_report.read_text(encoding="utf-8"))
            payload["rc_preflight"] = report
            runtime_report.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except (OSError, ValueError, TypeError):
            pass
    return report


def test_no_staticbox_parenting_mismatch():
    findings = [
        item for item in _report()["findings"]
        if str(item["code"]).startswith("wx-staticbox")
    ]
    assert not findings, "Parentage wx.StaticBoxSizer invalide :\n" + "\n".join(
        (
            f"{item['file']}:{item['line']} "
            f"{item.get('widget') or item.get('helper')} "
            f"parent={item.get('actual_parent')} "
            f"attendu={item.get('expected_parent')}"
        )
        for item in findings
    )


def test_no_mysql55_incompatible_add_column_if_not_exists():
    findings = [
        item for item in _report()["findings"]
        if item["code"] == "mysql55-add-column-if-not-exists"
    ]
    assert not findings, "DDL incompatible MariaDB/MySQL historique :\n" + "\n".join(
        f"{item['file']}:{item['line']} {item.get('text', '')}"
        for item in findings
    )


def test_no_insert_values_without_explicit_columns():
    findings = [
        item for item in _report()["findings"]
        if item["code"] == "sql-insert-values-no-columns"
    ]
    assert not findings, "INSERT dépendant de l'ordre physique du schéma :\n" + "\n".join(
        f"{item['file']}:{item['line']} {item.get('text', '')}"
        for item in findings
    )
