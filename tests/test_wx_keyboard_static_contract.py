from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUTTON = ROOT / "teamworks" / "Ctrl" / "CTRL_Bouton_image.py"
FILTER_TEXT = ROOT / "teamworks" / "Dlg" / "DLG_Filtre_texte.py"
KEYBOARD_SMOKE = ROOT / "tools" / "smoke_wx_keyboard_accessibility.py"


def test_common_buttons_keep_native_windows_keyboard_contract() -> None:
    source = BUTTON.read_text(encoding="utf-8")

    assert "class CTRL(wx.Button):" in source
    assert "class Toggle(wx.ToggleButton):" in source
    assert "wx.Button.__init__(self, parent" in source
    assert "wx.ToggleButton.__init__(self, parent" in source


def test_filter_dialog_declares_cancel_and_initial_focus_contract() -> None:
    source = FILTER_TEXT.read_text(encoding="utf-8")

    assert "id=wx.ID_CANCEL" in source
    assert "SetFocus()" in source
    assert "self.ctrl_texte.Enable(not self.radio1.GetValue())" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "compact")' in source


def test_windows_keyboard_smoke_covers_required_interactions() -> None:
    source = KEYBOARD_SMOKE.read_text(encoding="utf-8")

    required = (
        "wx.UIActionSimulator",
        "wx.WXK_TAB",
        "wx.WXK_SHIFT",
        "wx.WXK_RETURN",
        "wx.WXK_SPACE",
        "wx.WXK_ESCAPE",
        "wx.Window.FindFocus()",
        "IsShownOnScreen()",
        "dialog.ctrl_texte.IsEnabled()",
        "dialog.radio2.GetValue()",
    )
    for marker in required:
        assert marker in source, marker
