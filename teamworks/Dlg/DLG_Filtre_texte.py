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
    """Choix possibles : None pour « sans importance » ou un texte."""

    def __init__(self, parent, nom_filtre=u"", titre_frame=u"", texte=None):
        wx.Dialog.__init__(
            self,
            parent,
            id=-1,
            title=titre_frame,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.nom_filtre = nom_filtre
        self.titre_frame = titre_frame
        self.texte = texte
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = CTRL_Texte.H1(self, titre_frame or _(u"Filtre"))
        self.label = CTRL_Texte.BodySecondary(
            self,
            _(u"Définissez un filtre pour %s.") % self.nom_filtre,
        )
        self.section = CTRL_Section.Section(self, titre=self.nom_filtre.capitalize(), niveau=2)
        panel = self.section.GetContentPanel()

        self.radio1 = wx.RadioButton(panel, -1, _(u"Sans importance"), style=wx.RB_GROUP)
        self.radio2 = wx.RadioButton(panel, -1, _(u"Comportant l'expression suivante"))
        self.ctrl_texte = wx.TextCtrl(panel, -1, "")

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.radio1, 0, wx.EXPAND)
        contenu.Add(self.radio2, 0, wx.EXPAND | wx.TOP, UTILS_Styles.GetLayoutSpacing("field_gap"))
        contenu.Add(self.ctrl_texte, 0, wx.EXPAND | wx.TOP, UTILS_Styles.GetLayoutSpacing("field_gap"))
        panel.SetSizer(contenu)

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, id=wx.ID_OK, texte=_(u"Appliquer"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radio1)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radio2)

        if self.texte is not None:
            self.ctrl_texte.SetValue(texte)
            self.radio2.SetValue(True)
        self.OnRadio(None)

        self._layout()
        UTILS_Styles.ApplyWindowProfile(self, "compact")

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
        self.ctrl_texte.Enable(not self.radio1.GetValue())

    def GetTexte(self):
        if self.radio1.GetValue():
            return None
        return self.ctrl_texte.GetValue()

    def OnBoutonOk(self, event):
        if self.radio2.GetValue() and self.ctrl_texte.GetValue() == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous avez oublié de saisir une expression à trouver !"),
                _(u"Information"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    frm = MyDialog(None, nom_filtre=_(u"les offres"), titre_frame=_(u"Filtre des offres"), texte=None)
    frm.ShowModal()
    app.MainLoop()
