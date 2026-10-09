#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Conserve la locale native pendant toute la vie de l'application wx."""

import wx


def GetLocaleFrancais():
    """Partage une locale française sans la recréer à chaque fenêtre.

    wx.Locale modifie un état natif global. Des locales détenues par des
    dialogues peuvent être détruites dans un ordre différent de leur création,
    laissant les contrôles suivants utiliser une locale native déjà libérée.
    """
    app = wx.GetApp()
    if app is None:
        raise RuntimeError("La locale nécessite une application wx active")
    locale = getattr(app, "_teamworks_locale_fr", None)
    if locale is None:
        locale = wx.Locale(wx.LANGUAGE_FRENCH)
        app._teamworks_locale_fr = locale
    return locale
