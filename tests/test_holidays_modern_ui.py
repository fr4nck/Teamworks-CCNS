from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FERIES = ROOT / "teamworks" / "Dlg" / "DLG_Feries.py"


def _source():
    return FERIES.read_text(encoding="utf-8")


def test_holidays_dialog_uses_direct_responsive_layout():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.StaticBox" not in source
    assert "wx.StaticBoxSizer" not in source
    assert "wx.BoxSizer" in source
    assert "wx.WrapSizer" in source
    assert "AddStretchSpacer" in source


def test_holidays_dialog_has_no_legacy_tiny_actions_or_sunken_lists():
    source = _source()
    assert "wx.BitmapButton" not in source
    assert "Images/16x16/" not in source
    assert "wx.SUNKEN_BORDER" not in source
    assert "CTRL_Bouton_image.CTRL" in source


def test_holidays_dialog_uses_semantic_surfaces_and_dpi_sizes():
    source = _source()
    assert 'UTILS_Interface.GetToken("surface")' in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert "FromDIP" in source
