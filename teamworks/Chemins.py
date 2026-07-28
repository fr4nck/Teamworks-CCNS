#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os, sys
import sqlite3


_SQLITE_CONNECT_ORIGINAL = sqlite3.connect


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


if not getattr(sqlite3.connect, "_teamworks_text_paths", False):
    _sqlite_connect_text_path._teamworks_text_paths = True
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

def GetStaticPath(fichier=""):
    """ Retourne le chemin du répertoire Static """
    chemin = os.path.join(REP_COURANT, "Static")
    return os.path.join(chemin, fichier)

def GetMainPath(fichier=""):
    """ Retourne le chemin du répertoire principal """
    return os.path.join(REP_COURANT, fichier)
