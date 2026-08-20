#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Espace AUI pour les gadgets de la page d'accueil.

Les gadgets restent les contrôles historiques de ``Gadget.py`` mais deviennent
déplaçables, redimensionnables, dockables et flottants. Leur disposition AUI
est mémorisée séparément des données métier des gadgets.
"""

import wx
import wx.aui as aui

import Gadget
from Utils import UTILS_Customize
from Utils import UTILS_Interface


PERSPECTIVE_SECTION = "interface"
PERSPECTIVE_KEY = "gadgets_perspective"


class EspaceGadgets(wx.Panel):
    """Hôte AUI des gadgets de l'accueil."""

    managed_gadgets = True

    def __init__(self, parent, listeGadgets=None):
        wx.Panel.__init__(self, parent, -1, name="espace_gadgets_flottants")
        self.parent = parent
        self.listeGadgets = listeGadgets or []
        self.couleur_fond = self._couleur_tuple(UTILS_Interface.GetToken("surface"))
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.manager = None
        self._gadgets = {}
        self._restauration_en_cours = False

        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

        self.Construire()

    @staticmethod
    def _couleur_tuple(couleur):
        return (couleur.Red(), couleur.Green(), couleur.Blue())

    def _info_pane(self, nom, label, taille, index):
        largeur = max(180, int(taille[0]))
        hauteur = max(140, int(taille[1]))
        decalage = 26 * index
        return (
            aui.AuiPaneInfo()
            .Name(nom)
            .Caption(label)
            .CaptionVisible(False)
            .BestSize((largeur, hauteur))
            .MinSize((160, 110))
            .FloatingSize((largeur, hauteur))
            .FloatingPosition((24 + decalage, 24 + decalage))
            .Float()
            .Floatable(True)
            .Dockable(True)
            .Movable(True)
            .Resizable(True)
            .Gripper(True)
            .GripperTop(True)
            .CloseButton(False)
            .MaximizeButton(False)
        )

    def _DetruirePanes(self):
        for gadget in list(self._gadgets.values()):
            try:
                gadget.Destroy()
            except Exception:
                pass
        self._gadgets = {}

        if self.manager is not None:
            try:
                self.manager.UnInit()
            except Exception:
                pass
            self.manager = None

    def Construire(self):
        """Reconstruit les panes puis restaure leur disposition mémorisée."""
        self.Freeze()
        try:
            self._DetruirePanes()
            self.manager = aui.AuiManager(self)

            for index, (nom, parametres) in enumerate(self.listeGadgets):
                if not parametres.get("affichage", True):
                    continue

                gadget = Gadget.PanelGadget(
                    self,
                    self.couleur_fond,
                    index,
                    size=parametres.get("taille", wx.DefaultSize),
                )
                self._gadgets[nom] = gadget
                info = self._info_pane(
                    nom,
                    parametres.get("label", nom),
                    parametres.get("taille", (220, 180)),
                    index,
                )
                self.manager.AddPane(gadget, info)

            self._RestaurerPerspective()
            self.manager.Update()
        finally:
            self.Thaw()

    def _RestaurerPerspective(self):
        perspective = UTILS_Customize.GetValeur(
            PERSPECTIVE_SECTION,
            PERSPECTIVE_KEY,
            "",
        )
        if not perspective:
            return
        try:
            self._restauration_en_cours = True
            self.manager.LoadPerspective(perspective, update=False)
        except Exception:
            # Une perspective devient invalide si un ancien gadget disparaît :
            # l'accueil doit continuer à s'ouvrir avec la disposition par défaut.
            pass
        finally:
            self._restauration_en_cours = False

    def SauverPerspective(self):
        if self._restauration_en_cours or self.manager is None:
            return
        try:
            perspective = self.manager.SavePerspective()
            UTILS_Customize.SetValeur(
                PERSPECTIVE_SECTION,
                PERSPECTIVE_KEY,
                perspective,
            )
        except Exception:
            pass

    def ReinitialiserDisposition(self):
        """Revient à la disposition flottante initiale."""
        UTILS_Customize.SetValeur(PERSPECTIVE_SECTION, PERSPECTIVE_KEY, "")
        self.Construire()

    def MAJ(self, listeGadgets=None):
        """Recharge les gadgets sans perdre la disposition courante."""
        self.SauverPerspective()
        if listeGadgets is not None:
            self.listeGadgets = listeGadgets
        self.Construire()

    def Fermer_Gadget(self, nomGadgetAFermer):
        """Masque un gadget et conserve son état métier historique."""
        gadget = self._gadgets.get(nomGadgetAFermer)
        if gadget is None:
            return
        try:
            gadget.SaveConfig({"affichage": False})
        except Exception:
            pass
        pane = self.manager.GetPane(nomGadgetAFermer)
        if pane.IsOk():
            pane.Hide()
            self.manager.Update()
        self.SauverPerspective()

    def Ouvre_Gadget(self, nomGadgetAOuvrir):
        """Réaffiche un gadget déjà construit ou reconstruit l'espace."""
        gadget = self._gadgets.get(nomGadgetAOuvrir)
        if gadget is None:
            for nom, parametres in self.listeGadgets:
                if nom == nomGadgetAOuvrir:
                    parametres["affichage"] = True
                    break
            self.Construire()
            return

        try:
            gadget.SaveConfig({"affichage": True})
        except Exception:
            pass
        pane = self.manager.GetPane(nomGadgetAOuvrir)
        if pane.IsOk():
            pane.Show(True)
            self.manager.Update()
        self.SauverPerspective()

    def OnPaneClose(self, event):
        pane = event.GetPane()
        gadget = pane.window
        try:
            gadget.SaveConfig({"affichage": False})
        except Exception:
            pass
        wx.CallAfter(self.SauverPerspective)
        event.Skip()

    def OnDestroy(self, event):
        if event.GetEventObject() is self:
            self.SauverPerspective()
            self._DetruirePanes()
        event.Skip()
