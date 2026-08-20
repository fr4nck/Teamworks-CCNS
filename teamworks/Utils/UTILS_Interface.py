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

Ce module conserve l'API historique des thèmes Vert/Bleu/Noir tout en ajoutant
une couche de rôles sémantiques destinée à la migration progressive de
l'interface. Les écrans existants peuvent continuer à utiliser GetValeur() ;
les composants modernisés doivent préférer GetToken().
"""

import Chemins
from Utils.UTILS_Traduction import _
import wx
from Utils import UTILS_Customize


THEMES = [
    ("Vert", _(u"Vert (Par défaut)")),
    ("Bleu", _(u"Bleu")),
    ("Noir", _(u"Noir")),
]

APPEARANCE_MODES = (
    "system",
    "light",
    "dark",
)

# Noms stables à utiliser dans les nouveaux composants. La hiérarchie des
# surfaces et les couleurs d'état suivent le design system commun du projet.
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


# Palette historique : ne pas modifier les valeurs sans migration explicite.
DONNEES = {

    "Vert" : {
        "couleur_tres_foncee" : wx.Colour(33, 104, 0), # Fond Astuces page d'accueil
        "couleur_claire" : wx.Colour(137, 206, 27), # Texte du splash screen
        "couleur_tres_claire" : wx.Colour(240, 251, 237), # Lignes des listes
        "couleur_tres_claire_2" : wx.Colour(214, 250, 199), # Cadre Contacts de la fiche famille
    },

    "Bleu" : {
        "couleur_tres_foncee" : wx.Colour(0, 50, 95),
        "couleur_claire" : wx.Colour(0, 121, 204),
        "couleur_tres_claire" : wx.Colour(234, 240, 255),
        "couleur_tres_claire_2" : wx.Colour(211, 224, 250),
    },

    "Noir" : {
        "couleur_tres_foncee" : wx.Colour(0, 0, 0),
        "couleur_claire" : wx.Colour(150, 150, 150),
        "couleur_tres_claire" : wx.Colour(240, 240, 240),
        "couleur_tres_claire_2" : wx.Colour(230, 230, 230),
    },

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


def _normalise_theme(theme):
    if theme in DONNEES:
        return theme
    return "Vert"


def _normalise_appearance(appearance):
    if appearance in APPEARANCE_MODES:
        return appearance
    # Tant que tous les écrans historiques ne sont pas migrés, rester en clair
    # évite une interface hybride sur les machines configurées en sombre.
    return "light"


def GetTheme():
    return _normalise_theme(UTILS_Customize.GetValeur("interface", "theme", "Vert"))


def SetTheme(theme="Vert"):
    UTILS_Customize.SetValeur("interface", "theme", _normalise_theme(theme))


def GetAppearanceMode():
    """Retourne la préférence enregistrée : system, light ou dark.

    Le mode clair reste la valeur par défaut de migration afin de préserver le
    rendu historique tant que tous les écrans ne consomment pas encore les
    tokens sémantiques. Les modes system et dark restent disponibles
    explicitement.
    """
    return _normalise_appearance(
        UTILS_Customize.GetValeur("interface", "appearance", "light")
    )


def SetAppearanceMode(appearance="system"):
    """Enregistre la préférence d'apparence sans modifier le thème métier."""
    UTILS_Customize.SetValeur(
        "interface",
        "appearance",
        _normalise_appearance(appearance),
    )


def IsSystemDark():
    """Détecte le mode sombre de la plateforme lorsque wx le permet.

    La détection est volontairement défensive afin de rester compatible avec
    les plateformes/versions de wx qui ne fournissent pas GetAppearance().
    """
    try:
        get_appearance = getattr(wx.SystemSettings, "GetAppearance", None)
        if get_appearance is None:
            return False
        appearance = get_appearance()
        is_dark = getattr(appearance, "IsDark", None)
        if is_dark is None:
            return False
        return bool(is_dark())
    except Exception:
        return False


def ResolveAppearance(appearance=None):
    """Résout system en light/dark et garantit une valeur utilisable."""
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
        "info": wx.Colour(0, 95, 163),
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
        "info": wx.Colour(119, 184, 232),
        "selection": accent["selection"],
        "selection_text": wx.Colour(245, 245, 245),
        "disabled": wx.Colour(113, 113, 113),
        "focus": accent["primary"],
    }


def GetPalette(theme=None, appearance=None):
    """Retourne une palette sémantique complète pour le contexte demandé."""
    theme = GetTheme() if theme is None else _normalise_theme(theme)
    appearance = ResolveAppearance(appearance)
    if appearance == "dark":
        return _build_dark_palette(theme)
    return _build_light_palette(theme)


def GetToken(token, default=None, theme=None, appearance=None):
    """Retourne une couleur à partir de son rôle sémantique."""
    palette = GetPalette(theme=theme, appearance=appearance)
    return palette.get(token, default)


def GetValeur(cle="", defaut="", theme=None):
    """API historique, étendue pour accepter également les tokens sémantiques."""
    theme = GetTheme() if theme is None else _normalise_theme(theme)

    if cle in DONNEES[theme]:
        return DONNEES[theme][cle]

    if cle in SEMANTIC_TOKENS:
        return GetToken(cle, default=defaut, theme=theme)

    return defaut


if __name__ == '__main__':
    print((GetValeur("couleur_tres_foncee", wx.Colour(255, 0, 0))))
