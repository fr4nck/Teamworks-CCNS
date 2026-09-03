from pathlib import Path


ROOT = Path("teamworks") / "Dlg"
CONFIG = ROOT / "DLG_Config_password.py"
ENTRY = ROOT / "DLG_Saisie_password.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_password_configuration_uses_responsive_image_button():
    source = _source(CONFIG)
    assert "wx.BitmapButton" not in source
    assert "CTRL_Bouton_image.CTRL" in source
    assert 'Images/32x32/Aide.png' in source


def test_password_configuration_dialog_is_content_fitted():
    source = _source(CONFIG)
    dialog = source.split("class Dialog(wx.Dialog):", 1)[1]
    assert "wx.RESIZE_BORDER" not in dialog
    assert "wx.MAXIMIZE_BOX" not in dialog
    assert "wx.MINIMIZE_BOX" not in dialog
    assert 'UTILS_Styles.ApplyWindowProfile(self, "fit")' in dialog
    assert "wx.CallAfter(UTILS_Styles.RefitWindow, self)" in dialog
    assert "SetMinSize((550, 300))" not in dialog


def test_password_entry_dialog_follows_zoom_and_content():
    source = _source(ENTRY)
    assert "wx.RESIZE_BORDER" not in source
    assert "wx.MAXIMIZE_BOX" not in source
    assert "wx.MINIMIZE_BOX" not in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "fit")' in source
    assert "wx.CallAfter(UTILS_Styles.RefitWindow, self)" in source
    assert "UTILS_Styles.ApplyFieldRole" in source
    assert "wx.Bitmap(" not in source
    assert "CopyFromBitmap" not in source


def test_password_entry_buttons_use_common_icon_engine():
    source = _source(ENTRY)
    assert source.count("CTRL_Bouton_image.CTRL") >= 3
    assert 'Images/32x32/Aide.png' in source
    assert 'Images/32x32/Valider.png' in source
    assert 'Images/32x32/Annuler.png' in source
