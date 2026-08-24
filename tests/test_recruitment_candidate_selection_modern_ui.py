from pathlib import Path


def test_candidate_selection_dialog_uses_semantic_responsive_layout():
    source = Path("teamworks/Dlg/DLG_Selection_candidat.py").read_text(encoding="utf-8")

    assert "CTRL_Texte.H1" in source
    assert 'ApplyWindowProfile(self, "wide")' in source
    assert "wx.Notebook" in source
    assert "Sélectionner" in source
    assert "wx.SUNKEN_BORDER" not in source
    assert "size=(450, 600)" not in source
    assert "size=(-1, 150)" not in source
    assert "wx.FlexGridSizer" not in source
    assert "Images/16x16" not in source
