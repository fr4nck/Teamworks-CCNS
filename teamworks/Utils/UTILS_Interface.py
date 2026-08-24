#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

"""Fondations visuelles communes de Teamworks.

Ce module est la source centrale des couleurs et des préférences visuelles de
l'interface. Il conserve l'API historique Vert/Bleu/Noir tout en exposant des
rôles sémantiques stables. Les écrans existants peuvent continuer à utiliser
``GetValeur()`` ; les clés historiques de couleur sont désormais des alias vers
les tokens du thème actif.

La charte limite volontairement l'interface à cinq familles visuelles :
neutre, primaire, succès, avertissement et danger. Les variantes de surface,
de contraste, de sélection ou de focus sont des nuances de ces familles, pas
de nouvelles couleurs métier.

Ce module de fondation ne dépend volontairement pas de ``UTILS_Traduction`` :
il est importé très tôt par le moteur de thème et doit rester utilisable pendant
l'initialisation des utilitaires de fichiers/configuration. Les trois libellés
d'accents historiques sont donc stockés directement en français.
"""

import wx

from Utils import UTILS_Customize


THEMES = [
    ("Vert", u"Vert (Par défaut)"),
    ("Bleu", u"Bleu"),
    ("Noir", u"Noir"),
]

APPEARANCE_MODES = ("system", "light", "dark")
COLOUR_FAMILIES = ("neutral", "primary", "success", "warning", "danger")

# Contrat global de mise à l'échelle. Tous les consommateurs (moteur de thème,
# feuille de styles et dialogue de préférences) doivent utiliser ces valeurs.
INTERFACE_SCALE_MIN = 80
INTERFACE_SCALE_DEFAULT = 100
INTERFACE_SCALE_MAX = 200

SEMANTIC_TOKENS = (
    "surface",
    "surface_container_lowest",
    "surface_container_low",
    "surface_container",
    "surface_container_high",
    "surface_container_highest",
    "on_surface",
    "on_surface_variant",
    "primary",
    "on_primary",
    "primary_container",
    "on_primary_container",
    "outline",
    "outline_variant",
    "success",
    "warning",
    "danger",
    "info",
    "selection",
    "selection_text",
    "disabled",
    "focus",
)

TOKEN_FAMILY = {
    "surface": "neutral",
    "surface_container_lowest": "neutral",
    "surface_container_low": "neutral",
    "surface_container": "neutral",
    "surface_container_high": "neutral",
    "surface_container_highest": "neutral",
    "on_surface": "neutral",
    "on_surface_variant": "neutral",
    "outline": "neutral",
    "outline_variant": "neutral",
    "disabled": "neutral",
    "selection_text": "neutral",
    "primary": "primary",
    "on_primary": "primary",
    "primary_container": "primary",
    "on_primary_container": "primary",
    "info": "primary",
    "selection": "primary",
    "focus": "primary",
    "success": "success",
    "warning": "warning",
    "danger": "danger",
}

# Valeurs conservées pour compatibilité et documentation de l'ancien thème.
# ``GetValeur`` ne les renvoie plus directement : les quatre anciennes clés
# passent par LEGACY_TOKEN_MAP pour suivre aussi clair/sombre et les futurs
# thèmes centraux.
DONNEES = {
    "Vert": {
        "couleur_tres_foncee": wx.Colour(33, 104, 0),
        "couleur_claire": wx.Colour(137, 206, 27),
        "couleur_tres_claire": wx.Colour(240, 251, 237),
        "couleur_tres_claire_2": wx.Colour(214, 250, 199),
    },
    "Bleu": {
        "couleur_tres_foncee": wx.Colour(0, 50, 95),
        "couleur_claire": wx.Colour(0, 121, 204),
        "couleur_tres_claire": wx.Colour(234, 240, 255),
        "couleur_tres_claire_2": wx.Colour(211, 224, 250),
    },
    "Noir": {
        "couleur_tres_foncee": wx.Colour(0, 0, 0),
        "couleur_claire": wx.Colour(150, 150, 150),
        "couleur_tres_claire": wx.Colour(240, 240, 240),
        "couleur_tres_claire_2": wx.Colour(230, 230, 230),
    },
}

LEGACY_TOKEN_MAP = {
    "couleur_tres_foncee": "primary",
    "couleur_claire": "primary",
    "couleur_tres_claire": "surface_container_low",
    "couleur_tres_claire_2": "primary_container",
}

_LIGHT_ACCENTS = {
    "Vert": {
        "primary": wx.Colour(45, 112, 35),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(214, 244, 202),
        "on_primary_container": wx.Colour(16, 58, 12),
        "selection": wx.Colour(214, 244, 202),
    },
    "Bleu": {
        "primary": wx.Colour(0, 95, 163),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(211, 232, 255),
        "on_primary_container": wx.Colour(0, 43, 75),
        "selection": wx.Colour(211, 232, 255),
    },
    "Noir": {
        "primary": wx.Colour(74, 74, 74),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(225, 225, 225),
        "on_primary_container": wx.Colour(35, 35, 35),
        "selection": wx.Colour(225, 225, 225),
    },
}

_DARK_ACCENTS = {
    "Vert": {
        "primary": wx.Colour(139, 207, 116),
        "on_primary": wx.Colour(18, 57, 14),
        "primary_container": wx.Colour(42, 84, 34),
        "on_primary_container": wx.Colour(218, 246, 207),
        "selection": wx.Colour(55, 91, 47),
    },
    "Bleu": {
        "primary": wx.Colour(119, 184, 232),
        "on_primary": wx.Colour(0, 50, 84),
        "primary_container": wx.Colour(24, 70, 102),
        "on_primary_container": wx.Colour(216, 235, 250),
        "selection": wx.Colour(31, 73, 103),
    },
    "Noir": {
        "primary": wx.Colour(196, 196, 196),
        "on_primary": wx.Colour(40, 40, 40),
        "primary_container": wx.Colour(70, 70, 70),
        "on_primary_container": wx.Colour(238, 238, 238),
        "selection": wx.Colour(74, 74, 74),
    },
}

_LEGACY_APPEARANCE_NAMES = {
    "system": "Systeme",
    "light": "Clair",
    "dark": "Sombre",
}


def _normalise_theme(theme):
    return theme if theme in DONNEES else "Vert"


def _normalise_appearance(appearance):
    if appearance in APPEARANCE_MODES:
        return appearance
    return "light"


def GetTheme():
    """Retourne l'accent visuel Vert/Bleu/Noir."""
    accent = UTILS_Customize.GetValeur(
        "interface", "accent", "", ajouter_si_manquant=False
    )
    if accent in DONNEES:
        return accent
    legacy = UTILS_Customize.GetValeur("interface", "theme", "Vert")
    return _normalise_theme(legacy)


def SetTheme(theme="Vert"):
    UTILS_Customize.SetValeur("interface", "accent", _normalise_theme(theme))


def GetAppearanceMode():
    return _normalise_appearance(
        UTILS_Customize.GetValeur("interface", "appearance", "light")
    )


def SetAppearanceMode(appearance="system"):
    appearance = _normalise_appearance(appearance)
    UTILS_Customize.SetValeur("interface", "appearance", appearance)
    UTILS_Customize.SetValeur(
        "interface", "theme", _LEGACY_APPEARANCE_NAMES[appearance]
    )


def IsSystemDark():
    try:
        get_appearance = getattr(wx.SystemSettings, "GetAppearance", None)
        if get_appearance is None:
            return False
        appearance = get_appearance()
        is_dark = getattr(appearance, "IsDark", None)
        return bool(is_dark and is_dark())
    except Exception:
        return False


def ResolveAppearance(appearance=None):
    appearance = _normalise_appearance(
        GetAppearanceMode() if appearance is None else appearance
    )
    if appearance == "system":
        return "dark" if IsSystemDark() else "light"
    return appearance


def _build_light_palette(theme):
    accent = _LIGHT_ACCENTS[_normalise_theme(theme)]
    return {
        "surface": wx.Colour(248, 249, 250),
        "surface_container_lowest": wx.Colour(255, 255, 255),
        "surface_container_low": wx.Colour(244, 246, 248),
        "surface_container": wx.Colour(238, 241, 244),
        "surface_container_high": wx.Colour(231, 235, 239),
        "surface_container_highest": wx.Colour(223, 228, 233),
        "on_surface": wx.Colour(31, 31, 31),
        "on_surface_variant": wx.Colour(92, 92, 92),
        "primary": accent["primary"],
        "on_primary": accent["on_primary"],
        "primary_container": accent["primary_container"],
        "on_primary_container": accent["on_primary_container"],
        "outline": wx.Colour(118, 118, 118),
        "outline_variant": wx.Colour(205, 205, 205),
        "success": wx.Colour(38, 122, 54),
        "warning": wx.Colour(153, 93, 0),
        "danger": wx.Colour(186, 26, 26),
        "info": accent["primary"],
        "selection": accent["selection"],
        "selection_text": wx.Colour(25, 25, 25),
        "disabled": wx.Colour(160, 160, 160),
        "focus": accent["primary"],
    }


def _build_dark_palette(theme):
    accent = _DARK_ACCENTS[_normalise_theme(theme)]
    return {
        "surface": wx.Colour(28, 30, 32),
        "surface_container_lowest": wx.Colour(22, 24, 26),
        "surface_container_low": wx.Colour(34, 36, 39),
        "surface_container": wx.Colour(40, 43, 46),
        "surface_container_high": wx.Colour(47, 50, 54),
        "surface_container_highest": wx.Colour(55, 58, 62),
        "on_surface": wx.Colour(232, 232, 232),
        "on_surface_variant": wx.Colour(190, 190, 190),
        "primary": accent["primary"],
        "on_primary": accent["on_primary"],
        "primary_container": accent["primary_container"],
        "on_primary_container": accent["on_primary_container"],
        "outline": wx.Colour(145, 145, 145),
        "outline_variant": wx.Colour(83, 86, 90),
        "success": wx.Colour(111, 190, 121),
        "warning": wx.Colour(224, 174, 87),
        "danger": wx.Colour(238, 122, 122),
        "info": accent["primary"],
        "selection": accent["selection"],
        "selection_text": wx.Colour(245, 245, 245),
        "disabled": wx.Colour(113, 113, 113),
        "focus": accent["primary"],
    }


def GetPalette(theme=None, appearance=None):
    theme = GetTheme() if theme is None else _normalise_theme(theme)
    appearance = ResolveAppearance(appearance)
    if appearance == "dark":
        return _build_dark_palette(theme)
    return _build_light_palette(theme)


def GetToken(token, default=None, theme=None, appearance=None):
    palette = GetPalette(theme=theme, appearance=appearance)
    return palette.get(token, default)


def GetTokenFamily(token):
    return TOKEN_FAMILY.get(token)


def GetValeur(cle="", defaut="", theme=None):
    """API historique raccordée au design system central.

    Les quatre anciennes clés de couleur sont résolues en tokens sémantiques.
    Elles suivent donc désormais l'accent, le mode clair/sombre et tout futur
    thème défini dans ce module, sans modification des écrans appelants.
    """
    theme = GetTheme() if theme is None else _normalise_theme(theme)

    legacy_token = LEGACY_TOKEN_MAP.get(cle)
    if legacy_token:
        return GetToken(legacy_token, default=defaut, theme=theme)

    if cle in SEMANTIC_TOKENS:
        return GetToken(cle, default=defaut, theme=theme)

    return defaut


if __name__ == "__main__":
    print(GetValeur("couleur_tres_foncee", wx.Colour(255, 0, 0)))
