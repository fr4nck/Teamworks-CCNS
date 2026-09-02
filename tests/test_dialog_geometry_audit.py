from pathlib import Path

from scripts import audit_dialog_geometry


ROOT = Path(__file__).resolve().parents[1]
COORDS = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_coords.py"


def test_geometry_audit_flags_resizable_short_form():
    record = audit_dialog_geometry.classify(
        "wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)\n"
        "self.ctrl = wx.TextCtrl(self)\n"
        "self.Fit()\n"
    )
    codes = {item["code"] for item in record["findings"]}
    assert "resizable-without-expandable-content" in codes
    assert "fit-but-still-resizable" in codes


def test_geometry_audit_accepts_real_workspace_resize():
    record = audit_dialog_geometry.classify(
        "wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)\n"
        "self.listing = wx.ListCtrl(self)\n"
    )
    codes = {item["code"] for item in record["findings"]}
    assert "resizable-without-expandable-content" not in codes


def test_coordinates_compat_dialog_is_bounded_to_content():
    source = COORDS.read_text(encoding="utf-8")
    record = audit_dialog_geometry.classify(source)
    codes = {item["code"] for item in record["findings"]}

    assert "wx.RESIZE_BORDER" not in source
    assert "self.Fit()" in source
    assert "self.SetMaxSize" in source
    assert "resizable-without-expandable-content" not in codes
    assert "stretch-without-expandable-content" not in codes
