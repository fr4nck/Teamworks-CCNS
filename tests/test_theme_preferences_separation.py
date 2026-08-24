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


def _wx_attributes(path):
    return {
        node.attr
        for node in ast.walk(_tree(path))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "wx"
    }


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
    assert '("echelle_interface", "100")' in source
    assert '("echelle_police", "100")' in source


def test_customize_migrates_legacy_scale_before_inserting_defaults():
    source = _source(CUSTOMIZE_PATH)
    migration = source.split("# Migration TW-189", 1)[1].split(
        "for section, valeurs in LISTE_DONNEES", 1
    )[0]
    assert 'has_option("interface", "echelle_police")' in migration
    assert '"echelle_interface"' in migration
    assert 'self.cfg.get("interface", "echelle_police")' in migration


def test_theme_engine_reads_appearance_before_legacy_theme():
    source = _source(THEME_PATH)
    appearance_pos = source.index('has_option("interface", "appearance")')
    legacy_pos = source.index('has_option("interface", "theme")')
    assert appearance_pos < legacy_pos
    assert "_legacy_theme_as_appearance" in source
    assert 'os.environ.get("TEAMWORKS_APPEARANCE"' in source


def test_theme_engine_prefers_interface_scale_and_keeps_legacy_alias():
    source = _source(THEME_PATH)
    assert 'os.environ.get("TEAMWORKS_UI_SCALE"' in source
    assert 'os.environ.get("TEAMWORKS_FONT_SCALE"' in source
    assert source.index('os.environ.get("TEAMWORKS_UI_SCALE"') < source.index(
        'os.environ.get("TEAMWORKS_FONT_SCALE"'
    )
    modern = source.index('has_option("interface", "echelle_interface")')
    legacy = source.index('has_option("interface", "echelle_police")')
    assert modern < legacy
    assert "def interface_scale_percent" in source
    assert "return interface_scale_percent()" in source


def test_black_accent_no_longer_forces_dark_mode():
    source = _source(THEME_PATH)
    legacy_function = source.split("def _legacy_theme_as_appearance", 1)[1].split(
        "def _config_values", 1
    )[0]
    assert '"noir"' not in legacy_function
    dark_names = source.split("DARK_THEME_NAMES =", 1)[1].split("\n", 1)[0]
    assert "noir" not in dark_names.lower()


def test_interface_stores_accent_separately_and_syncs_legacy_appearance():
    source = _source(INTERFACE_PATH)
    assert '"interface", "accent"' in source
    assert '_LEGACY_APPEARANCE_NAMES' in source
    assert '"system": "Systeme"' in source
    assert '"light": "Clair"' in source
    assert '"dark": "Sombre"' in source


def test_preferences_expose_accent_appearance_and_interface_scale():
    source = _source(PREFERENCES_PATH)
    assert 'THEMES = ["Système", "Clair", "Sombre"]' in source
    assert "ACCENTS =" in source
    assert "APPEARANCES =" in source
    assert '"Accent :"' in source
    assert '"Apparence :"' in source
    assert '"Échelle de l\'interface :"' in source
    assert '"echelle_interface"' in source
    assert '"echelle_police"' in source
    assert "UTILS_Interface.SetTheme" in source
    assert "UTILS_Interface.SetAppearanceMode" in source


def test_preferences_do_not_overwrite_accent_with_legacy_appearance():
    source = _source(PREFERENCES_PATH)
    on_ok = source.split("def OnOk", 1)[1]
    assert "UTILS_Interface.SetTheme" in on_ok
    assert "UTILS_Interface.SetAppearanceMode" in on_ok
    assert 'SetValeur("interface", "theme"' not in on_ok
    assert "values = [" not in on_ok


def test_preferences_use_charter_typography_spacing_and_window_profile():
    source = _source(PREFERENCES_PATH)
    assert "FlexGridSizer" not in source
    assert "wx.BoxSizer" in source
    assert "def _ligne" in source
    assert "CTRL_Texte.H1" in source
    assert "CTRL_Texte.Label" in source
    assert "CTRL_Texte.BodySecondary" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "compact")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("dialog_padding")' in source
    assert "SetPointSize" not in source
    assert "SetSize((560, 430))" not in source


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


def test_global_theme_scales_native_metrics_without_reintroducing_toolbook():
    source = _source(THEME_PATH)
    wx_attributes = _wx_attributes(THEME_PATH)
    assert "BASE_METRICS" in source
    assert "def scale_px" in source
    assert "def metrics" in source
    assert "def _apply_metrics" in source
    assert '"control_height": 28' in source
    assert '"toolbar_icon": 24' in source
    assert "wx.ToolBar" in source
    assert "wx.Notebook" in source
    assert "SetToolBitmapSize" in source
    assert "SetPadding" in source
    assert "Toolbook" not in wx_attributes
