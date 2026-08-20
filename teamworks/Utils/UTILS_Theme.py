#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gestion centralisée de l'affichage Teamworks CCNS.

Le thème ``Système`` doit suivre l'OS, pas fabriquer une apparence parallèle.
Sous Windows, wxWidgets ne remonte pas toujours correctement le mode sombre ;
on complète donc sa détection avec le réglage utilisateur Windows. Les contrôles
natifs restent ensuite natifs autant que possible : on ne recolore manuellement
que les surfaces que wx laisse manifestement incohérentes.
"""

from __future__ import annotations

import configparser
import os
import sys
from pathlib import Path
from configparser import ConfigParser

import appdirs
import wx

import Chemins

DARK_THEME_NAMES = {"sombre", "dark", "noir"}
LIGHT_THEME_NAMES = {"clair", "light", "blanc"}
SYSTEM_THEME_NAMES = {"systeme", "système", "system", "auto"}
CONFIG_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")

_PATCHED = False
_MENU_INSTALLED = False
_CONFIG_CACHE = None


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


def _customize_path():
    """Retourne exactement le même emplacement que UTILS_Fichiers.GetRepUtilisateur.

    Cette fonction reste autonome pour éviter la dépendance circulaire
    UTILS_Customize -> UTILS_Theme -> UTILS_Fichiers -> UTILS_Customize.
    """
    portable = Path(Chemins.GetMainPath("Portable"))
    if portable.is_dir():
        return portable / "Customize.ini"

    config_dir = Path(appdirs.user_config_dir(appname=None, appauthor=False, roaming=True))
    return config_dir / "teamworks" / "Customize.ini"


def refresh_preferences():
    """Invalide le cache après migration ou modification des préférences."""
    global _CONFIG_CACHE
    _CONFIG_CACHE = None


def _config_values():
    global _CONFIG_CACHE
    env_theme = os.environ.get("TEAMWORKS_THEME", "").strip()
    env_scale = os.environ.get("TEAMWORKS_FONT_SCALE", "").strip()

    if _CONFIG_CACHE is not None and not env_theme and not env_scale:
        return _CONFIG_CACHE

    theme = env_theme
    scale = env_scale
    path = _customize_path()
    config_exists = path.is_file()
    if config_exists:
        try:
            parser = _read_config(path)
            if not theme and parser.has_option("interface", "theme"):
                theme = parser.get("interface", "theme")
            if not scale and parser.has_option("interface", "echelle_police"):
                scale = parser.get("interface", "echelle_police")
        except (OSError, ValueError):
            pass

    try:
        font_scale = max(80, min(200, int(scale or "100")))
    except ValueError:
        font_scale = 100

    values = (theme or "Systeme", font_scale)
    if config_exists and not env_theme and not env_scale:
        _CONFIG_CACHE = values
    return values


def requested_theme():
    return _config_values()[0]


def font_scale_percent():
    return _config_values()[1]


def _theme_kind(theme=None):
    value = (theme or requested_theme()).strip().lower()
    if value in DARK_THEME_NAMES:
        return "dark"
    if value in LIGHT_THEME_NAMES:
        return "light"
    return "system"


def _windows_apps_dark():
    """Retourne le choix clair/sombre des applications Windows, ou None.

    ``wx.SystemSettings.GetAppearance()`` peut rester en mode clair sous Windows
    10/11 alors que les applications sont configurées en sombre. La valeur
    ``AppsUseLightTheme`` est la source utilisateur utilisée par Windows pour ce
    choix. L'accès est volontairement local et ne lit aucune donnée personnelle.
    """
    if sys.platform != "win32":
        return None
    try:
        import winreg

        path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return int(value) == 0
    except (ImportError, OSError, ValueError, TypeError):
        return None


def _system_dark_from_os():
    windows_value = _windows_apps_dark()
    if windows_value is not None:
        return windows_value
    try:
        appearance = wx.SystemSettings.GetAppearance()
        return bool(hasattr(appearance, "IsDark") and appearance.IsDark())
    except Exception:
        return False


def is_dark_theme(theme=None):
    kind = _theme_kind(theme)
    if kind == "dark":
        return True
    if kind == "light":
        return False
    return _system_dark_from_os()


def enable_native_dark_mode(theme=None):
    """Demande à wxWidgets le rendu natif sombre avant création des fenêtres."""
    dark = is_dark_theme(theme)
    if sys.platform == "win32":
        try:
            # 2 active le support sombre natif de wxMSW lorsque disponible.
            wx.SystemOptions.SetOption("msw.dark-mode", 2 if dark else 0)
        except Exception:
            pass
    return dark


def _system_colour(colour_id, fallback):
    try:
        colour = wx.SystemSettings.GetColour(colour_id)
        if colour and colour.IsOk():
            return colour
    except Exception:
        pass
    return wx.Colour(*fallback)


def _colour_luminance(colour):
    return 0.2126 * colour.Red() + 0.7152 * colour.Green() + 0.0722 * colour.Blue()


def _looks_light(colour, threshold=150):
    try:
        return bool(colour and colour.IsOk() and _colour_luminance(colour) > threshold)
    except Exception:
        return False


def _looks_dark(colour, threshold=105):
    try:
        return bool(colour and colour.IsOk() and _colour_luminance(colour) < threshold)
    except Exception:
        return False


def _native_palette(dark):
    """Construit une palette de surfaces cohérente avec le rendu système.

    Les valeurs de repli sombres reprennent les niveaux de surfaces Windows 11 :
    fond principal, cartes/panneaux, puis zones de saisie. Elles ne servent que
    lorsque wxMSW continue de renvoyer ses anciennes couleurs claires.
    """
    palette = {
        "window": _system_colour(wx.SYS_COLOUR_WINDOW, (255, 255, 255)),
        "panel": _system_colour(wx.SYS_COLOUR_BTNFACE, (240, 240, 240)),
        "control": _system_colour(wx.SYS_COLOUR_WINDOW, (255, 255, 255)),
        "text": _system_colour(wx.SYS_COLOUR_WINDOWTEXT, (0, 0, 0)),
        "button_text": _system_colour(wx.SYS_COLOUR_BTNTEXT, (0, 0, 0)),
        "selection": _system_colour(wx.SYS_COLOUR_HIGHLIGHT, (0, 120, 215)),
        "selection_text": _system_colour(wx.SYS_COLOUR_HIGHLIGHTTEXT, (255, 255, 255)),
    }
    if dark and _colour_luminance(palette["window"]) > 128:
        palette.update({
            "window": wx.Colour(32, 32, 32),
            "panel": wx.Colour(43, 43, 43),
            "control": wx.Colour(50, 50, 50),
            "text": wx.Colour(243, 243, 243),
            "button_text": wx.Colour(243, 243, 243),
            "selection": _system_colour(wx.SYS_COLOUR_HIGHLIGHT, (0, 95, 184)),
            "selection_text": wx.Colour(255, 255, 255),
        })
    return palette


def _scale_font(window, scale):
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


def _set_colours(window, background=None, foreground=None):
    try:
        if background is not None:
            window.SetBackgroundColour(background)
        if foreground is not None:
            window.SetForegroundColour(foreground)
    except Exception:
        pass


def _background_colour(window):
    try:
        return window.GetBackgroundColour()
    except Exception:
        return None


def _foreground_colour(window):
    try:
        return window.GetForegroundColour()
    except Exception:
        return None


def _apply_palette(window, palette, dark, theme_kind):
    """Corrige uniquement les surfaces que le rendu natif laisse incohérentes.

    En mode ``Système``, Windows reste prioritaire : on n'impose jamais une
    palette parallèle à une surface déjà correctement sombre. On corrige seulement
    les îlots clairement restés en apparence claire ou un texte devenu illisible.

    En mode ``Sombre`` explicite, la palette Teamworks sert de repli cohérent.
    On évite dans tous les cas de repeindre ``wx.Button``, ``wx.Choice`` et
    ``wx.ComboBox`` : sous Windows leur apparence native sombre est préférable.
    """
    if not dark:
        return

    if isinstance(window, (wx.Frame, wx.Dialog)):
        current_bg = _background_colour(window)
        current_fg = _foreground_colour(window)
        background = palette["window"] if theme_kind == "dark" or _looks_light(current_bg) else None
        foreground = palette["text"] if theme_kind == "dark" or _looks_dark(current_fg) else None
        _set_colours(window, background, foreground)
        return

    if isinstance(window, wx.Panel):
        current_bg = _background_colour(window)
        current_fg = _foreground_colour(window)
        background = palette["panel"] if theme_kind == "dark" or _looks_light(current_bg) else None
        foreground = palette["text"] if theme_kind == "dark" or _looks_dark(current_fg) else None
        _set_colours(window, background, foreground)
        return

    # Libellés : jamais de fond imposé, seulement une correction de contraste.
    label_types = tuple(
        cls for cls in (
            getattr(wx, "StaticText", None),
            getattr(wx, "StaticBox", None),
            getattr(wx, "CheckBox", None),
            getattr(wx, "RadioButton", None),
        ) if cls is not None
    )
    if label_types and isinstance(window, label_types):
        current_fg = _foreground_colour(window)
        if theme_kind == "dark" or _looks_dark(current_fg):
            _set_colours(window, foreground=palette["text"])
        return

    # Contrôles de contenu qui restent parfois blancs malgré msw.dark-mode.
    content_types = tuple(
        cls for cls in (
            getattr(wx, "TextCtrl", None),
            getattr(wx, "ListBox", None),
            getattr(wx, "CheckListBox", None),
            getattr(wx, "ListCtrl", None),
            getattr(wx, "TreeCtrl", None),
            getattr(wx, "SpinCtrl", None),
        ) if cls is not None
    )
    if content_types and isinstance(window, content_types):
        current_bg = _background_colour(window)
        current_fg = _foreground_colour(window)
        background = palette["control"] if theme_kind == "dark" or _looks_light(current_bg) else None
        foreground = palette["text"] if theme_kind == "dark" or _looks_dark(current_fg) else None
        _set_colours(window, background, foreground)
        return

    # Les autres widgets restent entièrement natifs en mode Système. En mode
    # Sombre explicite, seul le texte non natif est corrigé si nécessaire.
    if theme_kind == "dark" and not isinstance(
        window,
        tuple(cls for cls in (
            getattr(wx, "Button", None),
            getattr(wx, "Choice", None),
            getattr(wx, "ComboBox", None),
        ) if cls is not None),
    ):
        _set_colours(window, foreground=palette["text"])


def apply_to_window(window, recursive=True, theme=None, scale=None, palette=None):
    if window is None:
        return

    if theme is None or scale is None:
        configured_theme, configured_scale = _config_values()
        theme = configured_theme if theme is None else theme
        scale = configured_scale if scale is None else scale
    kind = _theme_kind(theme)
    dark = is_dark_theme(theme)
    palette = palette or _native_palette(dark)

    _scale_font(window, scale)
    _apply_palette(window, palette, dark, kind)

    if recursive:
        try:
            children = window.GetChildren()
        except Exception:
            children = []
        for child in children:
            apply_to_window(child, True, theme=theme, scale=scale, palette=palette)

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
                refresh_preferences()

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
