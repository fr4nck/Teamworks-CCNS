#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os, sys
import sqlite3


_SQLITE_CONNECT_CURRENT = sqlite3.connect
_SQLITE_CONNECT_ORIGINAL = getattr(
    _SQLITE_CONNECT_CURRENT, "_teamworks_original_connect", _SQLITE_CONNECT_CURRENT
)


def _sqlite_connect_text_path(database, *args, **kwargs):
    """Garantit un chemin texte à sqlite3 sous Python 3.

    Quelques appels historiques encodent encore les chemins en UTF-8 avant
    d'ouvrir SQLite. Python 3 accepte nativement les chemins Unicode ; le
    décodage central évite les erreurs sur les répertoires accentués sans
    modifier les URI SQLite, les chemins texte ni les bases en mémoire.
    """
    if isinstance(database, bytes):
        database = database.decode("utf-8")
    return _SQLITE_CONNECT_ORIGINAL(database, *args, **kwargs)


if not getattr(_SQLITE_CONNECT_CURRENT, "_teamworks_text_paths", False):
    _sqlite_connect_text_path._teamworks_text_paths = True
    _sqlite_connect_text_path._teamworks_original_connect = _SQLITE_CONNECT_ORIGINAL
    sqlite3.connect = _sqlite_connect_text_path


frozen = getattr(sys, 'frozen', '')
if not frozen:
    REP_COURANT = os.path.dirname(os.path.abspath(__file__))
else :
    REP_COURANT = os.path.dirname(sys.executable)

if REP_COURANT not in sys.path :
    sys.path.insert(1, REP_COURANT)

for rep in os.listdir(REP_COURANT) :
    chemin = os.path.join(REP_COURANT, rep)
    if os.path.isdir(chemin) and chemin not in sys.path :
        sys.path.insert(2, chemin)

# Diagnostic installé très tôt : un import manquant ou un crash natif survenant
# avant la création de wx.App doit quand même laisser une trace transmissible.
try:
    from Utils import UTILS_Crash
    UTILS_Crash.InstallerHookMinimal()
    UTILS_Crash.ActiverFaulthandler()
except Exception:
    # Le diagnostic ne doit jamais empêcher Teamworks de démarrer.
    pass


def GetStaticPath(fichier=""):
    """Retourne le chemin Static ou l'asset de marque généré au runtime."""
    normalized = str(fichier).replace("\\", "/")
    if normalized in ("Images/Special/Logo_splash.png", "Images/16x16/Logo.png"):
        try:
            # Import volontairement tardif : Chemins est chargé avant le système
            # de préférences, alors que les assets de marque ne sont demandés
            # qu'une fois wx.App initialisé.
            from Utils import UTILS_Branding
            override = UTILS_Branding.GetRuntimeAssetOverride(normalized)
            if override:
                return override
        except Exception:
            pass

    chemin = os.path.join(REP_COURANT, "Static")
    return os.path.join(chemin, fichier)


def GetMainPath(fichier=""):
    """ Retourne le chemin du répertoire principal """
    return os.path.join(REP_COURANT, fichier)
