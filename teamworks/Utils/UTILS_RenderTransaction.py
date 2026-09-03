#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transaction de rendu centralisée pour les surfaces wx de Teamworks-CCNS.

Ce module est un correctif de stabilisation 0.9.1x, volontairement sans règle
métier. Il conserve le moteur de thème existant mais impose une seule phase de
mise en page et de peinture après l'application récursive des styles.

Sous Windows, les fenêtres de haut niveau sont gelées et double-bufferisées
pendant cette préparation. Un ``Show(False)`` / ``Hide`` ne réapplique jamais le
thème : cela évite notamment le flash clair/sombre observé à la fermeture.
"""

from __future__ import annotations

import sys

import wx

from Utils import UTILS_Theme


_INSTALLED = False
_ORIGINAL_SHOW = None
_ORIGINAL_SHOW_MODAL = None


def _show_requested(args, kwargs):
    """Retourne False pour ``Show(False)`` sans dépendre de la signature wx."""
    if "show" in kwargs:
        return bool(kwargs["show"])
    if args:
        return bool(args[0])
    return True


def _is_top_level(window):
    try:
        return isinstance(window, wx.TopLevelWindow)
    except AttributeError:
        return isinstance(window, (wx.Frame, wx.Dialog))


def _prepare_windows_surface(window):
    """Active le double buffering seulement sur les vraies surfaces Windows."""
    if sys.platform != "win32" or not _is_top_level(window):
        return
    try:
        window.SetDoubleBuffered(True)
    except Exception:
        pass


def _freeze_surface(window):
    """Gèle une surface de haut niveau sans perturber un Freeze déjà actif."""
    if not _is_top_level(window):
        return False
    try:
        if window.IsFrozen():
            return False
    except Exception:
        pass
    try:
        window.Freeze()
        return True
    except Exception:
        return False


def _thaw_surface(window, frozen_here):
    if not frozen_here:
        return
    try:
        window.Thaw()
    except Exception:
        pass


def _apply_node(window, recursive, theme, scale, palette, dark):
    """Applique thème/métriques sans déclencher Layout/Refresh intermédiaires."""
    UTILS_Theme._scale_font(window, scale)
    UTILS_Theme._apply_metrics(window, scale)
    UTILS_Theme._apply_palette(window, palette, dark)
    UTILS_Theme._apply_screen_specific_fixes(window)

    refresh_visual = getattr(window, "RafraichirVisuel", None)
    if callable(refresh_visual):
        try:
            refresh_visual()
        except Exception:
            pass

    if not recursive:
        return
    try:
        children = list(window.GetChildren())
    except Exception:
        children = []
    for child in children:
        _apply_node(child, True, theme, scale, palette, dark)


def apply_to_window(window, recursive=True, theme=None, scale=None, palette=None):
    """Applique l'apparence comme une transaction de rendu atomique.

    Contrairement à l'ancien parcours récursif, les enfants ne font jamais leur
    propre ``Layout``/``Refresh``. La surface racine est stabilisée une fois,
    après que tous les contrôles ont reçu thème, police, métriques et bitmaps.
    """
    if window is None:
        return

    if theme is None or scale is None:
        configured_theme, configured_scale = UTILS_Theme._config_values()
        theme = configured_theme if theme is None else theme
        scale = configured_scale if scale is None else scale

    dark = UTILS_Theme.is_dark_theme(theme)
    palette = palette or UTILS_Theme._semantic_palette(dark)

    _prepare_windows_surface(window)
    frozen_here = _freeze_surface(window)
    try:
        _apply_node(window, recursive, theme, scale, palette, dark)
        try:
            window.Layout()
        except Exception:
            pass

        # Une fenêtre encore cachée n'a rien à repeindre : son premier paint
        # utilisera directement l'état final. Pour une mutation visible, une
        # seule invalidation de la racine suffit.
        try:
            if window.IsShownOnScreen():
                window.Refresh(False)
        except Exception:
            pass
    finally:
        _thaw_surface(window, frozen_here)


def install():
    """Installe le cycle de rendu avant toute création d'écran Teamworks.

    On remplace volontairement le patch ``install_auto_theming`` historique au
    même point global (Show / ShowModal), afin de ne pas multiplier les hooks.
    """
    global _INSTALLED, _ORIGINAL_SHOW, _ORIGINAL_SHOW_MODAL
    if _INSTALLED:
        return
    _INSTALLED = True

    # Le mode natif doit être décidé avant la création des contrôles afin que
    # Windows ne commence pas par leur attribuer des pinceaux clairs.
    UTILS_Theme.enable_native_dark_mode()

    _ORIGINAL_SHOW = wx.Window.Show
    _ORIGINAL_SHOW_MODAL = wx.Dialog.ShowModal

    def themed_show(window, *args, **kwargs):
        # Ne surtout pas rethémer pendant Hide/Show(False) : c'était la cause
        # du flash de couleur visible juste avant la fermeture.
        if not _show_requested(args, kwargs):
            return _ORIGINAL_SHOW(window, *args, **kwargs)

        UTILS_Theme.enable_native_dark_mode()
        UTILS_Theme._install_preferences_menu(window)
        apply_to_window(window, True)
        return _ORIGINAL_SHOW(window, *args, **kwargs)

    def themed_show_modal(dialog, *args, **kwargs):
        UTILS_Theme.enable_native_dark_mode()
        apply_to_window(dialog, True)
        return _ORIGINAL_SHOW_MODAL(dialog, *args, **kwargs)

    wx.Window.Show = themed_show
    wx.Dialog.ShowModal = themed_show_modal

    # Tout appel explicite au moteur de thème utilise désormais le même contrat
    # atomique. Empêche l'ancien installateur de poser un second monkey-patch.
    UTILS_Theme.apply_to_window = apply_to_window
    UTILS_Theme._PATCHED = True
