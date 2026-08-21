#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface, UTILS_Styles
import wx
from Ctrl import CTRL_Texte
from Dlg import DLG_Scenario_gestion


class Panel(wx.Panel):
    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Panel.__init__(self, parent, id, name="panel_pageScenarios", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = CTRL_Texte.H2(self, _(u"Scénarios"))
        self.panelScenarios = DLG_Scenario_gestion.Panel(self, IDpersonne=self.IDpersonne)
        self.panelScenarios.label_introduction.Show(False)

        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(
            self.panelScenarios,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM,
            field_gap,
        )
        self.SetSizer(sizer)
