#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Point d'entrée de Teamworks-CCNS et coque d'interface wx.

Le cœur historique reste isolé dans ``Teamworks_core``. Cette coque fournit la
navigation actuelle, l'identité de version Teamworks-CCNS et retire du parcours
utilisateur les sollicitations commerciales historiques.
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
from Utils import UTILS_Version
from Utils.UTILS_Traduction import _


# Correctif de lecture des pièces historiques : installé avant l'ouverture de
# toute fiche individuelle afin qu'une date invalide ne bloque jamais la fiche.
UTILS_Qualifications_091g.install()


def _lire_version_teamworks_ccns():
    """Lit la version distribuée depuis le fichier VERSION canonique.

    En développement, VERSION est à la racine du dépôt. Dans le paquet
    PyInstaller, il est copié à côté de l'exécutable.
    """
    candidats = (
        Chemins.GetMainPath("VERSION"),
        os.path.abspath(os.path.join(Chemins.GetMainPath(""), os.pardir, "VERSION")),
    )
    for chemin in candidats:
        try:
            with open(chemin, "r", encoding="utf-8") as fichier:
                version = fichier.readline().strip()
            if version:
                return version
        except (OSError, UnicodeError):
            continue
    raise RuntimeError("VERSION Teamworks-CCNS introuvable")


VERSION_APPLICATION = _lire_version_teamworks_ccns()
MAIL_AUTEUR = ""
ADRESSE_FORUM = ""
ID_DERNIER_FICHIER = CORE.ID_DERNIER_FICHIER

# Le cœur historique consomme encore cette constante dans les journaux, les
# nouveaux fichiers et certains dialogues. On lui fournit donc la même source
# canonique au lieu de Versions.txt / v2.13.1.
CORE.VERSION_APPLICATION = VERSION_APPLICATION
CORE.MAIL_AUTEUR = MAIL_AUTEUR
CORE.ADRESSE_FORUM = ADRESSE_FORUM


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
CORE.Toolbook = Toolbook


class MyFrame(CORE.MyFrame):
    """Fenêtre Teamworks-CCNS avec identité et menus actuels."""

    _LIBELLES_HISTORIQUES_A_RETIRER = {
        u"Soutenir Teamworks",
        u"Acheter une licence pour accéder au manuel de référence",
        u"Accéder au forum d'entraide",
        u"Visionner des tutoriels vidéos",
    }

    def ConvertVersionTuple(self, texteVersion=""):
        """Normalise les versions CCNS tout en gardant la comparaison historique."""
        return UTILS_Version.ConvertirTuple(texteVersion)

    def AnnonceFinancement(self):
        """Désactive les sollicitations commerciales automatiques historiques."""
        return False

    def SetTitleFrame(self, nomFichier=""):
        if "[RESEAU]" in nomFichier:
            _port, _hote, user, _mdp = nomFichier.split(";")
            nom_affiche = nomFichier[nomFichier.index("[RESEAU]") + 8:]
            nomFichier = _(u"Fichier réseau : %s | Utilisateur : %s") % (
                nom_affiche,
                user,
            )
        if nomFichier:
            nomFichier = " - [" + nomFichier + "]"
        self.SetTitle("Teamworks CCNS %s%s" % (VERSION_APPLICATION, nomFichier))

    @classmethod
    def _nettoyer_menu(cls, menu):
        """Retire les entrées commerciales/obsolètes du menu wx réel."""
        for item in list(menu.GetMenuItems()):
            sous_menu = item.GetSubMenu()
            if sous_menu is not None:
                cls._nettoyer_menu(sous_menu)
            if item.IsSeparator():
                continue
            libelle = item.GetItemLabelText()
            if libelle in cls._LIBELLES_HISTORIQUES_A_RETIRER:
                menu.Delete(item)

    def CreationBarreMenus(self):
        super(MyFrame, self).CreationBarreMenus()
        barre = self.GetMenuBar()
        if barre is None:
            return
        for index in range(barre.GetMenuCount()):
            self._nettoyer_menu(barre.GetMenu(index))


CORE.MyFrame = MyFrame
MyApp = CORE.MyApp
SaisiePassword = CORE.SaisiePassword


class Redirect(CORE.Redirect):
    """Redirection stdout compatible avec le protocole des flux Python."""

    def flush(self):
        if not self.filename.closed:
            self.filename.flush()


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
