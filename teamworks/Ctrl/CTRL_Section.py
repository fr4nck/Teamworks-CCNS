#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Section visuelle réutilisable, équivalent d'un <section> Web.

Le composant ne choisit aucune couleur ni métrique locale : il consomme la
charte Teamworks (typographie, surfaces et espacements) afin que les écrans
restent cohérents et modifiables depuis un point central.
"""

import wx

from Ctrl import CTRL_Texte
from Utils import UTILS_Interface, UTILS_Styles


class Section(wx.Panel):
    def __init__(self, parent, titre=u"", niveau=2, description=u"", surface="surface_container_lowest"):
        wx.Panel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        self.surface = surface
        self.SetBackgroundColour(UTILS_Interface.GetToken(surface))

        fabrique_titre = {
            2: CTRL_Texte.H2,
            3: CTRL_Texte.H3,
            4: CTRL_Texte.H4,
            5: CTRL_Texte.H5,
            6: CTRL_Texte.H6,
        }.get(niveau, CTRL_Texte.H2)

        self.titre = fabrique_titre(self, titre) if titre else None
        self.description = CTRL_Texte.BodySecondary(self, description) if description else None
        self.contenu = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL)
        self.contenu.SetBackgroundColour(UTILS_Interface.GetToken(surface))

        self._layout()

    def _layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        if self.titre is not None:
            sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        if self.description is not None:
            sizer.Add(self.description, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(self.contenu, 1, wx.EXPAND | wx.ALL, padding)
        self.SetSizer(sizer)
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() | wx.TAB_TRAVERSAL)
        self.gap = gap

    def GetContentPanel(self):
        return self.contenu

    def GetGap(self):
        return self.gap
