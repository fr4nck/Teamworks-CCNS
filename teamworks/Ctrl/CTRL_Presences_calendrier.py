#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Calendrier sémantique de l'écran Présences."""

import datetime
import wx

from Ctrl import CTRL_Calendrier_tw
from Ctrl import CTRL_Presences_common
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


class PanelCalendrier(CTRL_Calendrier_tw.Panel):
    """Calendrier raccordé à la palette Teamworks.

    Les états calendaires consomment les cinq familles de la charte. Les
    anciens cadres bleus, gradients et polices locales sont supprimés du
    module Présences.
    """

    def __init__(self, parent, ID=-1):
        self._selection_dates = []
        CTRL_Calendrier_tw.Panel.__init__(
            self,
            parent,
            ID,
            bordHaut=0,
            bordBas=0,
            bordLateral=0,
        )
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.calendrier.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self._appliquer_palette()

    def _appliquer_palette(self):
        couleurs = {
            "couleurFond": "surface_container_lowest",
            "couleurNormal": "surface_container_lowest",
            "couleurWE": "surface_container_low",
            "couleurSelect": "primary",
            "couleurSurvol": "on_surface",
            "couleurFontJours": "on_surface",
            "couleurVacances": "warning",
            "couleurFontJoursAvecPresents": "primary",
            "couleurFerie": "surface_container_high",
        }
        for attribut, token in couleurs.items():
            setattr(self.calendrier, attribut, UTILS_Interface.GetToken(token))
        self.calendrier.MAJAffichage()

    def SetSelectionDates(self, listeDates):
        self._selection_dates = list(listeDates)
        panel = CTRL_Presences_common.find_presences_panel(self)
        if panel is not None:
            panel.SetSelectionDates(self._selection_dates)

    def GetSelectionDates(self):
        panel = CTRL_Presences_common.find_presences_panel(self)
        if panel is not None:
            return panel.GetSelectionDates()
        return list(self._selection_dates)

    def MAJselectionDates(self, listeDates):
        """Transmet la sélection sans dépendre d'un ancien arbre de splitters."""
        self.SetSelectionDates(listeDates)
        panel = CTRL_Presences_common.find_presences_panel(self)
        if panel is not None and getattr(panel, "init", False):
            panel.MAJpanelPlanning()
            panel.panelPersonnes.listCtrlPersonnes.CreateCouleurs()

    def OnBoutonAnnuel(self, event):
        """Bascule mensuel/annuel sans redimensionnements historiques codés en dur."""
        if self.calendrier.GetTypeCalendrier() == "mensuel":
            self.calendrier.SetTypeCalendrier("annuel")
            self.combo_mois.Enable(False)
            self.bouton_CalendrierAnnuel.SetToolTip(
                wx.ToolTip(_(u"Afficher le calendrier mensuel"))
            )
        else:
            self.calendrier.SetTypeCalendrier("mensuel")
            self.combo_mois.Enable(True)
            self.bouton_CalendrierAnnuel.SetToolTip(
                wx.ToolTip(_(u"Afficher le calendrier annuel"))
            )
        self.Layout()


class CTRL_Annee(wx.SpinCtrl):
    """Contrôle d'année conservé pour compatibilité avec les imports historiques."""

    def __init__(self, parent):
        wx.SpinCtrl.__init__(self, parent, -1, min=1950, max=2999)
        self.parent = parent
        self.SetMinSize((UTILS_Styles.Scale(72), -1))
        self.SetToolTip(wx.ToolTip(_(u"Sélectionnez une année")))
        self.SetAnnee(datetime.date.today().year)

    def SetAnnee(self, annee=None):
        self.SetValue(annee)

    def GetAnnee(self):
        return self.GetValue()
