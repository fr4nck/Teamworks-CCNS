from pathlib import Path


SOURCE = Path("teamworks/Ctrl/CTRL_Recrutement_navigation.py")


def test_recrutement_modes_use_common_toggle_contract():
    source = SOURCE.read_text(encoding="utf-8")
    assert "class BoutonMode(CTRL_Bouton_image.Toggle):" in source
    assert "wx.ToggleButton(" not in source
    assert "SetBackgroundColour(fond)" not in source
    assert "SetForegroundColour(texte)" not in source
    assert "GetControlMetric(\"button_min_height\")" not in source
    assert "bouton.SetValue(code == mode)" in source
    assert "wx.EVT_TOGGLEBUTTON" in source
