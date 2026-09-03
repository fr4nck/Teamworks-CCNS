#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Navigation et recherche du module Recrutement."""

import wx

from Ctrl import CTRL_Bouton_image
from ObjectListView import Filter
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


def _racine_recrutement(window):
    current = window
    while current is not None:
        try:
            if current.GetName() == "Recrutement":
                return current
        except Exception:
            pass
        try:
            current = current.GetParent()
        except Exception:
            current = None
    return None


class BoutonMode(CTRL_Bouton_image.Toggle):
    """Sélecteur de mode recrutements basé sur le contrat Toggle commun."""

    def __init__(self, parent, label, mode):
        CTRL_Bouton_image.Toggle.__init__(self, parent, texte=label)
        self.mode = mode

    def AppliquerTheme(self, actif=None):
        if actif is not None and bool(actif) != self.GetValue():
            self.SetValue(bool(actif))
            return
        CTRL_Bouton_image.Toggle.AppliquerTheme(self)


class BarreModes(wx.Panel):
    MODES = (
        ("candidats", _(u"Candidats")),
        ("candidatures", _(u"Candidatures")),
        ("entretiens", _(u"Entretiens")),
        ("emplois", _(u"Offres d'emploi")),
    )

    def __init__(self, parent, mode_initial="candidats"):
        wx.Panel.__init__(self, parent, -1, name="barre_modes_recrutement")
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_low"))
        self.boutons = {}

        gap = UTILS_Styles.GetLayoutSpacing("control_gap")
        sizer = wx.WrapSizer(wx.HORIZONTAL)
        for mode, label in self.MODES:
            bouton = BoutonMode(self, label, mode)
            bouton.Bind(wx.EVT_TOGGLEBUTTON, self.OnMode)
            self.boutons[mode] = bouton
            sizer.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)
        self.SetSizer(sizer)
        self.SetMode(mode_initial, notifier=False)

    def SetMode(self, mode, notifier=True):
        if mode not in self.boutons:
            return
        for code, bouton in self.boutons.items():
            bouton.SetValue(code == mode)
        if notifier:
            racine = _racine_recrutement(self)
            if racine is not None:
                racine.ChangerMode(mode)

    def OnMode(self, event):
        self.SetMode(event.GetEventObject().mode)


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, list_view):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.listView = list_view
        self.SetDescriptiveText(_(u"Rechercher un candidat"))
        self.ShowSearchButton(True)
        self.ShowCancelButton(False)
        self.SetMinSize((-1, UTILS_Styles.GetControlMetric("input_min_height")))

        nbre_colonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(
            Filter.TextSearch(self.listView, self.listView.columns[0:nbre_colonnes])
        )

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, event):
        self.Recherche(self.GetValue())

    def OnCancel(self, event):
        self.SetValue("")
        self.Recherche("")

    def OnDoSearch(self, event):
        self.Recherche(self.GetValue())

    def Recherche(self, texte):
        self.ShowCancelButton(bool(texte))
        self.listView.GetFilter().SetText(texte)
        self.listView.RepopulateList()
