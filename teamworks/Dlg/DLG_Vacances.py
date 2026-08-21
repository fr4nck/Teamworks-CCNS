#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Ol import OL_Vacances


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        intro = _(u"Vous pouvez ici saisir, modifier ou supprimer des périodes de vacances. Cliquez sur 'Importer depuis Internet' pour télécharger automatiquement les périodes depuis le site de l'Education Nationale.")
        titre = _(u"Gestion des périodes de vacances")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(
            self,
            titre=titre,
            texte=intro,
            hauteurHtml=30,
            nomImage=Chemins.GetStaticPath("Images/32x32/Calendrier.png"),
        )
        self.ctrl_listview = OL_Vacances.ListView(
            self,
            id=-1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.ctrl_listview.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.ctrl_listview.MAJ()
        self.ctrl_recherche = OL_Vacances.CTRL_Outils(self, listview=self.ctrl_listview)

        self.bouton_ajouter = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Ajouter"), cheminImage="Images/32x32/Ajouter.png"
        )
        self.bouton_modifier = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Modifier"), cheminImage="Images/32x32/Modifier.png"
        )
        self.bouton_supprimer = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Supprimer"), cheminImage="Images/32x32/Supprimer.png"
        )

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png"
        )
        self.bouton_importation = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Importer depuis internet"),
            cheminImage="Images/32x32/Fleche_bas.png",
        )
        self.bouton_fermer = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte=_(u"Fermer"),
            cheminImage="Images/32x32/Fermer.png",
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.Supprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImportation, self.bouton_importation)

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des périodes de vacances"))
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour ajouter une période de vacances")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier la période de vacances sélectionnée dans la liste")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer la période de vacances sélectionnée dans la liste")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_importation.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour importer des périodes depuis le site internet de l'Education Nationale")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour fermer")))
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def __do_layout(self):
        dialog_padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND)
        sizer_base.Add(
            self.ctrl_listview,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            dialog_padding,
        )
        sizer_base.Add(
            self.ctrl_recherche,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            field_gap,
        )

        sizer_actions = wx.WrapSizer(wx.HORIZONTAL)
        sizer_actions.Add(self.bouton_ajouter, 0, wx.RIGHT | wx.BOTTOM, toolbar_gap)
        sizer_actions.Add(self.bouton_modifier, 0, wx.RIGHT | wx.BOTTOM, toolbar_gap)
        sizer_actions.Add(self.bouton_supprimer, 0, wx.RIGHT | wx.BOTTOM, toolbar_gap)
        sizer_base.Add(
            sizer_actions,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            dialog_padding,
        )

        sizer_boutons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_boutons.Add(self.bouton_aide, 0, wx.RIGHT, toolbar_gap)
        sizer_boutons.Add(self.bouton_importation, 0, wx.RIGHT, toolbar_gap)
        sizer_boutons.AddStretchSpacer(1)
        sizer_boutons.Add(self.bouton_fermer, 0)
        sizer_base.Add(sizer_boutons, 0, wx.EXPAND | wx.ALL, dialog_padding)

        self.SetSizer(sizer_base)
        self.Layout()

    def Ajouter(self, event):
        self.ctrl_listview.Ajouter(None)

    def Modifier(self, event):
        self.ctrl_listview.Modifier(None)

    def Supprimer(self, event):
        self.ctrl_listview.Supprimer(None)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Vacances")

    def OnBoutonImportation(self, event):
        self.ctrl_listview.Importation(None)


if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
