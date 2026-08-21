#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Feuille de styles sémantique de Teamworks.

L'objectif est volontairement proche du Web : les écrans expriment un rôle
(display, h1..h6, body, caption...), un espacement, une icône, un contrôle ou
un profil de fenêtre, jamais une taille locale arbitraire. Toute évolution
visuelle peut ainsi être appliquée depuis un point unique.
"""

import wx

from Utils import UTILS_Customize
from Utils import UTILS_Interface


TEXT_STYLES = {
    "display": {"scale": 1.85, "min_points": 18, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface", "space_before": 20, "space_after": 10},
    "h1": {"scale": 1.60, "min_points": 16, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface", "space_before": 16, "space_after": 8},
    "h2": {"scale": 1.40, "min_points": 14, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface", "space_before": 14, "space_after": 7},
    "h3": {"scale": 1.22, "min_points": 12, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface", "space_before": 12, "space_after": 6},
    "h4": {"scale": 1.12, "min_points": 11, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface", "space_before": 10, "space_after": 5},
    "h5": {"scale": 1.05, "min_points": 10, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface", "space_before": 8, "space_after": 4},
    "h6": {"scale": 1.00, "min_points": 9, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface_variant", "space_before": 6, "space_after": 3},
    "lead": {"scale": 1.12, "min_points": 11, "weight": wx.FONTWEIGHT_NORMAL, "colour": "on_surface", "space_before": 0, "space_after": 8},
    "body-large": {"scale": 1.06, "min_points": 10, "weight": wx.FONTWEIGHT_NORMAL, "colour": "on_surface", "space_before": 0, "space_after": 5},
    "body": {"scale": 1.00, "min_points": 9, "weight": wx.FONTWEIGHT_NORMAL, "colour": "on_surface", "space_before": 0, "space_after": 4},
    "body-secondary": {"scale": 1.00, "min_points": 9, "weight": wx.FONTWEIGHT_NORMAL, "colour": "on_surface_variant", "space_before": 0, "space_after": 4},
    "body-small": {"scale": 0.90, "min_points": 8, "weight": wx.FONTWEIGHT_NORMAL, "colour": "on_surface", "space_before": 0, "space_after": 3},
    "label": {"scale": 0.95, "min_points": 9, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface_variant", "space_before": 0, "space_after": 2},
    "caption": {"scale": 0.86, "min_points": 8, "weight": wx.FONTWEIGHT_NORMAL, "colour": "on_surface_variant", "space_before": 0, "space_after": 2},
    "micro": {"scale": 0.78, "min_points": 7, "weight": wx.FONTWEIGHT_NORMAL, "colour": "on_surface_variant", "space_before": 0, "space_after": 1},
    "data-large": {"scale": 1.22, "min_points": 12, "weight": wx.FONTWEIGHT_BOLD, "colour": "on_surface", "space_before": 0, "space_after": 2},
}

SPACING = {
    "none": 0,
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
}

LAYOUT_SPACING = {
    "control_gap": "xs",
    "field_gap": "sm",
    "section_gap": "lg",
    "content_padding": "lg",
    "dialog_padding": "lg",
    "toolbar_gap": "sm",
    "page_gap": "xl",
}

ICON_SIZES = {
    "micro": 12,
    "small": 16,
    "medium": 20,
    "large": 24,
    "hero": 32,
}

CONTROL_METRICS = {
    "button_min_height": 36,
    "button_icon_margin": 4,
    "input_min_height": 32,
    "toolbar_min_height": 40,
    "footer_min_height": 28,
    "footer_text_padding": 10,
}

WINDOW_PROFILES = {
    "compact": {
        "width_ratio": 0.38,
        "height_ratio": 0.44,
        "min_size": (420, 320),
        "max_size": (760, 640),
    },
    "standard": {
        "width_ratio": 0.56,
        "height_ratio": 0.64,
        "min_size": (640, 480),
        "max_size": (1120, 880),
    },
    "wide": {
        "width_ratio": 0.72,
        "height_ratio": 0.72,
        "min_size": (820, 560),
        "max_size": (1520, 1040),
    },
    "workspace": {
        "width_ratio": 0.84,
        "height_ratio": 0.84,
        "min_size": (960, 640),
        "max_size": (1900, 1240),
    },
}


def GetEchelleInterface():
    """Retourne l'échelle UI en %, avec compatibilité de la clé historique."""
    try:
        valeur = UTILS_Customize.GetValeur(
            "interface", "echelle_interface", "", type_valeur=int,
            ajouter_si_manquant=False,
        )
        if valeur:
            return max(80, min(200, int(valeur)))
    except Exception:
        pass
    try:
        valeur = UTILS_Customize.GetValeur(
            "interface", "echelle_police", "100", type_valeur=int
        )
        return max(80, min(200, int(valeur)))
    except Exception:
        return 100


def Scale(value, minimum=1):
    """Équivalent d'une unité CSS adaptée au zoom de l'interface."""
    return max(minimum, int(round(value * GetEchelleInterface() / 100.0)))


def GetSpacing(name="sm"):
    """Retourne un espacement de la gamme centrale, mis à l'échelle."""
    return Scale(SPACING.get(name, SPACING["sm"]), minimum=0)


def GetLayoutSpacing(role="field_gap"):
    """Retourne l'espacement associé à un rôle de layout."""
    return GetSpacing(LAYOUT_SPACING.get(role, "sm"))


def GetIconSize(role="medium"):
    """Retourne une taille carrée d'icône issue de la charte."""
    value = Scale(ICON_SIZES.get(role, ICON_SIZES["medium"]))
    return value, value


def GetControlMetric(role="button_min_height"):
    """Retourne une métrique de contrôle native mise à l'échelle."""
    return Scale(CONTROL_METRICS.get(role, CONTROL_METRICS["button_min_height"]))


def GetWindowSize(profile="standard", display_size=None):
    """Calcule une taille de fenêtre durable à partir d'un profil sémantique."""
    definition = WINDOW_PROFILES.get(profile, WINDOW_PROFILES["standard"])
    if display_size is None:
        try:
            display_size = wx.GetDisplaySize()
        except Exception:
            display_size = (1280, 800)

    width = int(round(display_size[0] * definition["width_ratio"]))
    height = int(round(display_size[1] * definition["height_ratio"]))
    min_width, min_height = definition["min_size"]
    max_width, max_height = definition["max_size"]
    width = max(Scale(min_width), min(Scale(max_width), width))
    height = max(Scale(min_height), min(Scale(max_height), height))
    return width, height


def ApplyWindowProfile(window, profile="standard", centre=True):
    """Applique un profil de dimension à une fenêtre wx redimensionnable."""
    size = GetWindowSize(profile)
    window.SetSize(size)
    definition = WINDOW_PROFILES.get(profile, WINDOW_PROFILES["standard"])
    window.SetMinSize(tuple(Scale(value) for value in definition["min_size"]))
    if centre:
        try:
            window.CentreOnParent()
        except Exception:
            window.CentreOnScreen()
    return size


def GetTextStyle(style="body"):
    """Retourne une copie de la définition d'un style texte sémantique."""
    return dict(TEXT_STYLES.get(style, TEXT_STYLES["body"]))


def GetFont(style="body"):
    definition = GetTextStyle(style)
    font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    base_points = max(1, font.GetPointSize())
    points = max(
        definition["min_points"],
        int(round(base_points * definition["scale"])),
    )
    points = max(1, int(round(points * GetEchelleInterface() / 100.0)))
    font.SetPointSize(points)
    font.SetWeight(definition["weight"])
    return font


def AppliquerTexte(controle, style="body"):
    """Applique à un contrôle wx son rôle typographique, façon classe CSS."""
    definition = GetTextStyle(style)
    controle.SetFont(GetFont(style))
    controle.SetForegroundColour(UTILS_Interface.GetToken(definition["colour"]))
    return controle


def GetTextSpacing(style="body"):
    """Retourne (avant, après) pour harmoniser le rythme vertical."""
    definition = GetTextStyle(style)
    return (
        Scale(definition["space_before"], minimum=0),
        Scale(definition["space_after"], minimum=0),
    )
