#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Adaptations, UTILS_Interface, UTILS_Styles
from Ctrl import CTRL_Bouton_image, CTRL_Texte

OL_candidats = UTILS_Adaptations.Import("Ol.OL_candidats")
OL_personnes = UTILS_Adaptations.Import("Ol.OL_personnes")


class MyDialog(wx.Dialog):
    """Sélection d'un candidat ou d'un salarié."""

    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            id=-1,
            title=_(u"Sélectionner un candidat ou un salarié"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = CTRL_Texte.H1(self, _(u"Sélection d'une personne"))
        self.label = CTRL_Texte.BodySecondary(
            self,
            _(u"Choisissez un candidat ou un salarié dans l'onglet correspondant."),
        )

        self.noteBook = wx.Notebook(self, -1, style=wx.BK_TOP)
        style_liste = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES

        self.listCtrl_candidats = OL_candidats.ListView(
            self.noteBook,
            id=-1,
            activeDoubleClic=False,
            name="OL_candidats",
            style=style_liste,
        )
        self.listCtrl_candidats.MAJ()
        self.noteBook.AddPage(self.listCtrl_candidats, _(u"Candidats"))

        self.listCtrl_personnes = OL_personnes.ListView(
            self.noteBook,
            id=-1,
            activeDoubleClic=False,
            name="OL_personnes",
            style=style_liste,
        )
        self.noteBook.AddPage(self.listCtrl_personnes, _(u"Salariés"))

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, id=wx.ID_OK, texte=_(u"Sélectionner"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

        self._layout()
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def _layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, toolbar_gap)
        actions.Add(self.bouton_annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(self.label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(self.noteBook, 1, wx.EXPAND | wx.ALL, gap)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)

    def OnBoutonOk(self, event):
        selection_candidat = self.listCtrl_candidats.Selection()
        selection_personne = self.listCtrl_personnes.Selection()
        numPage = self.noteBook.GetSelection()

        if numPage == 0 and len(selection_candidat) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous n'avez sélectionné aucun candidat !"),
                _(u"Aucune sélection"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        if numPage == 1 and len(selection_personne) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous n'avez sélectionné aucun salarié !"),
                _(u"Aucune sélection"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.EndModal(wx.ID_OK)

    def GetIDcandidat(self):
        if self.noteBook.GetSelection() != 0:
            return 0
        selection = self.listCtrl_candidats.Selection()
        if not selection:
            return 0
        return selection[0].IDcandidat

    def GetIDpersonne(self):
        if self.noteBook.GetSelection() != 1:
            return 0
        selection = self.listCtrl_personnes.Selection()
        if not selection:
            return 0
        return selection[0].IDpersonne


if __name__ == "__main__":
    app = wx.App(0)
    frm = MyDialog(None)
    frm.ShowModal()
    app.MainLoop()
