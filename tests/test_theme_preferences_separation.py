import ast
from pathlib import Path


THEME_PATH = Path("teamworks/Utils/UTILS_Theme.py")
CUSTOMIZE_PATH = Path("teamworks/Utils/UTILS_Customize.py")
PREFERENCES_PATH = Path("teamworks/Dlg/DLG_Preferences.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path))


def test_display_modules_remain_valid_python():
    _tree(THEME_PATH)
    _tree(CUSTOMIZE_PATH)
    _tree(PREFERENCES_PATH)


def test_customize_has_separate_accent_and_appearance_defaults():
    source = _source(CUSTOMIZE_PATH)

    assert '("theme", "Vert")' in source
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


def test_preferences_expose_accent_and_appearance_separately():
    source = _source(PREFERENCES_PATH)

    assert "ACCENTS =" in source
    assert "APPEARANCES =" in source
    assert 'label="Accent :"' in source
    assert 'label="Apparence :"' in source
    assert '"theme",' in source
    assert '"appearance",' in source


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
