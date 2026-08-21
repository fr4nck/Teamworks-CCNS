#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Feuille de styles sémantique de Teamworks.

L'objectif est volontairement proche du Web : les écrans expriment un rôle
(h1, h2, body, caption...) et non une police/taille/couleur locale. Toute
évolution visuelle peut ainsi être appliquée depuis un point unique.
"""

import wx

from Utils import UTILS_Customize
from Utils import UTILS_Interface


TEXT_STYLES = {
    "h1": {
        "scale": 1.55,
        "min_points": 15,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 16,
        "space_after": 8,
    },
    "h2": {
        "scale": 1.30,
        "min_points": 13,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 14,
        "space_after": 6,
    },
    "h3": {
        "scale": 1.12,
        "min_points": 11,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface",
        "space_before": 10,
        "space_after": 4,
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
    "label": {
        "scale": 0.95,
        "min_points": 9,
        "weight": wx.FONTWEIGHT_BOLD,
        "colour": "on_surface_variant",
        "space_before": 0,
        "space_after": 2,
    },
    "caption": {
        "scale": 0.88,
        "min_points": 8,
        "weight": wx.FONTWEIGHT_NORMAL,
        "colour": "on_surface_variant",
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
