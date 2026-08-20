from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "teamworks" / "Utils" / "UTILS_Theme.py"
SOURCE = THEME.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _function_source(name):
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(SOURCE, node) or ""
    raise AssertionError(f"fonction introuvable : {name}")


def test_explicit_themes_take_priority_over_system_detection():
    source = _function_source("is_dark_theme")
    assert 'if kind == "dark"' in source
    assert "return True" in source
    assert 'if kind == "light"' in source
    assert "return False" in source
    assert "return _system_dark_from_os()" in source


def test_system_theme_has_a_distinct_kind():
    source = _function_source("_theme_kind")
    assert 'return "dark"' in source
    assert 'return "light"' in source
    assert 'return "system"' in source


def test_windows_personalize_setting_is_the_primary_windows_source():
    windows_source = _function_source("_windows_apps_dark")
    system_source = _function_source("_system_dark_from_os")
    assert "AppsUseLightTheme" in windows_source
    assert "Themes\\Personalize" in windows_source
    assert "_windows_apps_dark()" in system_source
    assert "wx.SystemSettings.GetAppearance()" in system_source


def test_native_controls_are_not_flat_repainted():
    source = _function_source("_apply_palette")
    native_source = _function_source("enable_native_dark_mode")
    assert "leur apparence native sombre est préférable" in source
    assert 'getattr(wx, "Button", None)' in source
    assert 'getattr(wx, "Choice", None)' in source
    assert 'getattr(wx, "ComboBox", None)' in source
    assert 'wx.SystemOptions.SetOption("msw.dark-mode"' in native_source


def test_dark_fallback_uses_distinct_windows_like_surface_levels():
    source = _function_source("_native_palette")
    assert '"window": wx.Colour(32, 32, 32)' in source
    assert '"panel": wx.Colour(43, 43, 43)' in source
    assert '"control": wx.Colour(50, 50, 50)' in source


def test_system_dark_repairs_only_obviously_light_surfaces():
    source = _function_source("_apply_palette")
    assert 'theme_kind == "dark" or _looks_light(current_bg)' in source
    assert 'theme_kind == "dark" or _looks_dark(current_fg)' in source
    assert 'background = palette["window"]' in source
    assert 'background = palette["panel"]' in source
    assert 'background = palette["control"]' in source


def test_system_mode_keeps_other_widgets_entirely_native():
    source = _function_source("_apply_palette")
    assert "Les autres widgets restent entièrement natifs en mode Système" in source
    assert 'if theme_kind == "dark" and not isinstance(' in source


def test_contrast_detection_is_bidirectional():
    light_source = _function_source("_looks_light")
    dark_source = _function_source("_looks_dark")
    assert "_colour_luminance" in light_source
    assert "_colour_luminance" in dark_source
