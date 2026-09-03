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
from Ctrl import CTRL_Bouton_image, CTRL_Texte
import FonctionsPerso
from Dlg import DLG_Saisie_password_dialog
from Utils import UTILS_Styles


class Panel(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="panel_config_verrouillage_entretien", style=wx.TAB_TRAVERSAL)

        self.barreTitre = FonctionsPerso.BarreTitre(self, _(u"Verrouillage des informations des entretiens"), u"")
        texteIntro = _(u"Vous pouvez protéger l'accès aux informations liées aux entretiens d'embauche (avis et commentaires).\nL'utilisateur devra ainsi saisir un mot de passe pour les afficher. Cochez la case et saisissez le mot de passe\nsouhaité à deux reprises. Pour désactiver la protection, il vous suffit de décocher cette case.")
        self.label_introduction = FonctionsPerso.StaticWrapText(self, -1, texteIntro)

        self.staticbox = wx.StaticBox(self, -1, _(u"Protection"))
        self.checkBox = wx.CheckBox(self.staticbox, -1, _(u"Activer la protection par mot de passe"))

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
        password = FonctionsPerso.Parametres(
            mode="get", categorie="recrutement", nom="password_entretien", valeur=""
        )
        self.checkBox.SetValue(password not in ("", None))

    def OnCheck(self, event):
        if self.checkBox.GetValue() is False:
            dlg = wx.MessageDialog(
                self,
                _(u"Voulez-vous vraiment annuler la protection par mot de passe ?"),
                "Confirmation",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dlg.ShowModal() == wx.ID_YES:
                dlg.Destroy()
                password = FonctionsPerso.Parametres(
                    mode="get", categorie="recrutement", nom="password_entretien", valeur=""
                )
                dlg = SaisiePassword(self)
                if dlg.ShowModal() == wx.ID_OK:
                    pwd = dlg.GetPassword()
                    if pwd != password:
                        dlg2 = wx.MessageDialog(
                            self,
                            _(u"Votre mot de passe est erroné."),
                            _(u"Mot de passe erroné"),
                            wx.OK | wx.ICON_ERROR,
                        )
                        dlg2.ShowModal()
                        dlg2.Destroy()
                        self.checkBox.SetValue(True)
                        dlg.Destroy()
                        return
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    self.checkBox.SetValue(True)
                    return
                FonctionsPerso.Parametres(
                    mode="set", categorie="recrutement", nom="password_entretien", valeur=""
                )
                self.checkBox.SetValue(False)
            else:
                self.checkBox.SetValue(True)
                dlg.Destroy()
        else:
            dlg = DLG_Saisie_password_dialog.MyDialog(self)
            if dlg.ShowModal() == wx.ID_OK:
                pwd = dlg.GetPassword()
                FonctionsPerso.Parametres(
                    mode="set", categorie="recrutement", nom="password_entretien", valeur=pwd
                )
                dlg.Destroy()
                self.checkBox.SetValue(True)
            else:
                self.checkBox.SetValue(False)
                dlg.Destroy()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Laprotectionparmotdepasse")


class SaisiePassword(wx.Dialog):
    def __init__(self, parent, id=-1, title=_(u"Saisie du code de déverrouillage")):
        wx.Dialog.__init__(self, parent, id, title, style=wx.DEFAULT_DIALOG_STYLE)

        self.label_2 = CTRL_Texte.BodySecondary(
            self,
            _(u"Pour désactiver le mot de passe, vous devez déjà le saisir."),
        )
        self.label_password = CTRL_Texte.Label(self, _(u"Mot de passe"))
        self.text_password = wx.TextCtrl(self, -1, "", style=wx.TE_PASSWORD)
        UTILS_Styles.ApplyFieldRole(self.text_password, UTILS_Styles.FIELD_NAME)

        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_OK,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )
        self.text_password.SetToolTip(wx.ToolTip(_(u"Saisissez votre mot de passe ici")))
        self.__do_layout()
        self.Bind(wx.EVT_SHOW, self.OnShow)

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        action_gap = UTILS_Styles.GetLayoutSpacing("control_gap")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_2, 0, wx.EXPAND | wx.ALL, padding)
        sizer.Add(self.label_password, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, padding)
        sizer.AddSpacer(gap)
        sizer.Add(self.text_password, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, padding)
        sizer.AddSpacer(padding)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, action_gap)
        actions.Add(self.bouton_annuler, 0)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)

        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "fit")

    def OnShow(self, event):
        if event.IsShown():
            wx.CallAfter(UTILS_Styles.RefitWindow, self)
        event.Skip()

    def GetPassword(self):
        return self.text_password.GetValue()


class Dialog(wx.Dialog):
    def __init__(self, parent):
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
        self.SetTitle(_(u"Verrouillage des informations des entretiens"))
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

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(sizer_pages, 1, wx.EXPAND | wx.ALL, padding)
        panel_sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.panel_base.SetSizer(panel_sizer)

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(sizer_base)
        self.sizer_pages = sizer_pages
        UTILS_Styles.ApplyWindowProfile(self, "fit")

    def OnShow(self, event):
        if event.IsShown():
            wx.CallAfter(UTILS_Styles.RefitWindow, self)
        event.Skip()

    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

    def Onbouton_annuler(self, event):
        self.EndModal(wx.ID_CANCEL)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
