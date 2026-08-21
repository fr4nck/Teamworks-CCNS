from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "teamworks" / "Utils" / "UTILS_Styles.py"
TEXT = ROOT / "teamworks" / "Ctrl" / "CTRL_Texte.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_typography_scale_covers_legacy_and_modern_roles():
    source = _source(STYLES)
    expected = (
        '"display"',
        '"h1"',
        '"h2"',
        '"h3"',
        '"h4"',
        '"h5"',
        '"h6"',
        '"lead"',
        '"body-large"',
        '"body"',
        '"body-secondary"',
        '"body-small"',
        '"label"',
        '"caption"',
        '"micro"',
        '"data-large"',
    )
    for token in expected:
        assert token in source

    # La gamme doit continuer à couvrir les extrêmes historiques utiles :
    # petits textes 7/8 pt et grands titres 16 pt, sans tailles locales.
    assert '"min_points": 7' in source
    assert '"min_points": 8' in source
    assert '"min_points": 16' in source
    assert '"min_points": 18' in source


def test_text_helpers_expose_the_complete_semantic_scale():
    source = _source(TEXT)
    expected_helpers = (
        "def Display(",
        "def H1(",
        "def H2(",
        "def H3(",
        "def H4(",
        "def H5(",
        "def H6(",
        "def Lead(",
        "def BodyLarge(",
        "def Body(",
        "def BodySecondary(",
        "def BodySmall(",
        "def Label(",
        "def Caption(",
        "def Micro(",
        "def DataLarge(",
    )
    for helper in expected_helpers:
        assert helper in source


def test_typography_remains_driven_by_native_font_and_interface_scale():
    source = _source(STYLES)
    assert "wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)" in source
    assert '"interface", "echelle_interface"' in source
    assert '"interface", "echelle_police"' in source
    assert "font.SetPointSize(points)" in source
