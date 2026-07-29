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
    "selection": wx.Colour(55, 95, 135),
}

_PATCHED = False


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

    return True


def _is_input_control(window: wx.Window) -> bool:
    classes = (
        wx.TextCtrl,
        wx.ComboBox,
        wx.Choice,
        wx.ListBox,
        wx.CheckListBox,
        wx.ListCtrl,
        wx.TreeCtrl,
        wx.SpinCtrl,
    )
    return isinstance(window, classes)


def _apply_control_palette(window: wx.Window) -> None:
    background = DARK_PALETTE["panel"]
    foreground = DARK_PALETTE["text"]

    if isinstance(window, (wx.Frame, wx.Dialog)):
        background = DARK_PALETTE["window"]
    elif _is_input_control(window):
        background = DARK_PALETTE["control"]
    elif isinstance(window, wx.StaticText):
        foreground = DARK_PALETTE["text"]

    window.SetBackgroundColour(background)
    window.SetForegroundColour(foreground)

    if isinstance(window, wx.ListCtrl):
        try:
            window.SetTextColour(foreground)
        except Exception:
            pass

    # Plusieurs contrôles AGW/HTML historiques ne dérivent pas d'une classe
    # wx standard identifiable mais exposent les mêmes méthodes de couleur.
    class_name = window.__class__.__name__.lower()
    if "html" in class_name or "ultimatelist" in class_name:
        try:
            window.SetBackgroundColour(DARK_PALETTE["control"])
            window.SetForegroundColour(DARK_PALETTE["text"])
        except Exception:
            pass


def apply_to_window(window: wx.Window, recursive: bool = True) -> None:
    """Applique une palette sombre lisible à une fenêtre et ses contrôles."""
    if not is_dark_theme() or window is None:
        return

    try:
        _apply_control_palette(window)
    except Exception:
        return

    if recursive:
        try:
            children = window.GetChildren()
        except Exception:
            children = []
        for child in children:
            apply_to_window(child, recursive=True)

    try:
        window.Refresh()
    except Exception:
        pass


def install_auto_theming() -> None:
    """Thème automatiquement les fenêtres juste avant leur affichage.

    Le code historique crée de nombreux dialogues dans des modules séparés.
    Centraliser l'interception de ``Show`` et ``ShowModal`` évite d'ajouter un
    appel manuel dans chaque écran tout en conservant le comportement wx natif.
    """
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    original_show = wx.Window.Show

    def themed_show(window, *args, **kwargs):
        apply_to_window(window, recursive=True)
        return original_show(window, *args, **kwargs)

    wx.Window.Show = themed_show

    original_show_modal = wx.Dialog.ShowModal

    def themed_show_modal(dialog, *args, **kwargs):
        apply_to_window(dialog, recursive=True)
        return original_show_modal(dialog, *args, **kwargs)

    wx.Dialog.ShowModal = themed_show_modal
