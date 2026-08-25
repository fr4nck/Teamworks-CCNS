#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Entrée canonique modernisée pour la configuration des expéditeurs.

Le layout historique reste isolé dans ``DLG_Saisie_email_exp_legacy``. Cette
façade ne redéfinit que les frontières de validation/sérialisation qui doivent
être communes au moteur d'envoi et à l'écran de paramétrage.
"""

import Chemins
import wx
import wx.lib.agw.labelbook as LB

from Utils.UTILS_Traduction import _
from Utils import UTILS_Mailing
from Dlg import DLG_Saisie_email_exp_legacy as _legacy


CTRL_Infos = _legacy.CTRL_Infos


class Page_SMTP(_legacy.Page_SMTP):
    def GetDonnees(self):
        if self.radio_predefini.GetValue() is True:
            adresse = UTILS_Mailing.NormalizeEmail(self.ctrl_adresse.GetValue()) or self.ctrl_adresse.GetValue().strip()
            nom_adresse = self.ctrl_nom_adresse.GetValue() or None
            selection = self.ctrl_predefinis.GetSelection()
            smtp = self.listeServeurs[selection][1]
            port = self.listeServeurs[selection][2]
            auth = self.listeServeurs[selection][3]
            startTLS = self.listeServeurs[selection][4]
            if auth is True:
                motdepasse = self.ctrl_mdp.GetValue()
                utilisateur = self.ctrl_utilisateur.GetValue()
            else:
                motdepasse = None
                utilisateur = None
        else:
            adresse = UTILS_Mailing.NormalizeEmail(self.ctrl_adresse.GetValue()) or self.ctrl_adresse.GetValue().strip()
            nom_adresse = self.ctrl_nom_adresse.GetValue() or None
            smtp = self.ctrl_smtp.GetValue().strip() or None
            port_value = self.ctrl_port.GetValue().strip()
            port = int(port_value) if port_value else None
            if self.ctrl_authentification.GetValue() is True:
                auth = 1
                motdepasse = self.ctrl_mdp.GetValue()
                utilisateur = self.ctrl_utilisateur.GetValue()
            else:
                auth = 0
                motdepasse = None
                utilisateur = None
            startTLS = 1 if self.ctrl_startTLS.GetValue() is True else 0

        return {
            "moteur": "smtp",
            "adresse": adresse,
            "nom_adresse": nom_adresse,
            "motdepasse": motdepasse,
            "smtp": smtp,
            "port": port,
            "auth": auth,
            "startTLS": startTLS,
            "utilisateur": utilisateur,
            "parametres": None,
        }

    def Validation(self):
        if self.radio_predefini.GetValue() is True and self.ctrl_predefinis.GetSelection() == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous n'avez sélectionné aucun serveur de messagerie dans la liste !"),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if self.ctrl_authentification.GetValue() is True:
            if self.ctrl_mdp.GetValue() == "":
                dlg = wx.MessageDialog(
                    self,
                    _(u"Vous avez omis de saisir le mot de passe de votre messagerie !"),
                    _(u"Erreur de saisie"),
                    wx.OK | wx.ICON_ERROR,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return False
            if self.ctrl_utilisateur.GetValue() == "":
                dlg = wx.MessageDialog(
                    self,
                    _(u"Vous avez omis de saisir le nom d'utilisateur de votre messagerie !"),
                    _(u"Erreur de saisie"),
                    wx.OK | wx.ICON_ERROR,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return False

        try:
            donnees = self.GetDonnees()
            UTILS_Mailing.ValidateBackendConfig(
                backend=donnees["moteur"],
                email_exp=donnees["adresse"],
                host=donnees["smtp"],
                port=donnees["port"],
                username=donnees["utilisateur"],
                password=donnees["motdepasse"],
                use_tls=donnees["startTLS"],
                parameters=donnees["parametres"],
            )
        except (TypeError, ValueError) as err:
            dlg = wx.MessageDialog(self, str(err), _(u"Erreur de saisie"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        return True


class Page_MAILJET(_legacy.Page_MAILJET):
    def GetDonnees(self):
        adresse = UTILS_Mailing.NormalizeEmail(self.ctrl_adresse.GetValue()) or self.ctrl_adresse.GetValue().strip()
        nom_adresse = self.ctrl_nom_adresse.GetValue()
        api_key = self.ctrl_api_key.GetValue().strip()
        api_secret = self.ctrl_api_secret.GetValue().strip()
        parametres = UTILS_Mailing.SerializeBackendParameters(
            {"api_key": api_key, "api_secret": api_secret},
            ordered_names=("api_key", "api_secret"),
        )
        return {
            "moteur": "mailjet",
            "adresse": adresse,
            "nom_adresse": nom_adresse,
            "motdepasse": None,
            "smtp": None,
            "port": None,
            "auth": None,
            "startTLS": None,
            "utilisateur": None,
            "parametres": parametres,
        }

    def SetDonnees(self, dictDonnees=None):
        if dictDonnees is None:
            dictDonnees = {}
        self.ctrl_adresse.SetValue(dictDonnees.get("adresse", ""))
        self.ctrl_nom_adresse.SetValue(dictDonnees.get("nom_adresse", ""))
        dict_parametres = UTILS_Mailing.ParseBackendParameters(
            dictDonnees.get("parametres", None),
            strict=False,
        )
        self.ctrl_api_key.SetValue(dict_parametres.get("api_key", ""))
        self.ctrl_api_secret.SetValue(dict_parametres.get("api_secret", ""))

    def Validation(self):
        if self.ctrl_nom_adresse.GetValue() == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez saisir le nom à afficher !"),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        try:
            donnees = self.GetDonnees()
            UTILS_Mailing.ValidateBackendConfig(
                backend=donnees["moteur"],
                email_exp=donnees["adresse"],
                host=donnees["smtp"],
                port=donnees["port"],
                username=donnees["utilisateur"],
                password=donnees["motdepasse"],
                use_tls=donnees["startTLS"],
                parameters=donnees["parametres"],
            )
        except (TypeError, ValueError) as err:
            dlg = wx.MessageDialog(self, str(err), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        return True


class Dialog(_legacy.Dialog):
    def InitLabelbook(self):
        self.listePages = [
            (
                "smtp",
                _(u"SMTP"),
                Page_SMTP(self),
                wx.Bitmap(Chemins.GetStaticPath("Images/32x32/Smtp.png"), wx.BITMAP_TYPE_PNG),
            ),
            (
                "mailjet",
                _(u"Mailjet"),
                Page_MAILJET(self),
                wx.Bitmap(Chemins.GetStaticPath("Images/32x32/Mailjet.png"), wx.BITMAP_TYPE_PNG),
            ),
        ]

        image_list = wx.ImageList(32, 32)
        for code, label, ctrl, image in self.listePages:
            image_list.Add(image)
        self.ctrl_labelbook.AssignImageList(image_list)

        for index, page_data in enumerate(self.listePages):
            code, label, ctrl, image = page_data
            self.ctrl_labelbook.AddPage(ctrl, label, imageId=index)


if __name__ == "__main__":
    app = wx.App(0)
    dialog = Dialog(None, IDadresse=None)
    dialog.ShowModal()
    app.MainLoop()
