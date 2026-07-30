from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"
MIGRATOR = ROOT / "tools" / "migrate_teamworks_tabs_smoke_mode.py"


def test_main_tabs_smoke_uses_real_toolbook_attribute():
    source = ENTRYPOINT.read_text(encoding="utf-8")

    assert "frame.toolBook.SetSelection(index)" in source
    assert "frame.toolBook.MAJ_panel(index)" in source
    assert "frame.toolBook.GetPageCount()" in source
    assert "frame.toolbook" not in source


def test_main_tabs_smoke_runs_forward_and_backward():
    source = ENTRYPOINT.read_text(encoding="utf-8")

    assert 'route = [("forward", index) for index in range(page_count)]' in source
    assert 'route.extend(("backward", index) for index in reversed(range(page_count)))' in source
    assert "enumerate(route, start=1)" in source
    assert "TEAMWORKS_SMOKE_TAB_READY:{pass_name}:{index}" in source
    assert "len(route) + 2" in source


def test_tabs_smoke_migrator_generates_the_same_round_trip_contract():
    source = MIGRATOR.read_text(encoding="utf-8")

    assert 'route = [("forward", index) for index in range(page_count)]' in source
    assert 'route.extend(("backward", index) for index in reversed(range(page_count)))' in source
    assert "TEAMWORKS_SMOKE_TAB_READY:{pass_name}:{index}" in source


def test_main_tabs_smoke_keeps_the_main_window_contract():
    source = ENTRYPOINT.read_text(encoding="utf-8")

    assert "TEAMWORKS_SMOKE_MAIN_WINDOW_READY" in source
    assert 'TEAMWORKS_SMOKE_MODE") == "main-window"' in source
