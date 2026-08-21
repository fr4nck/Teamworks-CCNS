from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "teamworks" / "Utils" / "UTILS_Interface.py"
STYLES = ROOT / "teamworks" / "Utils" / "UTILS_Styles.py"
CHARTER = ROOT / "docs" / "CHARTE_GRAPHIQUE_TEAMWORKS.md"


def _read(path):
    return path.read_text(encoding="utf-8")


def test_exactly_five_colour_families_are_declared():
    source = _read(INTERFACE)
    for family in ("neutral", "primary", "success", "warning", "danger"):
        assert '"%s"' % family in source
    assert "COLOUR_FAMILIES" in source
    assert '"info": "primary"' in source
    assert '"selection": "primary"' in source
    assert '"focus": "primary"' in source
    assert '"info": accent["primary"]' in source


def test_spacing_icons_controls_and_window_profiles_are_centralised():
    source = _read(STYLES)
    for spacing in ("none", "xs", "sm", "md", "lg", "xl", "2xl"):
        assert '"%s"' % spacing in source
    for profile in ("compact", "standard", "wide", "workspace"):
        assert '"%s"' % profile in source
    for icon in ("micro", "small", "medium", "large", "hero"):
        assert '"%s"' % icon in source
    assert "ICON_SIZES" in source
    assert "CONTROL_METRICS" in source
    assert '"button_min_height"' in source
    assert '"footer_min_height"' in source
    assert "GetIconSize" in source
    assert "GetControlMetric" in source
    assert "GetLayoutSpacing" in source
    assert "GetWindowSize" in source
    assert "ApplyWindowProfile" in source


def test_charter_documents_semantic_design_rules():
    source = _read(CHARTER)
    assert "cinq familles" in source.lower()
    assert "Neutre" in source
    assert "Primaire" in source
    assert "Succès" in source
    assert "Avertissement" in source
    assert "Danger" in source
    assert "compact" in source
    assert "workspace" in source
    assert "H1" in source and "H6" in source
    assert "Icônes et contrôles" in source
    assert "CTRL_Section.py" in source
