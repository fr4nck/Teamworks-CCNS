import ast
from pathlib import Path


THEME_PATH = Path("teamworks/Utils/UTILS_Theme.py")
CUSTOMIZE_PATH = Path("teamworks/Utils/UTILS_Customize.py")
INTERFACE_PATH = Path("teamworks/Utils/UTILS_Interface.py")
PREFERENCES_PATH = Path("teamworks/Dlg/DLG_Preferences.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path))


def test_display_modules_remain_valid_python():
    _tree(THEME_PATH)
    _tree(CUSTOMIZE_PATH)
    _tree(INTERFACE_PATH)
    _tree(PREFERENCES_PATH)


def test_customize_keeps_tw121_and_new_display_defaults():
    source = _source(CUSTOMIZE_PATH)

    assert '("theme", "Systeme")' in source
    assert '("accent", "Vert")' in source
    assert '("appearance", "system")' in source
    assert '("echelle_police", "100")' in source


def test_theme_engine_reads_appearance_before_legacy_theme():
    source = _source(THEME_PATH)

    appearance_pos = source.index('has_option("interface", "appearance")')
    legacy_pos = source.index('has_option("interface", "theme")')
    assert appearance_pos < legacy_pos
    assert "_legacy_theme_as_appearance" in source
    assert 'os.environ.get("TEAMWORKS_APPEARANCE"' in source


def test_black_accent_no_longer_forces_dark_mode():
    source = _source(THEME_PATH)
    legacy_function = source.split("def _legacy_theme_as_appearance", 1)[1].split(
        "def _config_values", 1
    )[0]

    assert '"noir"' not in legacy_function


def test_interface_stores_accent_separately_and_syncs_legacy_appearance():
    source = _source(INTERFACE_PATH)

    assert '"interface", "accent"' in source
    assert '_LEGACY_APPEARANCE_NAMES' in source
    assert '"system": "Systeme"' in source
    assert '"light": "Clair"' in source
    assert '"dark": "Sombre"' in source


def test_preferences_expose_accent_and_appearance_separately():
    source = _source(PREFERENCES_PATH)

    assert 'THEMES = ["Système", "Clair", "Sombre"]' in source
    assert "ACCENTS =" in source
    assert "APPEARANCES =" in source
    assert 'label="Accent :"' in source
    assert 'label="Apparence :"' in source
    assert "UTILS_Interface.SetTheme" in source
    assert "UTILS_Interface.SetAppearanceMode" in source


def test_global_theme_targets_dense_desktop_controls():
    source = _source(THEME_PATH)

    assert "wx.ListCtrl" in source
    assert "wx.SearchCtrl" in source
    assert "wx.TreeCtrl" in source
    assert "wx.TextCtrl" in source
    assert 'GetToken("surface_container_lowest"' in source
    assert 'GetToken("on_surface"' in source
    assert 'GetToken("selection"' in source
    assert "stEmptyListMsg" in source
