from pathlib import Path

from scripts import audit_dialog_geometry


ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "teamworks" / "Utils" / "UTILS_Styles.py"


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


def test_geometry_audit_flags_useless_stretch():
    record = audit_dialog_geometry.classify(
        "wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE)\n"
        "sizer.AddStretchSpacer(1)\n"
        "self.ctrl = wx.TextCtrl(self)\n"
    )
    codes = {item["code"] for item in record["findings"]}
    assert "stretch-without-expandable-content" in codes


def test_geometry_audit_requires_outer_refit_after_dynamic_content_change():
    record = audit_dialog_geometry.classify(
        "self.details.Show(active)\n"
        "self.Layout()\n"
    )
    codes = {item["code"] for item in record["findings"]}
    assert "dynamic-content-without-refit" in codes


def test_geometry_audit_accepts_refit_after_dynamic_content_change():
    record = audit_dialog_geometry.classify(
        "self.details.Show(active)\n"
        "UTILS_Styles.RefitWindow(self)\n"
    )
    codes = {item["code"] for item in record["findings"]}
    assert "dynamic-content-without-refit" not in codes


def test_fit_profile_is_a_semantic_content_driven_window_mode():
    source = STYLES.read_text(encoding="utf-8")
    assert "def FitWindowToContent(" in source
    assert "def RefitWindow(" in source
    assert 'if profile == "fit":' in source
    assert 'window._teamworks_window_profile = "fit"' in source
