from pathlib import Path

from scripts.audit_runtime_risks import audit_text


def categories_for(line: str) -> set[str]:
    root = Path("/tmp/repo")
    path = root / "teamworks" / "sample.py"
    return {finding.category for finding in audit_text(root, path, [line])}


def test_sqlite_bytes_path_is_reported_as_priority_risk():
    categories = categories_for("connexion = sqlite3.connect(path.encode('utf-8'))")

    assert "sqlite-direct" in categories
    assert "sqlite-bytes-path" in categories


def test_sqlite_string_path_is_not_reported_as_bytes_risk():
    categories = categories_for("connexion = sqlite3.connect(path)")

    assert "sqlite-direct" in categories
    assert "sqlite-bytes-path" not in categories
