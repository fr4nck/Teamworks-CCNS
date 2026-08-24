#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Écran Présences de Teamworks.

Composition moderne : calendrier, légende et sélection des personnes sont des
composants distincts qui partagent la charte graphique et ne dépendent plus
d'un arbre de parents ou de splitters historique.
"""

import wx

from Ctrl import CTRL_Planning
from Ctrl import CTRL_Presences_calendrier
from Ctrl import CTRL_Presences_legende
from Ctrl import CTRL_Presences_personnes
from Ctrl import CTRL_Section
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


# API historique réexportée pour les imports existants.
PanelCalendrier = CTRL_Presences_calendrier.PanelCalendrier
CTRL_Annee = CTRL_Presences_calendrier.CTRL_Annee
ListCtrl_Legendes = CTRL_Presences_legende.ListCtrl_Legendes
PanelLegendes = CTRL_Presences_legende.PanelLegendes
listCtrl_Personnes = CTRL_Presences_personnes.listCtrl_Personnes
BarreRecherche = CTRL_Presences_personnes.BarreRecherche
PanelPersonnes = CTRL_Presences_personnes.PanelPersonnes


selectionPersonnes = []
selectionDates = []


class PanelPresences(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(
            self,
            parent,
            ID,
            name="panel_presences",
            style=wx.TAB_TRAVERSAL,
        )
        self.init = False
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

    def InitPage(self):
        self.splitterV = wx.SplitterWindow(
            self,
            -1,
            style=wx.SP_LIVE_UPDATE,
        )
        self.splitterV.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.splitterV.SetMinimumPaneSize(UTILS_Styles.Scale(220))
        self.splitterV.SetSashGravity(0.24)

        self.sidebar = wx.Panel(self.splitterV, -1, style=wx.TAB_TRAVERSAL)
        self.sidebar.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_low")
        )
        self.panelPlanning = CTRL_Planning.PanelPlanning(self.splitterV, -1)

        self.sectionCalendrier = CTRL_Section.Section(
            self.sidebar,
            titre=_(u"Calendrier"),
            niveau=3,
        )
        contenu_calendrier = self.sectionCalendrier.GetContentPanel()
        self.panelCalendrier = PanelCalendrier(contenu_calendrier, -1)
        sizer_calendrier = wx.BoxSizer(wx.VERTICAL)
        sizer_calendrier.Add(self.panelCalendrier, 1, wx.EXPAND)
        contenu_calendrier.SetSizer(sizer_calendrier)

        self.sectionLegendes = CTRL_Section.Section(
            self.sidebar,
            titre=_(u"Légende"),
            niveau=3,
        )
        contenu_legendes = self.sectionLegendes.GetContentPanel()
        self.panelLegendes = PanelLegendes(contenu_legendes, -1)
        sizer_legendes = wx.BoxSizer(wx.VERTICAL)
        sizer_legendes.Add(self.panelLegendes, 1, wx.EXPAND)
        contenu_legendes.SetSizer(sizer_legendes)

        self.sectionPersonnes = CTRL_Section.Section(
            self.sidebar,
            titre=_(u"Individus"),
            niveau=3,
        )
        contenu_personnes = self.sectionPersonnes.GetContentPanel()
        self.panelPersonnes = PanelPersonnes(contenu_personnes, -1)
        sizer_personnes = wx.BoxSizer(wx.VERTICAL)
        sizer_personnes.Add(self.panelPersonnes, 1, wx.EXPAND)
        contenu_personnes.SetSizer(sizer_personnes)

        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        sidebar_sizer = wx.BoxSizer(wx.VERTICAL)
        sidebar_sizer.Add(
            self.sectionCalendrier,
            3,
            wx.EXPAND | wx.ALL,
            padding,
        )
        sidebar_sizer.Add(
            self.sectionLegendes,
            2,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            padding,
        )
        sidebar_sizer.Add(
            self.sectionPersonnes,
            4,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            padding,
        )
        self.sidebar.SetSizer(sidebar_sizer)

        self.splitterV.SplitVertically(
            self.sidebar,
            self.panelPlanning,
            UTILS_Styles.Scale(330),
        )
        self.__do_layout()
        self.init = True
        self.panelCalendrier.MAJselectionDates(listeDates=selectionDates)
        wx.CallAfter(self._ajuster_splitter_initial)

    def _ajuster_splitter_initial(self):
        if not self.splitterV.IsSplit():
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return
        cible = max(
            UTILS_Styles.Scale(280),
            min(UTILS_Styles.Scale(460), int(largeur * 0.24)),
        )
        self.splitterV.SetSashPosition(cible)

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.splitterV, 1, wx.EXPAND)
        self.SetSizer(sizer_base)
        self.Layout()

    def SetSelectionDates(self, selecDates):
        global selectionDates
        selectionDates = list(selecDates)

    def GetSelectionDates(self):
        return list(selectionDates)

    def SetSelectionPersonnes(self, selecPersonnes):
        global selectionPersonnes
        selectionPersonnes = list(selecPersonnes)

    def GetSelectionPersonnes(self):
        return list(selectionPersonnes)

    def MAJpanelPlanning(self, reinitSelectionPersonnes=False):
        global selectionPersonnes, selectionDates
        mode_affichage = CTRL_Planning.modeAffichage
        if reinitSelectionPersonnes:
            selectionPersonnes = self.panelPlanning.RecherchePresents(selectionDates)
        self.panelPlanning.ReInitPlanning(
            mode_affichage,
            selectionPersonnes,
            selectionDates,
        )
        self.panelPlanning.DCplanning.MAJ_listCtrl_Categories()
        self.panelPlanning.DCplanning.MAJAffichage()

    def MAJpanel(self, listeElements=None, reinitSelectionPersonnes=False):
        if listeElements is None:
            listeElements = []
        if not self.init:
            self.InitPage()

        if "planning" in listeElements or listeElements == []:
            self.panelPlanning.DCplanning.Init_valeurs_defaut()
            self.panelPlanning.RechargeDictCategories()
            self.MAJpanelPlanning(reinitSelectionPersonnes=True)
        if "listCtrl_personnes" in listeElements or listeElements == []:
            self.panelPersonnes.MAJpanel()
        if "legendes" in listeElements or listeElements == []:
            self.panelLegendes.MAJpanel()
        if "calendrier" in listeElements or listeElements == []:
            self.panelCalendrier.MAJpanel()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.statusbar = self.CreateStatusBar(2, 0)
        self.statusbar.SetStatusWidths([360, -1])
        self.panel = PanelPresences(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetTitle(_(u"Panel Présences"))
        UTILS_Styles.ApplyWindowProfile(self, "workspace")


if __name__ == "__main__":
    app = wx.App(0)
    frame_test = TestFrame(None, -1, "")
    app.SetTopWindow(frame_test)
    frame_test.Show()
    app.MainLoop()
