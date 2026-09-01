import sqlite3

from infrastructure.persistence.hr_connections_repository import SqliteHrConnectionsRepository


def test_hr_connections_schema_has_no_legacy_foreign_keys(tmp_path):
    path = tmp_path / "hr-connections.sqlite"
    SqliteHrConnectionsRepository(path)

    with sqlite3.connect(path) as conn:
        for table in ("tw_hr_connection_profiles", "tw_hr_cases", "tw_hr_audit_events"):
            assert conn.execute(f"PRAGMA foreign_key_list({table})").fetchall() == []


def test_hr_connections_schema_does_not_define_credential_columns(tmp_path):
    path = tmp_path / "hr-connections.sqlite"
    SqliteHrConnectionsRepository(path)

    with sqlite3.connect(path) as conn:
        columns = []
        for (table,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tw_hr_%'"
        ).fetchall():
            columns.extend(row[1].lower() for row in conn.execute(f"PRAGMA table_info({table})"))

    forbidden = {"password", "token", "cookie", "api_key", "private_key", "secret_value"}
    assert forbidden.isdisjoint(columns)
