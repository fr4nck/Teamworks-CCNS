from pathlib import Path


SOURCE = Path("tools/smoke_main_navigation.py")
WORKFLOW = Path(".github/workflows/ci.yml")


def test_windows_navigation_smoke_measures_real_button_geometry_and_dark_colours():
    source = SOURCE.read_text(encoding="utf-8")

    assert 'os.environ["TEAMWORKS_APPEARANCE"] = "dark"' in source
    assert "widths == minimums == maximums" in source
    assert "max(widths) < min(widths) * 1.75" in source
    assert "AUI_DOCKART_BACKGROUND_COLOUR" in source
    assert "AUI_DOCKART_SASH_COLOUR" in source
    assert "TEAMWORKS_SMOKE_MAIN_NAVIGATION_READY" in source


def test_windows_navigation_smoke_is_part_of_critical_ci():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'Invoke-Smoke "Navigation et thème sombre" @("tools/smoke_main_navigation.py")' in workflow
