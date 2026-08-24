from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECTION = ROOT / "teamworks" / "Ctrl" / "CTRL_Section.py"


def _source():
    return SECTION.read_text(encoding="utf-8")


def test_section_uses_semantic_typography_and_surfaces():
    source = _source()
    assert "CTRL_Texte.H2" in source
    assert "CTRL_Texte.H3" in source
    assert "CTRL_Texte.H4" in source
    assert "CTRL_Texte.H5" in source
    assert "CTRL_Texte.H6" in source
    assert "CTRL_Texte.BodySecondary" in source
    assert "UTILS_Interface.GetToken(surface)" in source


def test_section_consumes_global_spacing_only():
    source = _source()
    assert 'UTILS_Styles.GetLayoutSpacing("content_padding")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("field_gap")' in source
    assert "wx.StaticBox" not in source
    assert "wx.FlexGridSizer" not in source
    assert "SetPointSize" not in source
    assert "wx.Colour(" not in source
