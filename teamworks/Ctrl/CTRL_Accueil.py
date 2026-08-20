#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import ast
import wx

from Utils.UTILS_Traduction import _
from Ctrl import CTRL_Gadgets_flottants
import GestionDB
from Utils import UTILS_Config
from Utils import UTILS_Fichiers
from Utils import UTILS_Interface


LISTEGADGETSDEFAUT = [
    ["dossiers_incomplets", {
        "label": _(u"Dossiers incomplets"),
        "taille": (200, 200),
        "affichage": True,
        "config": False,
    }],
    ["horloge", {
        "label": _(u"Horloge"),
        "taille": (200, 200),
        "affichage": True,
        "config": True,
        "couleur_face": (214, 223, 247),
    }],
    ["calendrier", {
        "label": _(u"Calendrier"),
        "taille": (200, 200),
        "affichage": True,
        "config": True,
    }],
    ["updater", {
        "label": _(u"Mises à jour internet"),
        "taille": (200, 200),
        "affichage": True,
        "config": False,
    }],
    ["notes", {
        "label": _(u"Bloc-notes"),
        "taille": (200, 200),
        "affichage": True,
        "config": True,
        "texte": _(u"Hello !"),
        "taillePolice": 10,
        "familyPolice": 74,
        "stylePolice": 90,
        "weightPolice": 90,
        "nomPolice": "Segoe Print",
    }],
]


def _literal(valeur, defaut=None):
    if valeur in (None, ""):
        return defaut
    try:
        return ast.literal_eval(valeur)
    except (ValueError, SyntaxError, TypeError):
        return defaut


def ImportListeGadgets():
    """Récupère les gadgets persistés sans exécuter de contenu arbitraire."""
    DB = GestionDB.DB()
    DB.ExecuterReq("SELECT * FROM gadgets ORDER BY ordre;")
    listeGadgetsTmp = DB.ResultatReq()
    DB.Close()

    listeGadgets = []
    for IDgadget, nom, label, description, taille, affichage, ordre, config, parametres in listeGadgetsTmp:
        dictTmp = {
            "nom": nom,
            "label": label,
            "taille": _literal(taille, (200, 200)),
            "affichage": bool(_literal(affichage, True)),
            "ordre": ordre,
            "config": bool(_literal(config, False)),
        }
        dictTmpParam = _literal(parametres, {})
        if isinstance(dictTmpParam, dict):
            dictTmp.update(dictTmpParam)
        listeGadgets.append([nom, dictTmp])
    return listeGadgets


def MajTableGadgets(nomGadget="", parametres=None):
    """Enregistre directement les paramètres d'un gadget."""
    if parametres is None:
        parametres = {}

    listeDonnees = []
    dictParametres = {}
    for key, valeur in parametres.items():
        if key == "label":
            listeDonnees.append(("label", valeur))
        elif key == "taille":
            listeDonnees.append(("taille", str(valeur)))
        elif key == "affichage":
            listeDonnees.append(("affichage", str(valeur)))
        elif key == "ordre":
            listeDonnees.append(("ordre", valeur))
        elif key == "config":
            listeDonnees.append(("config", str(valeur)))
        else:
            dictParametres[key] = valeur

    if dictParametres:
        listeDonnees.append(("parametres", str(dictParametres)))

    DB = GestionDB.DB()
    DB.ReqMAJ("gadgets", listeDonnees, "nom", nomGadget, IDestChaine=True)
    DB.Close()


class MyHtmlWindow(CTRL_Gadgets_flottants.EspaceGadgets):
    """Nom historique conservé temporairement pour l'API de la fenêtre principale."""

    def __init__(self, parent, id, listeGadgets):
        CTRL_Gadgets_flottants.EspaceGadgets.__init__(self, parent, listeGadgets)

    def Efface(self):
        if self.manager is None:
            return
        for nom in list(self._gadgets):
            pane = self.manager.GetPane(nom)
            if pane.IsOk():
                pane.Hide()
        self.manager.Update()

    def Source(self):
        return ""

    def ConvertitCouleur(self, couleur):
        return "#%02X%02X%02X" % couleur


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(
            self,
            parent,
            -1,
            name="panel_accueil",
            style=wx.NO_FULL_REPAINT_ON_RESIZE,
        )
        couleur_surface = UTILS_Interface.GetToken("surface")
        self.couleur_fond = (
            couleur_surface.Red(),
            couleur_surface.Green(),
            couleur_surface.Blue(),
        )
        self.SetBackgroundColour(couleur_surface)

        self.listeGadgets = self.GetListeGadgets()
        self.html = MyHtmlWindow(self, -1, self.listeGadgets)

        # Le dashboard possède toute la surface de travail. L'ancienne bande
        # blanche/logo n'avait aucune fonction métier et réduisait l'espace utile.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.html, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def MAJ_Gadgets(self):
        # EspaceGadgets.MAJ gère lui-même son cycle Freeze/Thaw. Ne pas geler
        # une seconde fois toute la page : cela amplifiait les blocages visuels.
        self.listeGadgets = self.GetListeGadgets()
        self.html.MAJ(self.listeGadgets)

    def MAJpanel(self, listeElements=None):
        if listeElements is None:
            listeElements = []
        if "exemple" in listeElements or listeElements == []:
            self.MAJ_Gadgets()

    def GetListeGadgets(self):
        listeGadgets = ImportListeGadgets()

        affichage_updater = bool(self.GetGrandParent().MAJexiste)
        for nom, parametres in listeGadgets:
            if nom == "updater":
                parametres["affichage"] = affichage_updater
        return listeGadgets


class AffichageGadgets(object):
    """Boîte de dialogue historique de sélection des gadgets."""

    def __init__(self, parent):
        self.listeGadgets = ImportListeGadgets()

    def dialogue(self):
        listeNoms = []
        preSelection = []
        for index, (nomGadget, parametres) in enumerate(self.listeGadgets):
            listeNoms.append(parametres["label"])
            if parametres["affichage"] is True:
                preSelection.append(index)

        message = _(u"Sélectionnez les gadgets que vous souhaitez afficher sur votre page d'accueil")
        dlg = wx.MultiChoiceDialog(
            None,
            message,
            _(u"Affichage des gadgets"),
            listeNoms,
            wx.CHOICEDLG_STYLE,
        )
        dlg.SetSelections(preSelection)

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return False

        resultats = set(dlg.GetSelections())
        dlg.Destroy()
        for index in range(len(self.listeGadgets)):
            self.listeGadgets[index][1]["affichage"] = index in resultats

        try:
            topWindow = wx.GetApp().GetTopWindow()
            nomWindow = topWindow.GetName()
        except Exception:
            nomWindow = None

        if nomWindow == "general":
            topWindow.userConfig["listeGadgets"] = self.listeGadgets
        else:
            cfg = UTILS_Config.FichierConfig(
                nomFichier=UTILS_Fichiers.GetRepUtilisateur("Config.dat")
            )
            cfg.SetItemConfig("listeGadgets", self.listeGadgets)
        return True


class MyFrame(wx.Frame):
    """Frame de test."""

    def __init__(self, parent):
        wx.Frame.__init__(
            self,
            parent,
            -1,
            title="",
            name="frm_accueil",
            style=wx.DEFAULT_FRAME_STYLE,
        )
        self.parent = parent
        self.panel = Panel(self)


if __name__ == "__main__":
    app = wx.App(0)
    frame_1 = MyFrame(None)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
