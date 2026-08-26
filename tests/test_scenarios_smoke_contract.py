from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_scenarios_lifecycle.py"
SCENARIO_DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Scenario.py"


def test_scenarios_smoke_qualifies_create_edit_management_and_cleanup() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    for marker in (
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:fixture",
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:create-dialog",
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:create-save",
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:create-readback",
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:edit-dialog",
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:edit-save",
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:edit-readback",
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:management-readback",
        "TEAMWORKS_SMOKE_SCENARIOS_STAGE:cleanup",
        "TEAMWORKS_SMOKE_SCENARIOS_LIFECYCLE_READY",
        "TEAMWORKS_SMOKE_SCENARIOS_LIFECYCLE_FAILED",
    ):
        assert marker in source

    assert "DLG_Scenario" in source
    assert "DLG_Scenario_gestion" in source
    assert "IDscenario=None" in source
    assert 'GetTitle() == "Création d\'un scénario"' in source
    assert ".Sauvegarde()" in source
    assert "dictScenarios" in source
    assert 'ReqDEL("scenarios_cat"' in source
    assert 'ReqDEL("scenarios"' in source
    assert 'ReqDEL("personnes"' in source
    assert "PATCHED.unlink(missing_ok=True)" in source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in source


def test_scenario_dialog_persists_parent_and_category_tables() -> None:
    source = SCENARIO_DIALOG.read_text(encoding="utf-8")

    assert 'ReqInsert("scenarios", listeDonnees)' in source
    assert 'ReqMAJ("scenarios", listeDonnees, "IDscenario", self.IDscenario)' in source
    assert 'ReqInsert("scenarios_cat", listeDonnees)' in source
    assert 'ReqMAJ("scenarios_cat", listeDonnees, "IDscenario_cat", IDscenario_cat)' in source
    assert 'ReqDEL("scenarios_cat", "IDscenario_cat", IDscenario_cat)' in source
    assert "return IDscenario" in source


def test_scenario_dialog_distinguishes_create_and_edit_titles() -> None:
    source = SCENARIO_DIALOG.read_text(encoding="utf-8")

    assert "if self.IDscenario in (None, 0)" in source
    assert "Création d'un scénario" in source
    assert "Modification d'un scénario" in source


def test_scenario_report_error_uses_the_grid_counter() -> None:
    source = SCENARIO_DIALOG.read_text(encoding="utf-8")

    assert "% self.ctrl_tableau.nbreErreursReport" in source


def test_scenario_grid_resolves_its_dialog_without_staticbox_hierarchy_assumptions() -> None:
    source = SCENARIO_DIALOG.read_text(encoding="utf-8")

    assert "self.parent = wx.GetTopLevelParent(self)" in source
    assert "self.parent = parent.GetParent()" not in source


def test_scenario_dialog_loads_text_controls_with_values_under_phoenix() -> None:
    source = SCENARIO_DIALOG.read_text(encoding="utf-8")

    assert "self.ctrl_nom.SetValue(nom)" in source
    assert "self.ctrl_description.SetValue(str(description))" in source
    assert "self.ctrl_nom.SetLabel(nom)" not in source
    assert "self.ctrl_description.SetLabel(str(description))" not in source


def test_scenarios_lifecycle_runs_in_real_windows_application() -> None:
    if sys.platform != "win32":
        return

    completed = subprocess.run(
        [sys.executable, str(SMOKE)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    assert completed.returncode == 0, output
