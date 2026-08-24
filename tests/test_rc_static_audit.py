from pathlib import Path

from scripts.audit_rc_risks import audit


ROOT = Path(__file__).resolve().parents[1]


def _report():
    return audit(ROOT / "teamworks")


def test_no_staticbox_parenting_mismatch():
    findings = [
        item for item in _report()["findings"]
        if item["code"] == "wx-staticbox-parent"
    ]
    assert not findings, "Parentage wx.StaticBoxSizer invalide :\n" + "\n".join(
        f"{item['file']}:{item['line']} {item.get('widget')} parent={item.get('actual_parent')} attendu={item.get('expected_parent')}"
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
