from pathlib import Path


FILES = (
    "teamworks/Dlg/DLG_Filtre_texte.py",
    "teamworks/Dlg/DLG_Filtre_choice.py",
    "teamworks/Dlg/DLG_Filtre_coches.py",
)


def test_generic_filters_share_semantic_charter():
    for filename in FILES:
        source = Path(filename).read_text(encoding="utf-8")
        assert "CTRL_Section.Section" in source
        assert "CTRL_Texte.H1" in source
        assert "ApplyWindowProfile" in source
        assert "wx.StaticBox" not in source
        assert "wx.FlexGridSizer" not in source
        assert "Images/16x16" not in source
        assert "Images/32x32" not in source


def test_checkbox_filter_uses_single_native_checklist_control():
    source = Path("teamworks/Dlg/DLG_Filtre_coches.py").read_text(encoding="utf-8")
    assert "wx.CheckListBox" in source
    assert "CheckListCtrlMixin" not in source
