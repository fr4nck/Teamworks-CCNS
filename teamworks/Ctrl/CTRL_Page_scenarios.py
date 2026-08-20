#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
import wx
from Dlg import DLG_Scenario_gestion


class Panel(wx.Panel):
    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Panel.__init__(self, parent, id, name="panel_pageScenarios", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = wx.StaticText(self, -1, _(u"Scénarios"))
        font = self.titre.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(max(11, font.GetPointSize() + 2))
        self.titre.SetFont(font)

        self.panelScenarios = DLG_Scenario_gestion.Panel(self, IDpersonne=self.IDpersonne)
        self.panelScenarios.label_introduction.Show(False)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer.Add(self.panelScenarios, 1, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(sizer)
