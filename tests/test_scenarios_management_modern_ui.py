from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Scenario_gestion.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_scenario_manager_has_no_legacy_rigid_chrome():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.BitmapButton" not in source
    assert "Images/16x16/" not in source
    assert "SetBackgroundColour(wx.WHITE)" not in source
    assert ".Fit(self)" not in source
    assert "wx.WrapSizer" in source
    assert "AddStretchSpacer" in source


def test_scenario_tree_uses_semantic_surface_and_flexible_columns():
    source = _source()
    assert 'UTILS_Interface.GetToken("surface")' in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert "proportions = (0.34, 0.24, 0.42)" in source
    assert "proportions = (0.30, 0.25, 0.45)" in source
    assert "self.Bind(wx.EVT_SIZE, self.OnSize)" in source
    assert "FromDIP" in source


def test_scenario_manager_keeps_crud_and_duplication_contract():
    source = _source()
    assert 'DB.ReqDEL("scenarios", "IDscenario", IDscenario)' in source
    assert 'DB.ReqDEL("scenarios_cat", "IDscenario", IDscenario)' in source
    assert 'DB.ReqInsert("scenarios", listeDonnees)' in source
    assert 'DB.ReqInsert("scenarios_cat", listeDonnees)' in source
    assert "nbreReports" in source
    assert "DLG_Scenario.Dialog" in source
