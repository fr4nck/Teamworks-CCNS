from pathlib import Path


def test_recruitment_filters_use_semantic_layout_and_explicit_control_registry():
    source = Path("teamworks/Dlg/DLG_Filtre_recrutement.py").read_text(encoding="utf-8")

    assert "CTRL_Section.Section" in source
    assert "CTRL_Texte.H1" in source
    assert "ApplyWindowProfile" in source
    assert "ResoudreTypeControle" in source
    assert "eval(typeControle)" not in source
    assert "wx.lib.agw.hyperlink" not in source
    assert "wx.StaticBox" not in source
    assert "wx.BitmapButton" not in source
    assert 'SetColours("BLUE"' not in source
    assert "Réinitialiser" in source
    assert "Appliquer" in source
