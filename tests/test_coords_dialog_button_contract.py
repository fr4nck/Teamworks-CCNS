from pathlib import Path


PATH = Path("teamworks/Dlg/DLG_Saisie_coords.py")


def _source():
    return PATH.read_text(encoding="utf-8")


def test_coords_dialog_uses_common_toggle_contract_only():
    source = _source()
    assert "wx.ToggleButton(" not in source
    assert source.count("CTRL_Bouton_image.Toggle") == 4
    assert "SetBackgroundColour(UTILS_Interface.GetToken(\"primary_container\"))" not in source


def test_coords_dialog_is_content_fitted_and_refits_dynamic_sections():
    source = _source()
    assert "wx.RESIZE_BORDER" not in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "fit")' in source
    assert "wx.CallAfter(UTILS_Styles.RefitWindow, self)" in source
    assert "UTILS_Styles.RefitWindow(self, centre=False)" in source
    assert 'ApplyWindowProfile(self, "compact")' not in source


def test_coords_dialog_fields_use_semantic_widths():
    source = _source()
    assert "UTILS_Styles.FIELD_PHONE" in source
    assert "UTILS_Styles.FIELD_EMAIL" in source
    assert "UTILS_Styles.FIELD_TEXT" in source


def test_coords_dialog_primary_and_quiet_actions_use_common_roles():
    source = _source()
    assert 'role="primary"' in source
    assert 'role="quiet"' in source
