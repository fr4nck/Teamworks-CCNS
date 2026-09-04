import inspect
import sqlite3

import infrastructure.persistence.employee_protection_repository as persistence_module
from infrastructure.persistence.employee_protection_repository import (
    SqliteEmployeeProtectionRepository,
)


def test_employee_protection_schema_has_no_foreign_keys(tmp_path):
    path = tmp_path / "employee-protection.sqlite"
    SqliteEmployeeProtectionRepository(path)

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "PRAGMA foreign_key_list(tw_hr_employee_protection)"
        ).fetchall() == []


def test_employee_protection_schema_has_no_secret_or_health_columns(tmp_path):
    path = tmp_path / "employee-protection.sqlite"
    SqliteEmployeeProtectionRepository(path)

    with sqlite3.connect(path) as conn:
        columns = {
            row[1].lower()
            for row in conn.execute(
                "PRAGMA table_info(tw_hr_employee_protection)"
            ).fetchall()
        }

    forbidden = {
        "password",
        "secret",
        "token",
        "cookie",
        "api_key",
        "private_key",
        "diagnosis",
        "pathology",
        "medical_data",
        "health_data",
        "comment",
        "notes",
    }
    assert forbidden.isdisjoint(columns)


def test_employee_protection_persistence_does_not_import_legacy_database_layer():
    source = inspect.getsource(persistence_module)

    for forbidden in ("GestionDB", "UTILS_", "teamworks.", "import wx", "wx."):
        assert forbidden not in source
