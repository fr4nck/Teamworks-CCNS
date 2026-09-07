from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "Dlg" / "DLG_CCNS_salary_control_history.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_salary_history_creates_staticbox_parents_before_children():
    source = _source()

    snapshots_parent = source.index('self.box_snapshots = wx.StaticBox(self, -1, "Contrôles enregistrés")')
    snapshots_child = source.index("self.listbox = wx.ListBox(self.box_snapshots")
    details_parent = source.index('self.box_details = wx.StaticBox(self, -1, "Détail et analyse")')
    details_child = source.index("self.details = wx.TextCtrl(self.box_details")

    assert snapshots_parent < snapshots_child
    assert details_parent < details_child
    assert ".Reparent(" not in source


def test_salary_history_uses_workspace_profile_instead_of_raw_window_sizes():
    source = _source()

    assert 'UTILS_Styles.ApplyWindowProfile(self, "workspace", centre=False)' in source
    assert "self.SetSize((1120, 700))" not in source
    assert "self.SetMinSize((900, 560))" not in source


def test_salary_history_workspace_is_clamped_to_available_display_area():
    source = _source()

    assert "wx.Display.GetFromWindow(self)" in source
    assert "GetClientArea()" in source
    assert "max_width = max(1, area.GetWidth() - (2 * margin))" in source
    assert "max_height = max(1, area.GetHeight() - (2 * margin))" in source
    assert "width = min(current.GetWidth(), max_width)" in source
    assert "height = min(current.GetHeight(), max_height)" in source
    assert "min(self.GetMinSize().GetWidth(), width)" in source
    assert "min(self.GetMinSize().GetHeight(), height)" in source


def test_salary_history_actions_use_two_rows_for_high_zoom():
    source = _source()

    assert "actions = wx.BoxSizer(wx.VERTICAL)" in source
    assert "row_main = wx.BoxSizer(wx.HORIZONTAL)" in source
    assert "row_export = wx.BoxSizer(wx.HORIZONTAL)" in source
    assert "row_main.Add(self.filter, 1, wx.RIGHT | wx.EXPAND" in source
    assert "row_main.Add(self.button_compare" in source
    assert "row_main.Add(self.button_track_issues" in source
    assert "row_main.Add(self.button_alerts" in source
    assert "row_export.Add(self.button_export_csv" in source
    assert "row_export.Add(self.button_export_json" in source
    assert "row_export.Add(self.button_close" in source


def test_salary_history_list_and_detail_stay_expandable():
    source = _source()

    assert "snapshots_sizer.Add(self.listbox, 1, wx.ALL | wx.EXPAND" in source
    assert "body.Add(snapshots_sizer, 1, wx.RIGHT | wx.EXPAND" in source
    assert "details_sizer.Add(self.details, 1, wx.ALL | wx.EXPAND" in source
    assert "body.Add(details_sizer, 2, wx.EXPAND" in source
    assert "sizer.Add(body, 1, wx.ALL | wx.EXPAND" in source


def test_salary_history_has_no_high_zoom_raw_pixel_fallback():
    source = _source()

    for scale in (125, 150, 200):
        assert f"{scale}%" not in source
    assert "GetLayoutSpacing" in source
    assert "GetClientArea" in source
