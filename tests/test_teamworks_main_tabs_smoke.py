from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"


def test_main_tabs_smoke_uses_real_toolbook_attribute():
    source = ENTRYPOINT.read_text(encoding="iso-8859-15")

    assert "frame.toolBook.SetSelection(index)" in source
    assert "frame.toolBook.MAJ_panel(index)" in source
    assert "frame.toolBook.GetPageCount()" in source
    assert "frame.toolbook" not in source


def test_main_tabs_smoke_emits_all_runtime_markers():
    source = ENTRYPOINT.read_text(encoding="iso-8859-15")

    assert "TEAMWORKS_SMOKE_MAIN_WINDOW_READY" in source
    assert "TEAMWORKS_SMOKE_TAB_READY:{index}" in source
    assert 'TEAMWORKS_SMOKE_MODE") == "main-window"' in source
