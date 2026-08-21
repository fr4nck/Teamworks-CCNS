#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gardes statiques du contrat d'affichage Teamworks-CCNS.

Ces tests évitent d'importer wxPython : ils doivent donc rester exécutables dans
la CI générique tout en verrouillant les points de raccord critiques de TW-119.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "teamworks"
THEME = SOURCES / "Utils" / "UTILS_Theme.py"
CUSTOMIZE = SOURCES / "Utils" / "UTILS_Customize.py"
PREFERENCES = SOURCES / "Dlg" / "DLG_Preferences.py"


def _read(path: Path) -> str:
    assert path.is_file(), f"Fichier requis absent : {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_display_preferences_files_are_packaged_in_sources():
    for path in (THEME, CUSTOMIZE, PREFERENCES):
        assert path.is_file(), f"Fichier requis absent : {path.relative_to(ROOT)}"


def test_default_theme_is_system_and_font_scale_is_100_percent():
    source = _read(CUSTOMIZE)
    assert '("theme", "Systeme")' in source
    assert '("echelle_police", "100")' in source


def test_preferences_offer_three_modes_and_accessibility_scale_bounds():
    source = _read(PREFERENCES)
    assert 'THEMES = ["Système", "Clair", "Sombre"]' in source
    assert '("system", "Système")' in source
    assert '("light", "Clair")' in source
    assert '("dark", "Sombre")' in source
    assert "min=80" in source
    assert "max=200" in source
    assert "appearance_codes = [code for code, label in self.APPEARANCES]" in source


def test_theme_service_supports_system_light_dark_and_scale_clamping():
    source = _read(THEME)
    assert "DARK_THEME_NAMES" in source
    assert "LIGHT_THEME_NAMES" in source
    assert "SYSTEM_THEME_NAMES" in source
    assert "max(80, min(200" in source
    assert "wx.SystemSettings.GetAppearance()" in source


def test_theme_service_reads_utf8_bom_and_legacy_windows_profiles():
    source = _read(THEME)
    assert 'CONFIG_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")' in source
    assert "raw.decode(encoding)" in source
    assert "parser.read_string(text)" in source
    assert "except (OSError, ValueError)" in source


def test_preferences_are_reachable_from_settings_menu():
    source = _read(THEME)
    assert "wx.ID_PREFERENCES" in source
    assert "Préférences d'affichage" in source
    assert "from Dlg import DLG_Preferences" in source


def test_application_installs_native_and_recursive_theming_hooks():
    source = _read(CUSTOMIZE)
    assert "UTILS_Theme.enable_native_dark_mode()" in source
    assert "UTILS_Theme.install_auto_theming()" in source
