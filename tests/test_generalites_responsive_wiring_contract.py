from pathlib import Path


RESPONSIVE = Path("teamworks/Utils/UTILS_Responsive.py")
ADAPTER = Path("teamworks/Ctrl/CTRL_Page_generalites_091e.py")


def test_helper_responsive_couvre_snap_et_zoom():
    namespace = {}
    exec(RESPONSIVE.read_text(encoding="utf-8"), namespace)
    columns = namespace["form_column_count"]
    assert columns(1720, 100) == 2
    assert columns(960, 100) == 1
    assert columns(1720, 200) == 1
    assert columns(1720, 220) == 1


def test_adaptateur_cable_reellement_le_helper_responsive():
    source = ADAPTER.read_text(encoding="utf-8")
    assert "LEGACY.Panel_general" in source
    assert "UTILS_Generalites_international" in source
    assert "UTILS_Responsive.form_column_count(" in source
    assert "self.Bind(wx.EVT_SIZE, self._on_responsive_size)" in source
    assert "wx.CallAfter(self._appliquer_layout_responsive)" in source
    assert "if colonnes == 1:" in source
    assert "self.SetSizer(sizer, deleteOld=True)" in source
