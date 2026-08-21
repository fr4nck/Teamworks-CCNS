from pathlib import Path


def test_selection_periode_uses_flexible_semantic_rows_without_align_right():
    source = Path("teamworks/Dlg/DLG_Selection_periode.py").read_text(encoding="utf-8")

    assert "wx.StaticBox" not in source
    assert "wx.StaticBoxSizer" not in source
    assert "wx.FlexGridSizer" not in source
    assert source.count("CTRL_Section.Section(") == 3
    assert "cal_sizer = wx.BoxSizer(wx.HORIZONTAL)" in source
    assert "dates_sizer = wx.BoxSizer(wx.HORIZONTAL)" in source
    assert "bloc.Add(label, 0, wx.EXPAND)" in source
    assert "cal_sizer.Add(bloc, 1, wx.EXPAND | wx.RIGHT, gap)" in source
    assert "dates_sizer.Add(bloc, 1, wx.EXPAND | wx.RIGHT, gap)" in source
    assert "wx.ALIGN_RIGHT" not in source
