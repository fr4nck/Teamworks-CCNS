#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gestion centralisée du thème visuel Teamworks-CCNS."""

from __future__ import annotations

import os
from pathlib import Path
from configparser import ConfigParser

import wx


DARK_THEME_NAMES = {"sombre", "dark", "noir"}

DARK_PALETTE = {
    "window": wx.Colour(30, 30, 30),
    "panel": wx.Colour(37, 37, 38),
    "control": wx.Colour(45, 45, 48),
    "text": wx.Colour(235, 235, 235),
    "muted_text": wx.Colour(190, 190, 190),
    "accent": wx.Colour(75, 150, 220),
}


def _read_requested_theme() -> str:
    forced = os.environ.get("TEAMWORKS_THEME", "").strip()
    if forced:
        return forced

    appdata = os.environ.get("APPDATA")
    candidates = []
    if appdata:
        candidates.extend(Path(appdata).rglob("Customize.ini"))

    for path in candidates:
        parser = ConfigParser()
        try:
            parser.read(path, encoding="utf-8")
            if parser.has_option("interface", "theme"):
                return parser.get("interface", "theme")
        except (OSError, UnicodeError):
            continue

    return "Sombre"


def is_dark_theme(theme: str | None = None) -> bool:
    value = (theme or _read_requested_theme()).strip().lower()
    return value in DARK_THEME_NAMES


def enable_native_dark_mode(theme: str | None = None) -> bool:
    """Active le rendu sombre natif lorsque wxPython/Windows le supporte."""
    if not is_dark_theme(theme):
        return False

    try:
        wx.SystemOptions.SetOption("msw.dark-mode", 2)
    except Exception:
        pass

    try:
        appearance = wx.SystemSettings.GetAppearance()
        if hasattr(appearance, "IsDark") and appearance.IsDark():
            return True
    except Exception:
        pass

    return True


def apply_to_window(window: wx.Window, recursive: bool = True) -> None:
    """Applique une palette sombre lisible aux contrôles déjà construits."""
    if not is_dark_theme():
        return

    try:
        window.SetBackgroundColour(DARK_PALETTE["panel"])
        window.SetForegroundColour(DARK_PALETTE["text"])
    except Exception:
        return

    if recursive:
        for child in window.GetChildren():
            apply_to_window(child, recursive=True)

    try:
        window.Refresh()
    except Exception:
        pass
