#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Point d'entrée de Teamworks et coque d'interface moderne.

Le cœur historique reste isolé dans ``Teamworks_core``. Cette coque ne réécrit
pas la logique métier : elle remplace uniquement le livre d'onglets principal
par la navigation flexible et conserve les noms publics attendus par le reste
de l'application.
"""

import os
import sys

import wx

import Chemins
import Teamworks_core as CORE
from Ctrl import CTRL_Accueil
from Ctrl import CTRL_Navigation_principale
from Ctrl import CTRL_Personnes
from Ctrl import CTRL_Presences
from Ctrl import CTRL_Recrutement
from Utils import UTILS_Customize
from Utils import UTILS_Fichiers
from Utils import UTILS_Rapport_bugs
from Utils import UTILS_Qualifications_091g
from Utils.UTILS_Traduction import _


# Correctif de lecture des pièces historiques : installé avant l'ouverture de
# toute fiche individuelle afin qu'une date invalide ne bloque jamais la fiche.
UTILS_Qualifications_091g.install()


VERSION_APPLICATION = CORE.VERSION_APPLICATION
MAIL_AUTEUR = CORE.MAIL_AUTEUR
ADRESSE_FORUM = CORE.ADRESSE_FORUM
ID_DERNIER_FICHIER = CORE.ID_DERNIER_FICHIER


class Toolbook(CTRL_Navigation_principale.NavigationPrincipale):
    """Navigation principale flexible, compatible avec l'API historique."""

    def __init__(self, parent):
        CTRL_Navigation_principale.NavigationPrincipale.__init__(self, parent)
        self.Build_Pages()

    def Build_Pages(self):
        self.img_accueil = CTRL_Navigation_principale.BitmapNavigation(
            Chemins.GetStaticPath("Images/32x32/Maison.png"), 28
        )
        self.img_personnes = CTRL_Navigation_principale.BitmapNavigation(
            Chemins.GetStaticPath("Images/32x32/Personnes.png"), 28
        )
        self.img_presences = CTRL_Navigation_principale.BitmapNavigation(
            Chemins.GetStaticPath("Images/32x32/Horloge.png"), 28
        )
        self.img_recrutement = CTRL_Navigation_principale.BitmapNavigation(
            Chemins.GetStaticPath("Images/32x32/Recrutement.png"), 28
        )

        self.AddPage(
            CTRL_Accueil.Panel(self),
            _(u"Accueil"),
            bitmap=self.img_accueil,
            select=True,
        )
        self.AddPage(
            CTRL_Personnes.PanelPersonnes(self),
            _(u"Individus"),
            bitmap=self.img_personnes,
        )
        self.AddPage(
            CTRL_Presences.PanelPresences(self),
            _(u"Présences"),
            bitmap=self.img_presences,
        )
        self.AddPage(
            CTRL_Recrutement.Panel(self),
            _(u"Recrutement"),
            bitmap=self.img_recrutement,
        )

        self.dict_pages_by_index = {
            "accueil": 0,
            "individus": 1,
            "personnes": 1,
            "presences": 2,
            "recrutement": 3,
        }


# Le cœur historique résout Toolbook au moment où MyFrame est instanciée.
# Cette injection locale garde donc toute la logique existante tout en remplaçant
# réellement le composant de navigation, sans monkey-patcher wxPython.
CORE.Toolbook = Toolbook

MyFrame = CORE.MyFrame
MyApp = CORE.MyApp
SaisiePassword = CORE.SaisiePassword
Redirect = CORE.Redirect


def _detruire_fenetres_smoke(app):
    """Ferme proprement les fenêtres restantes avant la fin d'un smoke wx."""
    if not os.environ.get("TEAMWORKS_SMOKE_MODE"):
        return
    for window in list(wx.GetTopLevelWindows()):
        if window:
            window.Destroy()
    app.ProcessPendingEvents()
    wx.YieldIfNeeded()


def _initialiser_application():
    """Reprend le bootstrap historique en initialisant le cœur partagé."""
    for rep in ("Temp", "Updates", "Sync", "Lang", "Modeles", "Editions"):
        chemin = UTILS_Fichiers.GetRepUtilisateur(rep)
        if not os.path.isdir(chemin):
            os.makedirs(chemin)

    UTILS_Fichiers.DeplaceFichiers()

    customize = UTILS_Customize.Customize()
    CORE.CUSTOMIZE = customize
    globals()["CUSTOMIZE"] = customize

    UTILS_Rapport_bugs.Activer_rapport_erreurs(version=VERSION_APPLICATION)

    nom_journal = UTILS_Fichiers.GetRepUtilisateur(
        customize.GetValeur("journal", "nom", "journal.log")
    )
    if os.path.isfile(nom_journal) and os.path.getsize(nom_journal) > 5000000:
        os.remove(nom_journal)

    nom_fichier = sys.executable
    journal_actif = customize.GetValeur("journal", "actif", "1") != "0"
    if (
        not nom_fichier.endswith("python.exe")
        and journal_actif
        and not os.path.isfile("nolog.txt")
    ):
        sys.stdout = Redirect(nom_journal)

    app = MyApp(redirect=False)
    app.MainLoop()
    _detruire_fenetres_smoke(app)


if __name__ == "__main__":
    _initialiser_application()
