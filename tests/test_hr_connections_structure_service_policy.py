import inspect

import application.services.hr_connections.structure_configuration as structure_configuration


def test_structure_service_stays_ui_and_backend_agnostic():
    source = inspect.getsource(structure_configuration)

    for forbidden in ("wx.", "import wx", "sqlite3", "GestionDB", "teamworks."):
        assert forbidden not in source
