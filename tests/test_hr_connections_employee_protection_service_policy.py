import inspect

import application.services.hr_connections.employee_protection as employee_protection_service


def test_employee_protection_service_stays_ui_backend_and_network_agnostic():
    source = inspect.getsource(employee_protection_service)

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
