from scripts import audit_dialog_geometry


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
