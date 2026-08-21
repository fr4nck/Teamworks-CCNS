#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Feuille de styles sémantique de Teamworks.

L'objectif est volontairement proche du Web : les écrans expriment un rôle
(display, h1..h6, body, caption...) et non une police/taille/couleur locale.
Toute évolution visuelle peut ainsi être appliquée depuis un point unique.
"""

import wx

from Utils import UTILS_Customize
from Utils import UTILS_Interface


# La gamme couvre volontairement les tailles historiques rencontrées dans
# Teamworks (environ 7 à 16 pt) sans conserver leurs valeurs en dur dans les
# écrans. Les rôles indiquent l'intention ; GetFont() les adapte ensuite à la
# police native et à l'échelle d'interface.
TEXT_STYLES = {
    "display": {
        "scale": 1.85,
        "min_points": 18,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 20,
        "space_after": 10,
    },
    "h1": {
        "scale": 1.60,
        "min_points": 16,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 16,
        "space_after": 8,
    },
    "h2": {
        "scale": 1.40,
        "min_points": 14,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 14,
        "space_after": 7,
    },
    "h3": {
        "scale": 1.22,
        "min_points": 12,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 12,
        "space_after": 6,
    },
    "h4": {
        "scale": 1.12,
        "min_points": 11,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 10,
        "space_after": 5,
    },
    "h5": {
        "scale": 1.05,
        "min_points": 10,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 8,
        "space_after": 4,
    },
    "h6": {
        "scale": 1.00,
        "min_points": 9,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface_variant",
        "space_before": 6,
        "space_after": 3,
    },
    "lead": {
        "scale": 1.12,
        "min_points": 11,
        "weight": wx.FONTWEIGHT_NORMAL,
        "colour": "on_surface",
        "space_before": 0,
        "space_after": 8,
    },
    "body-large": {
        "scale": 1.06,
        "min_points": 10,
        "weight": wx.FONTWEIGHT_NORMAL,
        "colour": "on_surface",
        "space_before": 0,
        "space_after": 5,
    },
    "body": {
        "scale": 1.00,
        "min_points": 9,
        "weight": wx.FONTWEIGHT_NORMAL,
        "colour": "on_surface",
        "space_before": 0,
        "space_after": 4,
    },
    "body-secondary": {
        "scale": 1.00,
        "min_points": 9,
        "weight": wx.FONTWEIGHT_NORMAL,
        "colour": "on_surface_variant",
        "space_before": 0,
        "space_after": 4,
    },
    "body-small": {
        "scale": 0.90,
        "min_points": 8,
        "weight": wx.FONTWEIGHT_NORMAL,
        "colour": "on_surface",
        "space_before": 0,
        "space_after": 3,
    },
    "label": {
        "scale": 0.95,
        "min_points": 9,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface_variant",
        "space_before": 0,
        "space_after": 2,
    },
    "caption": {
        "scale": 0.86,
        "min_points": 8,
        "weight": wx.FONTWEIGHT_NORMAL,
        "colour": "on_surface_variant",
        "space_before": 0,
        "space_after": 2,
    },
    "micro": {
        "scale": 0.78,
        "min_points": 7,
        "weight": wx.FONTWEIGHT_NORMAL,
        "colour": "on_surface_variant",
        "space_before": 0,
        "space_after": 1,
    },
    "data-large": {
        "scale": 1.22,
        "min_points": 12,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 0,
        "space_after": 2,
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
