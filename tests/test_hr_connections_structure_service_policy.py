import inspect

import application.services.hr_connections.structure_service as structure_service


def test_structure_service_stays_ui_and_backend_agnostic():
    source = inspect.getsource(structure_service)

    for forbidden in ("wx.", "import wx", "sqlite3", "GestionDB", "teamworks."):
        assert forbidden not in source
