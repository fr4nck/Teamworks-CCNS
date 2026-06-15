from teamworks.CcnsCore.incomplete_files_ccns import _format_global_status, _map_global_severity


def test_format_global_status():
    assert _format_global_status("BLOQUANT") == "bloquant"


def test_map_global_severity():
    assert _map_global_severity("A_REVOIR") == "warning"
