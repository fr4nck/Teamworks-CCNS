#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import wx
import os
from six.moves import configparser
try :
    from Utils import UTILS_Adaptations
    from Utils import UTILS_Theme
except:
    import UTILS_Adaptations
    import UTILS_Theme
UTILS_Fichiers = UTILS_Adaptations.Import("Utils.UTILS_Fichiers")

# Le rendu natif doit être demandé avant la construction des fenêtres.
UTILS_Theme.enable_native_dark_mode()
UTILS_Theme.install_auto_theming()


LISTE_DONNEES = [
    ("interface", [
        # Contrat TW-121 historique : ``theme`` décrit l'apparence.
        # Les nouveaux composants utilisent ``appearance`` et ``accent`` afin
        # de ne plus confondre clair/sombre avec Vert/Bleu/Noir.
        ("theme", "Systeme"),
        ("accent", "Vert"),
        ("appearance", "system"),
        # Nouvelle clé explicite. ``echelle_police`` reste le miroir de
        # compatibilité pour les profils et versions antérieurs.
        ("echelle_interface", "100"),
        ("echelle_police", "100"),
    ]),
    ("branding", [
        ("logo_association", ""),
    ]),
    ("journal", [
        ("actif", "1"),
        ("nom", "journal.log"),
    ]),
    ("repertoire_donnees", [
        ("chemin", ""),
    ]),
]


def GetNomFichier(nomFichier="Customize.ini"):
    return UTILS_Fichiers.GetRepUtilisateur(nomFichier)


class Customize():
    def __init__(self):
        self.nomFichier = GetNomFichier()
        self.cfg = configparser.ConfigParser()
        self.InitFichier()

    def InitFichier(self):
        """Création, vérification et migration légère des préférences."""
        if os.path.isfile(self.nomFichier) :
            self.cfg.read(self.nomFichier)

        dirty = False

        # Migration TW-189 : un profil ayant déjà choisi 120 % doit rester à
        # 120 %. On copie donc l'ancienne valeur avant d'ajouter les défauts.
        if self.cfg.has_section("interface"):
            if (
                not self.cfg.has_option("interface", "echelle_interface")
                and self.cfg.has_option("interface", "echelle_police")
            ):
                self.cfg.set(
                    "interface",
                    "echelle_interface",
                    self.cfg.get("interface", "echelle_police"),
                )
                dirty = True

        for section, valeurs in LISTE_DONNEES :
            if section not in self.cfg.sections() :
                self.cfg.add_section(section)
                dirty = True
            for cle, valeur in valeurs :
                if cle not in self.cfg.options(section) :
                    self.cfg.set(section, cle, valeur)
                    dirty = True
        if dirty :
            self.Enregistrement()

    def GetCfg(self):
        return self.cfg

    def GetValeur(self, section="", cle="", defaut="", type_valeur=str, ajouter_si_manquant=True):
        if self.cfg.has_section(section) and self.cfg.has_option(section, cle) :
            if type_valeur == int :
                return self.cfg.getint(section, cle)
            elif type_valeur == float :
                return self.cfg.getfloat(section, cle)
            elif type_valeur == bool :
                return self.cfg.getboolean(section, cle)
            else :
                return self.cfg.get(section, cle)
        else:
            if ajouter_si_manquant == True :
                if self.cfg.has_section(section) == False :
                    self.cfg.add_section(section)
                self.cfg.set(section, cle, str(defaut))
                self.Enregistrement()
                return defaut
            return None

    def SetValeur(self, section="", cle="", valeur=""):
        if self.cfg.has_section(section) == False :
            self.cfg.add_section(section)
        self.cfg.set(section, cle, str(valeur))

    def Enregistrement(self):
        """ Enregistrement du fichier sur le disque dur """
        with open(self.nomFichier, "w") as fichier:
            self.cfg.write(fichier)


def GetCustomize():
    try :
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
    except :
        nomWindow = None
    if nomWindow == "general" :
        return topWindow.GetCustomize()
    return Customize()


def GetValeur(section="", cle="", defaut="", type_valeur=str, ajouter_si_manquant=True):
    customize = GetCustomize()
    return customize.GetValeur(section, cle, defaut, type_valeur, ajouter_si_manquant)


def SetValeur(section="", cle="", valeur=""):
    customize = GetCustomize()
    customize.SetValeur(section, cle, valeur)
    customize.Enregistrement()


if __name__ == u"__main__":
    print(("GET :", GetValeur("interface", "theme", "Systeme")))
