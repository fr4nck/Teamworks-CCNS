from dataclasses import fields
import inspect

import domain.hr_connections.employee_protection as employee_protection
from domain.hr_connections.employee_protection import EmployeeProtectionRecord


def test_employee_protection_record_does_not_define_secret_or_health_detail_fields():
    field_names = {field.name.lower() for field in fields(EmployeeProtectionRecord)}
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
        "medical_note",
        "comment",
        "notes",
    }

    assert forbidden.isdisjoint(field_names)


def test_employee_protection_domain_stays_ui_persistence_and_network_agnostic():
    source = inspect.getsource(employee_protection)

    for forbidden in (
        "import wx",
        "wx.",
        "sqlite3",
        "GestionDB",
        "requests.",
        "urllib.request",
        "teamworks.",
    ):
        assert forbidden not in source
