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
from Utils.UTILS_Traduction import _


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


_BaseMyFrame = CORE.MyFrame


class MyFrame(_BaseMyFrame):
    """Coque principale enrichie de points d'entrée modernes et isolés."""

    def CreationBarreMenus(self):
        _BaseMyFrame.CreationBarreMenus(self)

        # CRH-10B reste injecté depuis la coque moderne afin d'éviter de modifier
        # le très gros cœur historique pour un unique point d'entrée satellite.
        menu_parametrage = self.dictInfosMenu["menu_parametrage"]["ctrl"]
        menu_parametrage.AppendSeparator()
        item_id = wx.Window.NewControlId()
        item = wx.MenuItem(
            menu_parametrage,
            item_id,
            _(u"Organismes && connexions RH"),
            _(u"Configurer les organismes, références et portails RH de la structure"),
        )
        item.SetBitmap(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Utilisateur_reseau.png"),
                wx.BITMAP_TYPE_PNG,
            )
        )
        menu_parametrage.Append(item)
        self.Bind(wx.EVT_MENU, self.On_param_connexions_rh, id=item_id)
        self.dictInfosMenu["connexions_rh"] = {"id": item_id, "ctrl": item}

    def On_param_connexions_rh(self, event):
        """Ouvre le paramétrage CRH-10B uniquement sur demande explicite."""
        if self.userConfig.get("nomFichier", "") == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord ouvrir un fichier Teamworks."),
                _(u"Organismes & connexions RH"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        try:
            from Dlg import DLG_Organismes_connexions_rh

            dlg = DLG_Organismes_connexions_rh.Dialog(self)
        except Exception as exc:
            wx.MessageBox(
                _(u"Le paramétrage des connexions RH est momentanément indisponible.\n\n%s")
                % str(exc),
                _(u"Organismes & connexions RH"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()


# ``MyApp.OnInit`` résout ``MyFrame`` dans le module Teamworks_core au moment de
# l'exécution. On remplace donc ce point de composition, comme pour Toolbook,
# sans modifier la classe wxPython elle-même ni dupliquer le bootstrap historique.
CORE.MyFrame = MyFrame

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
