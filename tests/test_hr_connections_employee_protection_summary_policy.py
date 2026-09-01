from dataclasses import fields
import inspect

import application.services.hr_connections.employee_protection_summary as summary_module
from application.services.hr_connections.employee_protection_summary import (
    EmployeeProtectionSummary,
)


def test_summary_does_not_expose_automatic_legal_compliance_fields():
    field_names = {field.name.lower() for field in fields(EmployeeProtectionSummary)}

    forbidden = {
        "compliant",
        "non_compliant",
        "legal_status",
        "mandatory_missing",
        "legal_alert",
    }
    assert forbidden.isdisjoint(field_names)


def test_summary_stays_ui_backend_and_network_agnostic():
    source = inspect.getsource(summary_module)

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
