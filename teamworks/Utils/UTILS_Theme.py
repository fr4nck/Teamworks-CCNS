#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Système d'affichage centralisé de Teamworks-CCNS.

Le réglage historique ``echelle_police`` est désormais interprété comme une
échelle d'interface : typographie, icônes, barres d'outils, onglets et hauteur
des contrôles évoluent ensemble. Cela évite le cas classique où un texte à
120 % reste enfermé dans des composants dimensionnés pour 100 %.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from configparser import ConfigParser

import appdirs
import wx

import Chemins

DARK_THEME_NAMES = {"sombre", "dark", "noir"}
LIGHT_THEME_NAMES = {"clair", "light", "blanc"}
SYSTEM_THEME_NAMES = {"systeme", "système", "system", "auto"}
CONFIG_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")

# Grille de densité desktop. Les valeurs sont des DIP de référence à 100 %.
BASE_METRICS = {
    "space_xs": 4,
    "space_s": 8,
    "space_m": 12,
    "space_l": 16,
    "control_height": 28,
    "toolbar_icon": 24,
    "navigation_icon": 32,
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
    # Nouveau nom explicite ; l'ancien reste accepté pour compatibilité.
    env_scale = (
        os.environ.get("TEAMWORKS_UI_SCALE", "").strip()
        or os.environ.get("TEAMWORKS_FONT_SCALE", "").strip()
    )

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
            if not scale:
                if parser.has_option("interface", "echelle_interface"):
                    scale = parser.get("interface", "echelle_interface")
                elif parser.has_option("interface", "echelle_police"):
                    scale = parser.get("interface", "echelle_police")
        except (OSError, ValueError):
            pass

    try:
        interface_scale = max(80, min(200, int(scale or "100")))
    except ValueError:
        interface_scale = 100

    values = (theme or "Systeme", interface_scale)
    # Ne jamais figer les valeurs par défaut tant que le fichier cible n'existe
    # pas : il peut être déplacé juste après par la migration de premier lancement.
    if config_exists and not env_theme and not env_scale:
        _CONFIG_CACHE = values
    return values


def requested_theme():
    return _config_values()[0]


def interface_scale_percent():
    return _config_values()[1]


def font_scale_percent():
    """Alias historique conservé pour les appelants existants."""
    return interface_scale_percent()


def scale_px(value, scale=None, minimum=1):
    """Convertit une métrique de référence en pixels d'interface cohérents."""
    if scale is None:
        scale = interface_scale_percent()
    return max(minimum, int(round(float(value) * scale / 100.0)))


def metrics(scale=None):
    if scale is None:
        scale = interface_scale_percent()
    return {name: scale_px(value, scale=scale) for name, value in BASE_METRICS.items()}


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
    """Construit des rôles de surface cohérents, inspirés Fluent/Material.

    Les couleurs système restent prioritaires pour la sélection et les actions.
    Les autres rôles évitent l'ancien grand aplat gris/bleu sans transformer
    l'application métier en interface mobile.
    """
    selection = _system_colour(wx.SYS_COLOUR_HIGHLIGHT, (0, 120, 215))
    selection_text = _system_colour(wx.SYS_COLOUR_HIGHLIGHTTEXT, (255, 255, 255))

    if dark:
        return {
            "surface": wx.Colour(30, 30, 30),
            "surface_lowest": wx.Colour(25, 25, 25),
            "surface_low": wx.Colour(36, 36, 36),
            "surface_container": wx.Colour(40, 40, 40),
            "surface_high": wx.Colour(46, 46, 46),
            "surface_highest": wx.Colour(52, 52, 52),
            "control": wx.Colour(45, 45, 48),
            "text": wx.Colour(242, 242, 242),
            "text_variant": wx.Colour(200, 200, 200),
            "button_text": wx.Colour(242, 242, 242),
            "selection": selection,
            "selection_text": selection_text,
            "outline": wx.Colour(78, 78, 78),
        }

    system_window = _system_colour(wx.SYS_COLOUR_WINDOW, (255, 255, 255))
    system_text = _system_colour(wx.SYS_COLOUR_WINDOWTEXT, (27, 26, 25))
    if _colour_luminance(system_window) < 128:
        system_window = wx.Colour(255, 255, 255)
    return {
        "surface": wx.Colour(243, 243, 243),
        "surface_lowest": system_window,
        "surface_low": wx.Colour(250, 250, 250),
        "surface_container": wx.Colour(247, 247, 247),
        "surface_high": wx.Colour(238, 238, 238),
        "surface_highest": wx.Colour(229, 229, 229),
        "control": system_window,
        "text": system_text,
        "text_variant": wx.Colour(96, 94, 92),
        "button_text": _system_colour(wx.SYS_COLOUR_BTNTEXT, (27, 26, 25)),
        "selection": selection,
        "selection_text": selection_text,
        "outline": wx.Colour(200, 198, 196),
    }


def _scale_font(window, scale):
    if scale == 100 or getattr(window, "_teamworks_font_scaled", False):
        return
    try:
        font = window.GetFont()
        if font and font.IsOk():
            current = (
                font.GetFractionalPointSize()
                if hasattr(font, "GetFractionalPointSize")
                else font.GetPointSize()
            )
            new_size = max(6.0, current * scale / 100.0)
            if hasattr(font, "SetFractionalPointSize"):
                font.SetFractionalPointSize(new_size)
            else:
                font.SetPointSize(int(round(new_size)))
            window.SetFont(font)
            window._teamworks_font_scaled = True
    except Exception:
        pass


def _resize_bitmap(bitmap, target_size):
    try:
        if not bitmap or not bitmap.IsOk():
            return bitmap
        image = bitmap.ConvertToImage()
        if image.GetWidth() == target_size and image.GetHeight() == target_size:
            return bitmap
        image.Rescale(target_size, target_size, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image)
    except Exception:
        return bitmap


def _scale_toolbook_images(toolbook, scale):
    """Redimensionne réellement les icônes du wx.Toolbook.

    Agrandir uniquement la police ou la hauteur de la toolbar laisse des icônes
    de 32 px minuscules. On reconstruit donc l'ImageList à la bonne échelle en
    conservant exactement les mêmes index de pages.
    """
    if getattr(toolbook, "_teamworks_images_scaled", False):
        return
    try:
        image_list = toolbook.GetImageList()
        if image_list is None:
            return
        target = scale_px(BASE_METRICS["navigation_icon"], scale=scale)
        new_list = wx.ImageList(target, target)
        for index in range(image_list.GetImageCount()):
            new_list.Add(_resize_bitmap(image_list.GetBitmap(index), target))
        toolbook.AssignImageList(new_list)
        toolbook._teamworks_image_list = new_list
        toolbook._teamworks_images_scaled = True
    except Exception:
        pass


def _minimum_height(window, height):
    try:
        minimum = window.GetMinSize()
        current_height = minimum.GetHeight() if minimum else -1
        if current_height < height:
            window.SetMinSize((minimum.GetWidth() if minimum else -1, height))
    except Exception:
        pass


def _apply_metrics(window, scale):
    ui = metrics(scale)

    try:
        if hasattr(window, "InvalidateBestSize"):
            window.InvalidateBestSize()
    except Exception:
        pass

    if isinstance(window, wx.Toolbook):
        _scale_toolbook_images(window, scale)
        try:
            toolbar = window.GetToolBar()
            if toolbar:
                toolbar._teamworks_navigation_toolbar = True
                toolbar.SetWindowStyleFlag(wx.TB_HORZ_TEXT | wx.TB_FLAT | wx.TB_NODIVIDER)
                toolbar.SetToolBitmapSize((ui["navigation_icon"], ui["navigation_icon"]))
                if hasattr(toolbar, "SetToolPacking"):
                    toolbar.SetToolPacking(ui["space_xs"])
                if hasattr(toolbar, "SetMargins"):
                    toolbar.SetMargins(ui["space_s"], ui["space_xs"])
                toolbar.Realize()
                _minimum_height(toolbar, toolbar.GetBestSize().GetHeight())
        except Exception:
            pass

    elif isinstance(window, wx.ToolBar):
        try:
            icon_size = (
                ui["navigation_icon"]
                if getattr(window, "_teamworks_navigation_toolbar", False)
                else ui["toolbar_icon"]
            )
            window.SetToolBitmapSize((icon_size, icon_size))
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

    if isinstance(window, (wx.Button, wx.TextCtrl, wx.ComboBox, wx.Choice, wx.SpinCtrl)):
        _minimum_height(window, ui["control_height"])


def _apply_palette(window, palette, dark):
    background = None
    foreground = palette["text"]

    if isinstance(window, (wx.Frame, wx.Dialog)):
        background = palette["surface"]
    elif isinstance(window, wx.ToolBar):
        background = palette["surface_high"]
    elif isinstance(window, (wx.Toolbook, wx.Notebook)):
        background = palette["surface_container"]
    elif isinstance(window, wx.Panel):
        background = palette["surface_container"]
    elif isinstance(
        window,
        (
            wx.TextCtrl,
            wx.ComboBox,
            wx.Choice,
            wx.ListBox,
            wx.CheckListBox,
            wx.ListCtrl,
            wx.TreeCtrl,
            wx.SpinCtrl,
        ),
    ):
        background = palette["control"]
    elif isinstance(window, wx.Button):
        # Laisser le moteur natif dessiner le bouton ; on ne force que le texte.
        foreground = palette["button_text"]

    try:
        if background is not None:
            window.SetBackgroundColour(background)
        window.SetForegroundColour(foreground)
    except Exception:
        pass


def apply_to_window(window, recursive=True, theme=None, scale=None, palette=None):
    if window is None:
        return

    if theme is None or scale is None:
        configured_theme, configured_scale = _config_values()
        theme = configured_theme if theme is None else theme
        scale = configured_scale if scale is None else scale
    dark = is_dark_theme(theme)
    palette = palette or _native_palette(dark)

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

            frame.Bind(wx.EVT_MENU, open_preferences, item)
            _MENU_INSTALLED = True
            return


def install_auto_theming():
    """Installe le point d'entrée transversal historique du thème.

    Ce hook reste unique et central : aucune retouche locale d'écran n'est
    nécessaire. L'objectif est précisément d'éviter l'empilement de rustines
    tout en conservant la compatibilité avec les centaines de dialogues wx.
    """
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
