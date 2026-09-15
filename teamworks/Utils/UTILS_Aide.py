#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Aide utilisateur Teamworks-CCNS.

L'ancien mécanisme d'aide Teamworks demandait une licence puis redirigeait vers
un service web historique. Ce parcours commercial n'appartient plus à
Teamworks-CCNS. Les boutons d'aide restent fonctionnels mais n'ouvrent plus de
fenêtre de financement ni d'URL historique.
"""

import wx

from Utils.UTILS_Traduction import _


def Aide(page=None):
    """Informe proprement sur l'aide courante, sans sollicitation commerciale."""
    message = _(
        u"L'aide en ligne historique de Teamworks n'est plus utilisée par "
        u"Teamworks-CCNS.\n\n"
        u"Aucun achat ni licence supplémentaire n'est nécessaire pour utiliser "
        u"le logiciel. La documentation Teamworks-CCNS est en cours de "
        u"centralisation dans le projet."
    )
    if page not in (None, ""):
        message += _(u"\n\nRubrique demandée : %s") % page
    dlg = wx.MessageDialog(
        None,
        message,
        _(u"Aide Teamworks-CCNS"),
        wx.OK | wx.ICON_INFORMATION,
    )
    try:
        dlg.ShowModal()
    finally:
        dlg.Destroy()


if __name__ == "__main__":
    app = wx.App(0)
    Aide()
    app.MainLoop()
