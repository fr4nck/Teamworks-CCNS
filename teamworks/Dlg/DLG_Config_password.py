#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
import FonctionsPerso
from Dlg import DLG_Saisie_password
from Utils import UTILS_Styles


class Panel(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="panel_config_password", style=wx.TAB_TRAVERSAL)

        self.barreTitre = FonctionsPerso.BarreTitre(self, _(u"Protection par mot de passe"), u"")
        texteIntro = _(u"Vous pouvez protéger l'accès à ce fichier par un mot de passe. L'utilisateur de ce fichier devra\nainsi saisir le mot de passe à son ouverture. Cochez la case et saisissez le mot de passe souhaité\nà deux reprises. Pour désactiver la protection, il vous suffit de décocher cette case.")
        self.label_introduction = FonctionsPerso.StaticWrapText(self, -1, texteIntro)

        self.staticbox = wx.StaticBox(self, -1, _(u"Protection"))
        self.checkBox = wx.CheckBox(self.staticbox, -1, _(u"Activer la protection par mot de passe"))
        self.MAJ_checkBox()

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        if parent.GetName() != "treebook_configuration":
            self.bouton_aide.Show(False)

        self.Bind(wx.EVT_CHECKBOX, self.OnCheck, self.checkBox)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)

        # Layout historique conservé ici : le peigne iconographique ne doit pas
        # modifier le comportement métier de la page de configuration.
        grid_sizer_principal = wx.FlexGridSizer(rows=5, cols=1, vgap=0, hgap=0)
        grid_sizer_principal.Add(self.barreTitre, 1, wx.EXPAND, 0)
        grid_sizer_principal.Add(self.label_introduction, 1, wx.ALL | wx.EXPAND, 10)

        staticbox = wx.StaticBoxSizer(self.staticbox, wx.VERTICAL)
        staticbox.Add(self.checkBox, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer_principal.Add(staticbox, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_principal.Add((20, 20), 0, wx.ALL | wx.EXPAND, 10)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=10)
        grid_sizer_boutons.Add((5, 5), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_principal.Add(grid_sizer_boutons, 1, wx.EXPAND | wx.ALL, 10)

        grid_sizer_principal.AddGrowableRow(3)
        grid_sizer_principal.AddGrowableCol(0)
        self.SetSizer(grid_sizer_principal)
        grid_sizer_principal.Fit(self)

    def MAJpanel(self):
        self.MAJ_checkBox()

    def MAJ_checkBox(self):
        """Recherche le mot de passe dans la base."""
        DB = GestionDB.DB()
        req = "SELECT motdepasse FROM divers WHERE IDdivers=1;"
        DB.ExecuterReq(req)
        donnees = DB.ResultatReq()
        DB.Close()
        if len(donnees) == 0:
            return
        password = donnees[0][0]

        if password in ("", None):
            self.checkBox.SetValue(False)
        else:
            self.checkBox.SetValue(True)

    def OnCheck(self, event):
        if self.checkBox.GetValue() is False:
            dlg = wx.MessageDialog(
                self,
                _(u"Voulez-vous vraiment annuler la protection par mot de passe ?"),
                "Confirmation",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dlg.ShowModal() == wx.ID_YES:
                DB = GestionDB.DB()
                listeDonnees = [("motdepasse", "")]
                DB.ReqMAJ("divers", listeDonnees, "IDdivers", 1)
                DB.Commit()
                DB.Close()
                dlg.Destroy()
                self.checkBox.SetValue(False)
            else:
                self.checkBox.SetValue(True)
                dlg.Destroy()
        else:
            dlg = DLG_Saisie_password.Dialog(self)
            dlg.ShowModal()
            dlg.Destroy()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Laprotectionparmotdepasse")


class Dialog(wx.Dialog):
    def __init__(self, parent):
        # Formulaire compact : pas de RESIZE_BORDER/MAXIMIZE_BOX/MINIMIZE_BOX.
        # Le profil fit suit le contenu et le zoom au lieu de laisser la fenêtre
        # s'étirer comme une zone de travail.
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent

        self.panel_base = wx.Panel(self, -1)
        self.panel_contenu = Panel(self.panel_base)
        self.panel_contenu.barreTitre.Show(False)
        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_fermer = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Fermer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"),
        )
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_fermer)
        self.Bind(wx.EVT_SHOW, self.OnShow)

    def __set_properties(self):
        self.SetTitle(_(u"Protection par mot de passe"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_(u"Cliquez pour fermer")))

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("control_gap")

        sizer_pages = wx.BoxSizer(wx.VERTICAL)
        sizer_pages.Add(self.panel_contenu, 1, wx.EXPAND)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0, wx.RIGHT, gap)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_fermer, 0)

        sizer_panel = wx.BoxSizer(wx.VERTICAL)
        sizer_panel.Add(sizer_pages, 1, wx.EXPAND | wx.ALL, padding)
        sizer_panel.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.panel_base.SetSizer(sizer_panel)

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(sizer_base)
        self.sizer_pages = sizer_pages
        UTILS_Styles.ApplyWindowProfile(self, "fit")

    def OnShow(self, event):
        # Refit différé : les métriques réellement appliquées par Windows,
        # le thème et le zoom sont prises en compte avant de figer l'enveloppe.
        if event.IsShown():
            wx.CallAfter(UTILS_Styles.RefitWindow, self)
        event.Skip()

    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Laprotectionparmotdepasse")

    def Onbouton_annuler(self, event):
        self.EndModal(wx.ID_CANCEL)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
