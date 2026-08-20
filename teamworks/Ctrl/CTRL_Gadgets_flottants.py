#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Espace AUI pour les gadgets de la page d'accueil."""

import wx
import wx.aui as aui

import Gadget
from Utils import UTILS_Customize
from Utils import UTILS_Interface


PERSPECTIVE_SECTION = "interface"
PERSPECTIVE_KEY = "gadgets_perspective_v2"


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

    def AppliquerThemeGadget(self, gadget):
        """Applique le thème via l'API du composant quand elle existe."""
        appliquer = getattr(gadget, "AppliquerTheme", None)
        if appliquer is not None:
            try:
                appliquer()
                return
            except Exception:
                pass

        # Compatibilité pour un éventuel gadget externe encore ancien.
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

    def _info_pane(self, nom, label, taille, index):
        """Crée un pane visible, tuilé, redimensionnable et détachable."""
        largeur = max(200, int(taille[0]))
        hauteur = max(150, int(taille[1]))
        return (
            aui.AuiPaneInfo()
            .Name(nom)
            .Caption(label)
            .CaptionVisible(False)
            .BestSize((largeur, hauteur))
            .MinSize((180, 120))
            .FloatingSize((largeur, hauteur))
            .Top()
            .Layer(0)
            .Row(index // 3)
            .Position(index % 3)
            .Floatable(True)
            .Dockable(True)
            .Movable(True)
            .Resizable(True)
            .Gripper(True)
            .GripperTop(True)
            .CloseButton(False)
            .MaximizeButton(False)
        )

    def _CreerGadget(self, nom, parametres, index):
        gadget = Gadget.PanelGadget(
            self,
            self.couleur_fond,
            index,
            size=parametres.get("taille", wx.DefaultSize),
        )
        self.AppliquerThemeGadget(gadget)
        self._gadgets[nom] = gadget
        self.manager.AddPane(
            gadget,
            self._info_pane(
                nom,
                parametres.get("label", nom),
                parametres.get("taille", (220, 180)),
                index,
            ),
        )
        return gadget

    def _SupprimerGadget(self, nom):
        """Retire un seul pane sans reconstruire le dashboard complet."""
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
        """Construit le dashboard initial puis restaure sa perspective."""
        self.Freeze()
        try:
            self._DetruirePanes()
            self.manager = aui.AuiManager(self)

            for index, (nom, parametres) in enumerate(self.listeGadgets):
                if parametres.get("affichage", True):
                    self._CreerGadget(nom, parametres, index)

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
            pass
        finally:
            self._restauration_en_cours = False

    def SauverPerspective(self):
        if self._restauration_en_cours or self.manager is None:
            return
        try:
            UTILS_Customize.SetValeur(
                PERSPECTIVE_SECTION,
                PERSPECTIVE_KEY,
                self.manager.SavePerspective(),
            )
        except Exception:
            pass

    def PlanifierSauvegardePerspective(self, delai=150):
        """Regroupe les mouvements AUI en une seule écriture disque."""
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
        """Persiste après le repaint pour ne pas bloquer l'événement souris."""
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
        self._timers_visibilite[nom] = wx.CallLater(
            delai,
            self._PersisterVisibilite,
            nom,
            affichage,
        )

    def ReinitialiserDisposition(self):
        UTILS_Customize.SetValeur(PERSPECTIVE_SECTION, PERSPECTIVE_KEY, "")
        self.Construire()

    def ToutRendreFlottant(self):
        if self.manager is None:
            return
        for index, (nom, gadget) in enumerate(self._gadgets.items()):
            pane = self.manager.GetPane(nom)
            if not pane.IsOk():
                continue
            largeur, hauteur = gadget.GetSize()
            pane.Float()
            pane.FloatingPosition((48 + (32 * index), 72 + (32 * index)))
            pane.FloatingSize((max(200, largeur), max(150, hauteur)))
        self.manager.Update()
        self.PlanifierSauvegardePerspective()

    def ToutAncrer(self):
        if self.manager is None:
            return
        for index, nom in enumerate(self._gadgets):
            pane = self.manager.GetPane(nom)
            if pane.IsOk():
                pane.Dock().Top().Layer(0).Row(index // 3).Position(index % 3).Show(True)
        self.manager.Update()
        self.PlanifierSauvegardePerspective()

    def OnContextMenu(self, event):
        menu = wx.Menu()
        id_flottants = wx.NewIdRef()
        id_ancrer = wx.NewIdRef()
        id_reset = wx.NewIdRef()
        menu.Append(id_flottants, u"Tout rendre flottant")
        menu.Append(id_ancrer, u"Tout ancrer dans l'accueil")
        menu.AppendSeparator()
        menu.Append(id_reset, u"Réinitialiser la disposition")
        self.Bind(wx.EVT_MENU, lambda evt: self.ToutRendreFlottant(), id=id_flottants)
        self.Bind(wx.EVT_MENU, lambda evt: self.ToutAncrer(), id=id_ancrer)
        self.Bind(wx.EVT_MENU, lambda evt: self.ReinitialiserDisposition(), id=id_reset)
        self.PopupMenu(menu)
        menu.Destroy()

    def MAJ(self, listeGadgets=None):
        """Applique uniquement les différences de visibilité/configuration."""
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
                taille = parametres.get("taille", (220, 180))
                pane.BestSize((max(200, int(taille[0])), max(150, int(taille[1]))))
                pane.Show(True)
                self.AppliquerThemeGadget(self._gadgets[nom])

            self.manager.Update()
        finally:
            self.Thaw()
        self.PlanifierSauvegardePerspective()

    def Fermer_Gadget(self, nomGadgetAFermer):
        """Masque immédiatement un gadget puis persiste son état en différé."""
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
                gadget = self._CreerGadget(nom, parametres, index)
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
