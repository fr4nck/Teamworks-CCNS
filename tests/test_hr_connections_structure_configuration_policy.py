import inspect

import application.services.hr_connections.structure_configuration as structure_configuration


def test_structure_configuration_service_stays_ui_and_backend_agnostic():
    source = inspect.getsource(structure_configuration)

    assert "import wx" not in source
    assert "from wx" not in source
    assert "sqlite3" not in source
    assert "infrastructure.persistence" not in source
    assert "GestionDB" not in source
