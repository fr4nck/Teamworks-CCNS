from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_password.py",
    ROOT / "teamworks" / "Dlg" / "DLG_Config_password.py",
    ROOT / "teamworks" / "Ol" / "OL_entretiens.py",
)
ENTRETIENS = ROOT / "teamworks" / "Ol" / "OL_entretiens.py"


def test_short_password_dialogs_are_not_user_resizable():
    """Les formulaires mot de passe doivent rester compacts et suivre leur contenu."""
    for path in FILES:
        source = path.read_text(encoding="utf-8")
        assert "wx.RESIZE_BORDER" not in source
        assert "wx.MAXIMIZE_BOX" not in source
        assert "wx.MINIMIZE_BOX" not in source
        assert 'ApplyWindowProfile(self, "fit")' in source
        assert "RefitWindow" in source


def test_entretiens_password_keeps_sizer_and_keyboard_contract():
    source = ENTRETIENS.read_text(encoding="utf-8")
    dialog = source.split("class SaisiePassword(wx.Dialog):", 1)[1].split("# Réexports", 1)[0]

    assert "self.SetSizer(sizer)" in dialog
    assert "wx.EVT_TEXT_ENTER" in dialog
    assert "self.text_password.SetFocus()" in dialog
    assert "id=wx.ID_OK" in dialog
    assert "id=wx.ID_CANCEL" in dialog
