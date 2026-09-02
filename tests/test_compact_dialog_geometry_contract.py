from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_password.py",
    ROOT / "teamworks" / "Dlg" / "DLG_Config_password.py",
)


def test_short_password_dialogs_are_not_user_resizable():
    for path in FILES:
        source = path.read_text(encoding="utf-8")
        assert "wx.RESIZE_BORDER" not in source
        assert "wx.MAXIMIZE_BOX" not in source
        assert "wx.MINIMIZE_BOX" not in source
        assert ".Fit(self)" in source
