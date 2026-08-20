from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
if str(TEAMWORKS) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS))

from Utils import UTILS_Theme  # noqa: E402


def test_explicit_theme_overrides_system_detection(monkeypatch):
    monkeypatch.setattr(UTILS_Theme, "_system_dark_from_os", lambda: False)
    assert UTILS_Theme.is_dark_theme("Sombre") is True
    assert UTILS_Theme.is_dark_theme("Clair") is False


def test_system_theme_uses_os_detection(monkeypatch):
    monkeypatch.setattr(UTILS_Theme, "_system_dark_from_os", lambda: True)
    assert UTILS_Theme.is_dark_theme("Systeme") is True
    monkeypatch.setattr(UTILS_Theme, "_system_dark_from_os", lambda: False)
    assert UTILS_Theme.is_dark_theme("Systeme") is False


def test_windows_personalize_setting_is_the_primary_windows_source():
    source = (TEAMWORKS / "Utils" / "UTILS_Theme.py").read_text(encoding="utf-8")
    assert "AppsUseLightTheme" in source
    assert r"Themes\\Personalize" in source
    assert "wx.SystemSettings.GetAppearance()" in source


def test_native_controls_are_not_flat_repainted():
    source = (TEAMWORKS / "Utils" / "UTILS_Theme.py").read_text(encoding="utf-8")
    assert "On évite volontairement de repeindre" in source
    assert 'getattr(wx, "Button", None)' in source
    assert 'getattr(wx, "Choice", None)' in source
    assert 'getattr(wx, "ComboBox", None)' in source
    assert 'wx.SystemOptions.SetOption("msw.dark-mode"' in source


def test_dark_fallback_uses_distinct_windows_like_surface_levels():
    source = (TEAMWORKS / "Utils" / "UTILS_Theme.py").read_text(encoding="utf-8")
    assert '"window": wx.Colour(32, 32, 32)' in source
    assert '"panel": wx.Colour(43, 43, 43)' in source
    assert '"control": wx.Colour(50, 50, 50)' in source
