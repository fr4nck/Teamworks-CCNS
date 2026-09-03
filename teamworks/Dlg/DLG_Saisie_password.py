#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image, CTRL_Texte
import GestionDB
import FonctionsPerso
from Utils import UTILS_Styles


class Dialog(wx.Dialog):
    def __init__(self, parent, title=""):
        # Petit formulaire : sa taille doit suivre ses contrôles et le zoom,
        # pas fournir une surface librement étirable sans contenu extensible.
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.typeJour = type

        self.panel_base = wx.Panel(self, -1)
        self.label_password1 = CTRL_Texte.Label(self.panel_base, _(u"Mot de passe"))
        self.text_password1 = wx.TextCtrl(self.panel_base, -1, "", style=wx.TE_PASSWORD)
        self.label_password2 = CTRL_Texte.Label(self.panel_base, _(u"Confirmation"))
        self.text_password2 = wx.TextCtrl(self.panel_base, -1, "", style=wx.TE_PASSWORD)
        UTILS_Styles.ApplyFieldRole(self.text_password1, UTILS_Styles.FIELD_NAME)
        UTILS_Styles.ApplyFieldRole(self.text_password2, UTILS_Styles.FIELD_NAME)

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_SHOW, self.OnShow)

    def __set_properties(self):
        self.SetTitle(_(u"Saisie d'un mot de passe"))
        self.text_password1.SetToolTip(wx.ToolTip(_(u"Saisissez ici votre mot de passe")))
        self.text_password2.SetToolTip(
            wx.ToolTip(_(u"Saisissez ici une deuxième fois votre mot de passe pour confirmation"))
        )
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour annuler la saisie")))

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        action_gap = UTILS_Styles.GetLayoutSpacing("control_gap")

        champs = wx.BoxSizer(wx.VERTICAL)
        champs.Add(self.label_password1, 0, wx.EXPAND)
        champs.AddSpacer(gap)
        champs.Add(self.text_password1, 0, wx.EXPAND)
        champs.AddSpacer(gap)
        champs.Add(self.label_password2, 0, wx.EXPAND)
        champs.AddSpacer(gap)
        champs.Add(self.text_password2, 0, wx.EXPAND)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0, wx.RIGHT, action_gap)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, action_gap)
        actions.Add(self.bouton_annuler, 0)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(champs, 0, wx.EXPAND | wx.ALL, padding)
        panel_sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.panel_base.SetSizer(panel_sizer)

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(sizer_base)
        UTILS_Styles.ApplyWindowProfile(self, "fit")

    def OnShow(self, event):
        # Le contrôle est refitté une fois visible afin de prendre en compte les
        # métriques Windows/DPI et la police réellement appliquée au zoom courant.
        if event.IsShown():
            wx.CallAfter(UTILS_Styles.RefitWindow, self)
        event.Skip()

    def Sauvegarde(self):
        """Sauvegarde des données dans la base de données."""
        varPassword = self.text_password1.GetValue()

        DB = GestionDB.DB()
        listeDonnees = [("motdepasse", varPassword)]
        DB.ReqMAJ("divers", listeDonnees, "IDdivers", 1)
        DB.Commit()
        DB.Close()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Laprotectionparmotdepasse")

    def OnBoutonAnnuler(self, event):
        parent = self.GetParent()
        if parent is not None and hasattr(parent, "checkBox"):
            parent.checkBox.SetValue(False)
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        """Validation des données saisies."""
        varPassword1 = self.text_password1.GetValue()
        if varPassword1 == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez saisir un mot de passe valide !"),
                "Erreur",
                wx.OK,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.text_password1.SetFocus()
            return

        varPassword2 = self.text_password2.GetValue()
        if varPassword2 == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez confirmer le mot de passe !"),
                "Erreur",
                wx.OK,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.text_password2.SetFocus()
            return

        if varPassword1 != varPassword2:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous avez saisi deux mots de passe différents ! \n\nVeuillez recommencer votre saisie."),
                "Erreur",
                wx.OK,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.text_password1.SetFocus()
            return

        self.Sauvegarde()

        if FonctionsPerso.FrameOuverte("panel_config_password") is not None:
            parent = self.GetParent()
            if parent is not None and hasattr(parent, "MAJpanel"):
                parent.MAJpanel()

        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, "")
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
