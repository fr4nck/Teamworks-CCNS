#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Espace AUI pour les gadgets de la page d'accueil."""

import wx
import wx.aui as aui

import Gadget
from Utils import UTILS_Customize, UTILS_Interface, UTILS_Styles


PERSPECTIVE_SECTION = "interface"
PERSPECTIVE_KEY = "gadgets_dashboard_perspective_v3"


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
        self._timer_perspective = None
        self._timers_visibilite = {}

        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

        self.Construire()

    @staticmethod
    def _couleur_tuple(couleur):
        return (couleur.Red(), couleur.Green(), couleur.Blue())

    def _token_tuple(self, token):
        return self._couleur_tuple(UTILS_Interface.GetToken(token))

    def _AppliquerThemeManager(self):
        """Raccorde le fond et les séparateurs AUI à la palette centrale."""
        surface = UTILS_Interface.GetToken("surface")
        self.couleur_fond = self._couleur_tuple(surface)
        self.SetBackgroundColour(surface)
        if self.manager is None:
            return
        art = self.manager.GetArtProvider()
        couleurs = (
            (aui.AUI_DOCKART_BACKGROUND_COLOUR, "surface"),
            (aui.AUI_DOCKART_SASH_COLOUR, "surface_container_high"),
            (aui.AUI_DOCKART_BORDER_COLOUR, "outline_variant"),
            (aui.AUI_DOCKART_GRIPPER_COLOUR, "outline"),
        )
        for identifiant, token in couleurs:
            art.SetColour(identifiant, UTILS_Interface.GetToken(token))

    def AppliquerThemeGadget(self, gadget):
        appliquer = getattr(gadget, "AppliquerTheme", None)
        if appliquer is not None:
            try:
                appliquer()
                return
            except Exception:
                pass

        gadget.couleurFondDC = self._token_tuple("surface")
        gadget.couleurFondTitre = self._token_tuple("surface_container_highest")
        gadget.couleurBord = self._token_tuple("outline_variant")
        gadget.couleurDegrade = self._token_tuple("surface_container_high")
        gadget.couleurTexteTitre = self._token_tuple("on_surface")
        try:
            gadget.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
            gadget.Refresh()
        except Exception:
            pass

    def _taille_persisted_or_default(self, taille):
        if taille in (None, wx.DefaultSize):
            return UTILS_Styles.GetGadgetMetric("default_size")
        try:
            largeur, hauteur = int(taille[0]), int(taille[1])
        except Exception:
            return UTILS_Styles.GetGadgetMetric("default_size")
        min_width, min_height = UTILS_Styles.GetGadgetMetric("min_size")
        return max(min_width, largeur), max(min_height, hauteur)

    def _info_pane(self, nom, label, taille, index):
        largeur, hauteur = self._taille_persisted_or_default(taille)
        min_size = UTILS_Styles.GetGadgetMetric("min_size")
        colonnes = UTILS_Styles.GetGadgetMetric("columns")
        return (
            aui.AuiPaneInfo()
            .Name(nom)
            .Caption(label)
            .CaptionVisible(False)
            .BestSize((largeur, hauteur))
            .MinSize(min_size)
            .Top()
            .Layer(0)
            .Row(index // colonnes)
            .Position(index % colonnes)
            # Un gadget appartient au dashboard. Interdire le détachement AUI
            # évite une fenêtre flottante qui survivrait au masquage de l'accueil.
            .Floatable(False)
            .Dockable(True)
            .Movable(True)
            .Resizable(True)
            .Gripper(True)
            .GripperTop(True)
            .CloseButton(False)
            .MaximizeButton(False)
        )

    def _CreerGadget(self, nom, parametres, index):
        taille = parametres.get("taille")
        gadget = Gadget.PanelGadget(
            self,
            self.couleur_fond,
            index,
            size=self._taille_persisted_or_default(taille),
        )
        self.AppliquerThemeGadget(gadget)
        self._gadgets[nom] = gadget
        self.manager.AddPane(
            gadget,
            self._info_pane(nom, parametres.get("label", nom), taille, index),
        )
        return gadget

    def _SupprimerGadget(self, nom):
        gadget = self._gadgets.pop(nom, None)
        if gadget is None or self.manager is None:
            return
        try:
            self.manager.DetachPane(gadget)
        except Exception:
            pass
        try:
            gadget.Destroy()
        except Exception:
            pass

    def _DetruirePanes(self):
        if self.manager is not None:
            for nom in list(self._gadgets):
                self._SupprimerGadget(nom)
            try:
                self.manager.UnInit()
            except Exception:
                pass
            self.manager = None
        self._gadgets = {}

    def Construire(self):
        self.Freeze()
        try:
            self._DetruirePanes()
            self.manager = aui.AuiManager(self)
            self._AppliquerThemeManager()
            for index, (nom, parametres) in enumerate(self.listeGadgets):
                if parametres.get("affichage", True):
                    self._CreerGadget(nom, parametres, index)
            self._RestaurerPerspective()
            self.manager.Update()
        finally:
            self.Thaw()

    def _RestaurerPerspective(self):
        perspective = UTILS_Customize.GetValeur(PERSPECTIVE_SECTION, PERSPECTIVE_KEY, "")
        if not perspective:
            return
        try:
            self._restauration_en_cours = True
            self.manager.LoadPerspective(perspective, update=False)
            self._AncrerDansDashboard()
        except Exception:
            pass
        finally:
            self._restauration_en_cours = False

    def _AncrerDansDashboard(self):
        """Réaffirme la frontière dashboard après toute restauration AUI."""
        if self.manager is None:
            return
        colonnes = UTILS_Styles.GetGadgetMetric("columns")
        for index, nom in enumerate(self._gadgets):
            pane = self.manager.GetPane(nom)
            if pane.IsOk():
                pane.Dock().Top().Layer(0).Row(index // colonnes).Position(index % colonnes)
                pane.Floatable(False).Show(True)

    def SauverPerspective(self):
        if self._restauration_en_cours or self.manager is None:
            return
        try:
            UTILS_Customize.SetValeur(PERSPECTIVE_SECTION, PERSPECTIVE_KEY, self.manager.SavePerspective())
        except Exception:
            pass

    def PlanifierSauvegardePerspective(self, delai=150):
        try:
            if self._timer_perspective is not None and self._timer_perspective.IsRunning():
                self._timer_perspective.Stop()
        except Exception:
            pass
        self._timer_perspective = wx.CallLater(delai, self.SauverPerspective)

    def _PersisterVisibilite(self, nom, affichage):
        self._timers_visibilite.pop(nom, None)
        gadget = self._gadgets.get(nom)
        if gadget is None:
            return
        try:
            gadget.SaveConfig({"affichage": affichage})
        except Exception:
            pass

    def PlanifierVisibilite(self, nom, affichage, delai=80):
        gadget = self._gadgets.get(nom)
        if gadget is None:
            return
        gadget.paramGadget["affichage"] = affichage
        try:
            self.listeGadgets[gadget.index][1]["affichage"] = affichage
        except Exception:
            pass

        ancien = self._timers_visibilite.pop(nom, None)
        try:
            if ancien is not None and ancien.IsRunning():
                ancien.Stop()
        except Exception:
            pass
        self._timers_visibilite[nom] = wx.CallLater(delai, self._PersisterVisibilite, nom, affichage)

    def ReinitialiserDisposition(self):
        UTILS_Customize.SetValeur(PERSPECTIVE_SECTION, PERSPECTIVE_KEY, "")
        self.Construire()

    def ToutAncrer(self):
        if self.manager is None:
            return
        self._AncrerDansDashboard()
        self.manager.Update()
        self.PlanifierSauvegardePerspective()

    def OnContextMenu(self, event):
        menu = wx.Menu()
        id_ancrer = wx.NewIdRef()
        id_reset = wx.NewIdRef()
        menu.Append(id_ancrer, u"Rétablir la disposition du dashboard")
        menu.AppendSeparator()
        menu.Append(id_reset, u"Réinitialiser la disposition")
        self.Bind(wx.EVT_MENU, lambda evt: self.ToutAncrer(), id=id_ancrer)
        self.Bind(wx.EVT_MENU, lambda evt: self.ReinitialiserDisposition(), id=id_reset)
        self.PopupMenu(menu)
        menu.Destroy()

    def MAJ(self, listeGadgets=None):
        if listeGadgets is not None:
            self.listeGadgets = listeGadgets
        if self.manager is None:
            self.Construire()
            return

        visibles = {
            nom: (index, parametres)
            for index, (nom, parametres) in enumerate(self.listeGadgets)
            if parametres.get("affichage", True)
        }
        existants = set(self._gadgets)
        souhaites = set(visibles)

        self.Freeze()
        try:
            self._AppliquerThemeManager()
            for nom in existants - souhaites:
                self._SupprimerGadget(nom)
            for nom in souhaites - existants:
                index, parametres = visibles[nom]
                self._CreerGadget(nom, parametres, index)
            for nom in souhaites & existants:
                index, parametres = visibles[nom]
                pane = self.manager.GetPane(nom)
                if not pane.IsOk():
                    continue
                pane.Caption(parametres.get("label", nom))
                largeur, hauteur = self._taille_persisted_or_default(parametres.get("taille"))
                pane.BestSize((largeur, hauteur))
                pane.Show(True)
                self.AppliquerThemeGadget(self._gadgets[nom])
            self.manager.Update()
        finally:
            self.Thaw()
        self.PlanifierSauvegardePerspective()

    def Fermer_Gadget(self, nomGadgetAFermer):
        gadget = self._gadgets.get(nomGadgetAFermer)
        if gadget is None or self.manager is None:
            return
        pane = self.manager.GetPane(nomGadgetAFermer)
        if pane.IsOk():
            pane.Hide()
            self.manager.Update()
        self.PlanifierVisibilite(nomGadgetAFermer, False)
        self.PlanifierSauvegardePerspective()

    def Ouvre_Gadget(self, nomGadgetAOuvrir):
        gadget = self._gadgets.get(nomGadgetAOuvrir)
        if gadget is None:
            for index, (nom, parametres) in enumerate(self.listeGadgets):
                if nom != nomGadgetAOuvrir:
                    continue
                parametres["affichage"] = True
                self._CreerGadget(nom, parametres, index)
                self.manager.Update()
                self.PlanifierVisibilite(nom, True)
                self.PlanifierSauvegardePerspective()
                return
            return
        pane = self.manager.GetPane(nomGadgetAOuvrir)
        if pane.IsOk():
            pane.Show(True)
            self.manager.Update()
        self.PlanifierVisibilite(nomGadgetAOuvrir, True)
        self.PlanifierSauvegardePerspective()

    def OnPaneClose(self, event):
        pane = event.GetPane()
        gadget = pane.window
        nom = getattr(gadget, "nomGadget", "")
        if nom:
            self.PlanifierVisibilite(nom, False)
            self.PlanifierSauvegardePerspective()
        event.Skip()

    def OnDestroy(self, event):
        if event.GetEventObject() is self:
            try:
                if self._timer_perspective is not None and self._timer_perspective.IsRunning():
                    self._timer_perspective.Stop()
            except Exception:
                pass
            self.SauverPerspective()
            self._DetruirePanes()
        event.Skip()
