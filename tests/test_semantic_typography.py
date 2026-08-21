from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "teamworks" / "Utils" / "UTILS_Styles.py"
TEXT = ROOT / "teamworks" / "Ctrl" / "CTRL_Texte.py"
BANDEAU = ROOT / "teamworks" / "Ctrl" / "CTRL_Bandeau.py"
AUDIT = ROOT / "scripts" / "audit_legacy_ui.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_text_hierarchy_is_centralized_like_a_stylesheet():
    source = _source(STYLES)
    for style in ("h1", "h2", "h3", "body", "body-secondary", "label", "caption"):
        assert '"%s"' % style in source
    assert "UTILS_Interface.GetToken" in source
    assert '"echelle_interface"' in source
    assert '"echelle_police"' in source


def test_native_semantic_text_controls_exist():
    source = _source(TEXT)
    assert "class Texte(wx.StaticText)" in source
    for helper in ("H1", "H2", "H3", "Body", "BodySecondary", "Label", "Caption"):
        assert "def %s(" % helper in source
    assert "UTILS_Styles.AppliquerTexte" in source


def test_common_banner_consumes_h1_instead_of_local_font_recipe():
    source = _source(BANDEAU)
    assert "CTRL_Texte.H1" in source
    assert ".SetFont(" not in source
    assert "wx.Font(" not in source
    assert "UTILS_Styles.Scale" in source


def test_ui_audit_tracks_manual_typography():
    source = _source(AUDIT)
    assert '"typography.manual_font"' in source
    assert '"typography.literal_font"' in source
