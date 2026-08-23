#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gestion centralisée de l'affichage Teamworks-CCNS.

Le thème d'accent (Vert/Bleu/Noir) et l'apparence (clair/sombre/système) sont
volontairement séparés. Ce module applique l'apparence aux contrôles wx natifs,
délègue les couleurs sémantiques à ``UTILS_Interface`` et met à l'échelle les
métriques d'interface sans réintroduire le ``wx.Toolbook`` historique.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from configparser import ConfigParser

import appdirs
import wx

import Chemins
from Utils import UTILS_Interface

DARK_THEME_NAMES = {"sombre", "dark"}
LIGHT_THEME_NAMES = {"clair", "light", "blanc"}
SYSTEM_THEME_NAMES = {"systeme", "système", "system", "auto"}
CONFIG_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")

BASE_METRICS = {
    "space_xs": 4,
    "space_s": 8,
    "space_m": 12,
    "space_l": 16,
    "control_height": 28,
    "toolbar_icon": 24,
    "tab_padding_x": 10,
    "tab_padding_y": 6,
}

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
    portable = Path(Chemins.GetMainPath("Portable"))
    if portable.is_dir():
        return portable / "Customize.ini"
    config_dir = Path(appdirs.user_config_dir(appname=None, appauthor=False, roaming=True))
    return config_dir / "teamworks" / "Customize.ini"


def refresh_preferences():
    global _CONFIG_CACHE
    _CONFIG_CACHE = None


def _legacy_theme_as_appearance(value):
    value = (value or "").strip().lower()
    if value in DARK_THEME_NAMES:
        return "dark"
    if value in LIGHT_THEME_NAMES:
        return "light"
    if value in SYSTEM_THEME_NAMES:
        return "system"
    return ""


def _config_values():
    global _CONFIG_CACHE
    env_appearance = (
        os.environ.get("TEAMWORKS_APPEARANCE", "").strip()
        or os.environ.get("TEAMWORKS_THEME", "").strip()
    )
    env_scale = (
        os.environ.get("TEAMWORKS_UI_SCALE", "").strip()
        or os.environ.get("TEAMWORKS_FONT_SCALE", "").strip()
    )
    if _CONFIG_CACHE is not None and not env_appearance and not env_scale:
        return _CONFIG_CACHE

    appearance = env_appearance
    scale = env_scale
    path = _customize_path()
    config_exists = path.is_file()
    if config_exists:
        try:
            parser = _read_config(path)
            if not appearance and parser.has_option("interface", "appearance"):
                appearance = parser.get("interface", "appearance")
            if not appearance and parser.has_option("interface", "theme"):
                appearance = _legacy_theme_as_appearance(parser.get("interface", "theme"))
            if not scale:
                if parser.has_option("interface", "echelle_interface"):
                    scale = parser.get("interface", "echelle_interface")
                elif parser.has_option("interface", "echelle_police"):
                    scale = parser.get("interface", "echelle_police")
        except (OSError, ValueError):
            pass

    appearance = (appearance or "system").strip().lower()
    if appearance in DARK_THEME_NAMES:
        appearance = "dark"
    elif appearance in LIGHT_THEME_NAMES:
        appearance = "light"
    elif appearance in SYSTEM_THEME_NAMES:
        appearance = "system"
    else:
        appearance = "system"

    try:
        interface_scale = max(
            UTILS_Interface.INTERFACE_SCALE_MIN,
            min(
                UTILS_Interface.INTERFACE_SCALE_MAX,
                int(scale or str(UTILS_Interface.INTERFACE_SCALE_DEFAULT)),
            ),
        )
    except ValueError:
        interface_scale = UTILS_Interface.INTERFACE_SCALE_DEFAULT

    values = (appearance, interface_scale)
    if config_exists and not env_appearance and not env_scale:
        _CONFIG_CACHE = values
    return values


def requested_appearance():
    return _config_values()[0]


def requested_theme():
    return requested_appearance()


def interface_scale_percent():
    return _config_values()[1]


def font_scale_percent():
    return interface_scale_percent()


def scale_px(value, scale=None, minimum=1):
    if scale is None:
        scale = interface_scale_percent()
    return max(minimum, int(round(float(value) * scale / 100.0)))


def metrics(scale=None):
    if scale is None:
        scale = interface_scale_percent()
    return {name: scale_px(value, scale=scale) for name, value in BASE_METRICS.items()}


def is_dark_theme(theme=None):
    value = (theme or requested_appearance()).strip().lower()
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


def _native_palette(dark):
    palette = {
        "surface": _system_colour(wx.SYS_COLOUR_BTNFACE, (240, 240, 240)),
        "surface_low": _system_colour(wx.SYS_COLOUR_BTNFACE, (245, 245, 245)),
        "surface_high": _system_colour(wx.SYS_COLOUR_3DFACE, (232, 232, 232)),
        "control": _system_colour(wx.SYS_COLOUR_WINDOW, (255, 255, 255)),
        "text": _system_colour(wx.SYS_COLOUR_WINDOWTEXT, (0, 0, 0)),
        "text_variant": _system_colour(wx.SYS_COLOUR_GRAYTEXT, (100, 100, 100)),
        "button_text": _system_colour(wx.SYS_COLOUR_BTNTEXT, (0, 0, 0)),
        "selection": _system_colour(wx.SYS_COLOUR_HIGHLIGHT, (0, 120, 215)),
        "selection_text": _system_colour(wx.SYS_COLOUR_HIGHLIGHTTEXT, (255, 255, 255)),
        "outline": _system_colour(wx.SYS_COLOUR_3DSHADOW, (180, 180, 180)),
    }
    if dark and _colour_luminance(palette["control"]) > 128:
        palette.update({
            "surface": wx.Colour(32, 32, 32),
            "surface_low": wx.Colour(37, 37, 38),
            "surface_high": wx.Colour(52, 52, 52),
            "control": wx.Colour(45, 45, 48),
            "text": wx.Colour(240, 240, 240),
            "text_variant": wx.Colour(190, 190, 190),
            "button_text": wx.Colour(240, 240, 240),
            "selection": wx.Colour(0, 95, 184),
            "selection_text": wx.Colour(255, 255, 255),
            "outline": wx.Colour(83, 86, 90),
        })
    return palette


def _semantic_palette(dark):
    try:
        appearance = "dark" if dark else "light"
        return {
            "surface": UTILS_Interface.GetToken("surface", appearance=appearance),
            "surface_low": UTILS_Interface.GetToken("surface_container_low", appearance=appearance),
            "surface_high": UTILS_Interface.GetToken("surface_container_high", appearance=appearance),
            "control": UTILS_Interface.GetToken("surface_container_lowest", appearance=appearance),
            "text": UTILS_Interface.GetToken("on_surface", appearance=appearance),
            "text_variant": UTILS_Interface.GetToken("on_surface_variant", appearance=appearance),
            "button_text": UTILS_Interface.GetToken("on_surface", appearance=appearance),
            "selection": UTILS_Interface.GetToken("selection", appearance=appearance),
            "selection_text": UTILS_Interface.GetToken("selection_text", appearance=appearance),
            "outline": UTILS_Interface.GetToken("outline_variant", appearance=appearance),
        }
    except Exception:
        return _native_palette(dark)


def _font_point_size(font):
    if hasattr(font, "GetFractionalPointSize"):
        return float(font.GetFractionalPointSize())
    return float(font.GetPointSize())


def _set_font_point_size(font, value):
    value = max(6.0, float(value))
    if hasattr(font, "SetFractionalPointSize"):
        font.SetFractionalPointSize(value)
    else:
        font.SetPointSize(int(round(value)))


def _scale_font(window, scale):
    try:
        semantic_style = getattr(window, "_teamworks_text_style", None)
        if semantic_style:
            from Utils import UTILS_Styles
            window.SetFont(UTILS_Styles.GetFont(semantic_style))
            window._teamworks_font_scale_percent = scale
            window._teamworks_font_scaled = True
            return

        font = window.GetFont()
        if not font or not font.IsOk():
            return

        last_scale = getattr(window, "_teamworks_font_scale_percent", None)
        if last_scale == scale:
            return

        base_points = getattr(window, "_teamworks_font_base_points", None)
        if base_points is None:
            current = _font_point_size(font)
            if getattr(window, "_teamworks_font_scaled", False):
                previous_scale = last_scale or scale or 100
                base_points = current * 100.0 / float(previous_scale)
            else:
                base_points = current
            window._teamworks_font_base_points = base_points

        _set_font_point_size(font, base_points * float(scale) / 100.0)
        window.SetFont(font)
        window._teamworks_font_scale_percent = scale
        window._teamworks_font_scaled = True
    except Exception:
        pass


def _minimum_height(window, height):
    """Applique une hauteur de thème sans écraser un minimum métier explicite.

    Le minimum d'origine est mémorisé une seule fois. Le minimum effectif peut
    donc augmenter à 125 % puis redescendre à 100 % sans rester artificiellement
    gonflé par une ancienne application du thème.
    """
    try:
        minimum = window.GetMinSize()
        width = minimum.GetWidth() if minimum else -1
        current_height = minimum.GetHeight() if minimum else -1

        base_height = getattr(window, "_teamworks_min_height_base", None)
        if base_height is None:
            base_height = current_height
            window._teamworks_min_height_base = base_height

        target_height = max(int(base_height), int(height)) if base_height >= 0 else int(height)
        if current_height != target_height:
            window.SetMinSize((width, target_height))
    except Exception:
        pass


def _apply_metrics(window, scale):
    ui = metrics(scale)
    try:
        if hasattr(window, "InvalidateBestSize"):
            window.InvalidateBestSize()
    except Exception:
        pass

    if isinstance(window, wx.ToolBar):
        try:
            window.SetToolBitmapSize((ui["toolbar_icon"], ui["toolbar_icon"]))
            if hasattr(window, "SetToolPacking"):
                window.SetToolPacking(ui["space_xs"])
            if hasattr(window, "SetMargins"):
                window.SetMargins(ui["space_s"], ui["space_xs"])
            window.Realize()
            _minimum_height(window, window.GetBestSize().GetHeight())
        except Exception:
            pass
    elif isinstance(window, wx.Notebook):
        try:
            if hasattr(window, "SetPadding"):
                window.SetPadding((ui["tab_padding_x"], ui["tab_padding_y"]))
        except Exception:
            pass

    controls = (wx.Button, wx.TextCtrl, wx.ComboBox, wx.Choice, wx.SpinCtrl)
    if hasattr(wx, "ToggleButton"):
        controls = controls + (wx.ToggleButton,)
    if hasattr(wx, "SearchCtrl"):
        controls = controls + (wx.SearchCtrl,)
    if isinstance(window, controls):
        _minimum_height(window, ui["control_height"])


def _set_colours(window, background=None, foreground=None):
    try:
        if background is not None:
            window.SetBackgroundColour(background)
        if foreground is not None:
            window.SetForegroundColour(foreground)
    except Exception:
        pass


def _apply_objectlistview_theme(window, palette):
    """Applique le chrome visuel commun aux ObjectListView historiques.

    Aucune colonne, checkbox ni callback métier n'est modifié ici. Les anciennes
    couleurs de lignes et polices de message vide restent donc sans effet dès
    que le thème central est appliqué.
    """
    try:
        if hasattr(window, "oddRowsBackColor"):
            window.oddRowsBackColor = palette["surface_low"]
        if hasattr(window, "evenRowsBackColor"):
            window.evenRowsBackColor = palette["control"]
        if hasattr(window, "groupTextColour"):
            window.groupTextColour = palette["text"]
        if hasattr(window, "groupBackgroundColour"):
            window.groupBackgroundColour = palette["surface_high"]
        group_font = getattr(window, "groupFont", None)
        if group_font is not None and group_font.IsOk():
            group_font.SetWeight(wx.FONTWEIGHT_BOLD)
            window.groupFont = group_font

        empty = getattr(window, "stEmptyListMsg", None)
        if empty is not None:
            _set_colours(empty, background=palette["control"], foreground=palette["text_variant"])
            try:
                base_font = window.GetFont()
                if base_font and base_font.IsOk():
                    empty.SetFont(base_font)
            except Exception:
                pass
        if hasattr(window, "SetEmptyListMsgFont"):
            try:
                base_font = window.GetFont()
                if base_font and base_font.IsOk():
                    window.SetEmptyListMsgFont(base_font)
            except Exception:
                pass
    except Exception:
        pass


def _apply_palette(window, palette, dark):
    background = None
    foreground = None
    input_types = (
        wx.TextCtrl,
        wx.ComboBox,
        wx.Choice,
        wx.ListBox,
        wx.CheckListBox,
        wx.ListCtrl,
        wx.TreeCtrl,
        wx.SpinCtrl,
    )
    if hasattr(wx, "SearchCtrl"):
        input_types = input_types + (wx.SearchCtrl,)

    if isinstance(window, (wx.Frame, wx.Dialog)):
        background = palette["surface"]
        foreground = palette["text"]
    elif isinstance(window, input_types):
        background = palette["control"]
        foreground = palette["text"]
    elif isinstance(window, wx.Panel):
        background = palette["surface"]
        foreground = palette["text"]
    elif isinstance(window, wx.Button):
        foreground = palette["button_text"]
    elif isinstance(window, (wx.StaticText, wx.CheckBox, wx.RadioButton)):
        foreground = palette["text"]
    elif isinstance(window, wx.StaticLine):
        foreground = palette["outline"]

    _set_colours(window, background=background, foreground=foreground)
    _apply_objectlistview_theme(window, palette)

    empty = getattr(window, "stEmptyListMsg", None)
    if empty is not None:
        _set_colours(empty, background=palette["control"], foreground=palette["text_variant"])


def apply_to_window(window, recursive=True, theme=None, scale=None, palette=None):
    if window is None:
        return
    if theme is None or scale is None:
        configured_theme, configured_scale = _config_values()
        theme = configured_theme if theme is None else theme
        scale = configured_scale if scale is None else scale
    dark = is_dark_theme(theme)
    palette = palette or _semantic_palette(dark)

    _scale_font(window, scale)
    _apply_metrics(window, scale)
    _apply_palette(window, palette, dark)

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
                apply_to_window(frame, True)

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
