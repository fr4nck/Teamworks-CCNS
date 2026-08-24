#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import wx

from Utils.UTILS_Traduction import _
from Ctrl import CTRL_Bouton_image, CTRL_Section, CTRL_Texte
from Utils import UTILS_Interface, UTILS_Styles


class MyDialog(wx.Dialog):
    """Choix possibles : None pour « sans importance » ou une liste cochée."""

    def __init__(self, parent, nom_filtre=u"", titre_frame=u"", listeSelection=None, listeChoix=None):
        if listeChoix is None:
            listeChoix = []
        wx.Dialog.__init__(
            self,
            parent,
            id=-1,
            title=titre_frame,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.nom_filtre = nom_filtre
        self.titre_frame = titre_frame
        self.listeSelection = listeSelection
        self.listeChoix = listeChoix
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = CTRL_Texte.H1(self, titre_frame or _(u"Filtre"))
        self.label = CTRL_Texte.BodySecondary(
            self,
            _(u"Définissez un filtre pour le champ « %s ».") % self.nom_filtre,
        )
        self.section = CTRL_Section.Section(self, titre=self.nom_filtre.capitalize(), niveau=2)
        panel = self.section.GetContentPanel()

        self.radio1 = wx.RadioButton(panel, -1, _(u"Sans importance"), style=wx.RB_GROUP)
        self.radio2 = wx.RadioButton(panel, -1, _(u"Uniquement les éléments sélectionnés"))
        self.checkListBox = CheckListBox(panel)
        self.checkListBox.Remplissage(self.listeChoix)

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.radio1, 0, wx.EXPAND)
        contenu.Add(self.radio2, 0, wx.EXPAND | wx.TOP, UTILS_Styles.GetLayoutSpacing("field_gap"))
        contenu.Add(self.checkListBox, 1, wx.EXPAND | wx.TOP, UTILS_Styles.GetLayoutSpacing("field_gap"))
        panel.SetSizer(contenu)

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, id=wx.ID_OK, texte=_(u"Appliquer"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radio1)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radio2)

        if self.listeSelection is not None:
            self.checkListBox.CocheListe(self.listeSelection)
            self.radio2.SetValue(True)
        self.OnRadio(None)

        self._layout()
        UTILS_Styles.ApplyWindowProfile(self, "standard")

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
        sizer.Add(self.section, 1, wx.EXPAND | wx.ALL, gap)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)

    def OnRadio(self, event):
        self.checkListBox.Enable(not self.radio1.GetValue())

    def GetListeSelections(self):
        if self.radio1.GetValue():
            return None
        return self.checkListBox.GetIDetLabels()

    def OnBoutonOk(self, event):
        self.EndModal(wx.ID_OK)


class CheckListBox(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, choices=[])
        self.listeDonnees = []
        self.listeIDcoches = []
        self.dictIndexes = {}
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck, self)

    def Remplissage(self, liste=None):
        if liste is not None:
            self.listeDonnees = liste
        self.dictIndexes = {}
        self.Clear()
        for index, (ID, texte) in enumerate(self.listeDonnees):
            self.Append(texte)
            self.dictIndexes[index] = ID

    def CocheListe(self, liste=None):
        if liste is not None:
            self.listeIDcoches = liste
        for index in range(self.GetCount()):
            self.Check(index, self.dictIndexes[index] in self.listeIDcoches)

    def GetIDcoches(self):
        return [
            self.dictIndexes[index]
            for index in range(self.GetCount())
            if self.IsChecked(index)
        ]

    def GetIDetLabels(self):
        return [
            (self.dictIndexes[index], self.GetString(index))
            for index in range(self.GetCount())
            if self.IsChecked(index)
        ]

    def OnCheck(self, event):
        self.listeIDcoches = self.GetIDcoches()


if __name__ == "__main__":
    app = wx.App(0)
    frm = MyDialog(None)
    frm.ShowModal()
    app.MainLoop()
