#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gestion centralisée de l'affichage Teamworks-CCNS."""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from configparser import ConfigParser

import wx

DARK_THEME_NAMES = {"sombre", "dark", "noir"}
LIGHT_THEME_NAMES = {"clair", "light", "blanc"}
SYSTEM_THEME_NAMES = {"systeme", "système", "system", "auto"}
CONFIG_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")

DARK_PALETTE = {
    "window": wx.Colour(30, 30, 30),
    "panel": wx.Colour(37, 37, 38),
    "control": wx.Colour(45, 45, 48),
    "text": wx.Colour(235, 235, 235),
    "selection": wx.Colour(55, 95, 135),
}

_PATCHED = False
_MENU_INSTALLED = False


def _read_config(path):
    raw = Path(path).read_bytes()
    last_error = None
    for encoding in CONFIG_ENCODINGS:
        try:
            text = raw.decode(encoding)
            parser = ConfigParser()
            parser.read_string(text)
            return parser
        except (UnicodeError, configparser.Error) as exc:
            last_error = exc
    raise ValueError(f"Configuration illisible : {path}") from last_error


def _config_values():
    theme = os.environ.get("TEAMWORKS_THEME", "").strip()
    scale = os.environ.get("TEAMWORKS_FONT_SCALE", "").strip()
    appdata = os.environ.get("APPDATA")
    candidates = list(Path(appdata).rglob("Customize.ini")) if appdata else []
    for path in candidates:
        try:
            parser = _read_config(path)
            if not theme and parser.has_option("interface", "theme"):
                theme = parser.get("interface", "theme")
            if not scale and parser.has_option("interface", "echelle_police"):
                scale = parser.get("interface", "echelle_police")
            if theme and scale:
                break
        except (OSError, ValueError):
            continue
    try:
        font_scale = max(80, min(200, int(scale or "100")))
    except ValueError:
        font_scale = 100
    return theme or "Systeme", font_scale


def requested_theme():
    return _config_values()[0]


def font_scale_percent():
    return _config_values()[1]


def is_dark_theme(theme=None):
    value = (theme or requested_theme()).strip().lower()
    if value in DARK_THEME_NAMES:
        return True
    if value in LIGHT_THEME_NAMES:
        return False
    try:
        appearance = wx.SystemSettings.GetAppearance()
        return bool(hasattr(appearance, "IsDark") and appearance.IsDark())
    except Exception:
        return False


def enable_native_dark_mode(theme=None):
    dark = is_dark_theme(theme)
    try:
        wx.SystemOptions.SetOption("msw.dark-mode", 2 if dark else 0)
    except Exception:
        pass
    return dark


def _scale_font(window):
    scale = font_scale_percent()
    if scale == 100 or getattr(window, "_teamworks_font_scaled", False):
        return
    try:
        font = window.GetFont()
        if font and font.IsOk():
            current = font.GetFractionalPointSize() if hasattr(font, "GetFractionalPointSize") else font.GetPointSize()
            new_size = max(6.0, current * scale / 100.0)
            if hasattr(font, "SetFractionalPointSize"):
                font.SetFractionalPointSize(new_size)
            else:
                font.SetPointSize(int(round(new_size)))
            window.SetFont(font)
            window._teamworks_font_scaled = True
    except Exception:
        pass


def _apply_dark_palette(window):
    background = DARK_PALETTE["panel"]
    if isinstance(window, (wx.Frame, wx.Dialog)):
        background = DARK_PALETTE["window"]
    elif isinstance(window, (wx.TextCtrl, wx.ComboBox, wx.Choice, wx.ListBox,
                             wx.CheckListBox, wx.ListCtrl, wx.TreeCtrl, wx.SpinCtrl)):
        background = DARK_PALETTE["control"]
    window.SetBackgroundColour(background)
    window.SetForegroundColour(DARK_PALETTE["text"])


def apply_to_window(window, recursive=True):
    if window is None:
        return
    _scale_font(window)
    if is_dark_theme():
        try:
            _apply_dark_palette(window)
        except Exception:
            pass
    if recursive:
        try:
            children = window.GetChildren()
        except Exception:
            children = []
        for child in children:
            apply_to_window(child, True)
    try:
        window.Layout()
        window.Refresh()
    except Exception:
        pass


def _install_preferences_menu(frame):
    global _MENU_INSTALLED
    if _MENU_INSTALLED or not isinstance(frame, wx.Frame):
        return
    menu_bar = frame.GetMenuBar()
    if menu_bar is None:
        return
    for index in range(menu_bar.GetMenuCount()):
        label = menu_bar.GetMenuLabel(index).replace("&", "").lower()
        if "param" in label:
            menu = menu_bar.GetMenu(index)
            menu.InsertSeparator(0)
            item = menu.Insert(0, wx.ID_PREFERENCES, "Préférences d'affichage…")
            def open_preferences(event):
                from Dlg import DLG_Preferences
                dialog = DLG_Preferences.Dialog(frame)
                dialog.ShowModal()
                dialog.Destroy()
            frame.Bind(wx.EVT_MENU, open_preferences, item)
            _MENU_INSTALLED = True
            return


def install_auto_theming():
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    original_show = wx.Window.Show
    def themed_show(window, *args, **kwargs):
        _install_preferences_menu(window)
        apply_to_window(window, True)
        return original_show(window, *args, **kwargs)
    wx.Window.Show = themed_show

    original_show_modal = wx.Dialog.ShowModal
    def themed_show_modal(dialog, *args, **kwargs):
        apply_to_window(dialog, True)
        return original_show_modal(dialog, *args, **kwargs)
    wx.Dialog.ShowModal = themed_show_modal
