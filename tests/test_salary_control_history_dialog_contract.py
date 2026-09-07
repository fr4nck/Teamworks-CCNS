from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "Dlg" / "DLG_CCNS_salary_control_history.py"


def test_salary_history_creates_staticbox_parents_before_children():
    source = SOURCE.read_text(encoding="utf-8")

    snapshots_parent = source.index('self.box_snapshots = wx.StaticBox(self, -1, "Contrôles enregistrés")')
    snapshots_child = source.index("self.listbox = wx.ListBox(self.box_snapshots")
    details_parent = source.index('self.box_details = wx.StaticBox(self, -1, "Détail et analyse")')
    details_child = source.index("self.details = wx.TextCtrl(self.box_details")

    assert snapshots_parent < snapshots_child
    assert details_parent < details_child
    assert ".Reparent(" not in source


def test_salary_history_uses_workspace_profile_instead_of_raw_window_sizes():
    source = SOURCE.read_text(encoding="utf-8")

    assert 'UTILS_Styles.ApplyWindowProfile(self, "workspace")' in source
    assert "self.SetSize((1120, 700))" not in source
    assert "self.SetMinSize((900, 560))" not in source
