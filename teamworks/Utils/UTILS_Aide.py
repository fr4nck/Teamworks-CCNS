#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Aide utilisateur Teamworks-CCNS.

La documentation courante est publiée avec MkDocs. Les anciens identifiants
d'aide restent acceptés et sont traduits vers les pages modernes lorsqu'une
correspondance fiable existe.
"""

import wx

from Utils.UTILS_Traduction import _


DOCUMENTATION_BASE = "https://fr4nck.github.io/Teamworks-CCNS/"

_PAGE_MAP = {
    "Personnes": "utilisation/individus/",
    "Laficheindividuelle": "utilisation/individus/",
    "Contrats": "utilisation/contrats-ccns-cee/",
    "DPAE": "utilisation/dpae-due/",
    "DUE": "utilisation/dpae-due/",
    "EditeurdEmails": "utilisation/documents/",
    "Publipostage": "utilisation/documents/",
    "Vacances": "administration/parametrage/",
    "Lesgadgets": "administration/parametrage/",
    "Rechercherunemisejourdulogiciel": "demarrage/mise-a-jour/",
}


def GetUrl(page=None):
    """Retourne l'URL de documentation la plus précise connue."""
    suffixe = _PAGE_MAP.get(page, "")
    return DOCUMENTATION_BASE + suffixe


def Aide(page=None):
    """Ouvre la documentation Teamworks-CCNS dans le navigateur par défaut."""
    url = GetUrl(page)
    try:
        ouvert = wx.LaunchDefaultBrowser(url)
    except Exception:
        ouvert = False

    if ouvert is False:
        wx.MessageBox(
            _(
                u"La documentation Teamworks-CCNS n'a pas pu être ouverte "
                u"automatiquement.\n\nAdresse : %s"
            ) % url,
            _(u"Documentation Teamworks-CCNS"),
            wx.OK | wx.ICON_INFORMATION,
        )
    return url


if __name__ == "__main__":
    app = wx.App(0)
    Aide()
