#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Teamworks
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.easter import easter


def _dip(window, width, height):
    try:
        return window.FromDIP(wx.Size(width, height))
    except Exception:
        return wx.Size(width, height)


class MyDialog(wx.Dialog):
    def __init__(self, parent, fichierOuvert=None):
        wx.Dialog.__init__(self, parent, id=-1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.label_intro = wx.StaticText(
            self,
            -1,
            _(u"Cette fonctionnalité permet à Teamworks de créer les jours fériés variables d'une ou plusieurs années selon les algorithmes intégrés. Saisissez une ou plusieurs années séparées par un point-virgule, choisissez les jours à créer puis validez."),
        )
        self.label_intro.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        self.label_annees = wx.StaticText(self, -1, _(u"Années"))
        self.ctrl_annees = wx.TextCtrl(self, -1, u"")
        self.label_jours = wx.StaticText(self, -1, _(u"Jours fériés"))
        listeJours = [_(u"Lundi de Pâques"), _(u"Jeudi de l'ascension"), _(u"Lundi de Pentecôte")]
        self.ctrl_jours = wx.CheckListBox(self, -1, choices=listeJours)
        self.ctrl_jours.SetMinSize(_dip(self, 320, 110))

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png")
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self, id=wx.ID_OK, texte=_(u"Créer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png")
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self, id=wx.ID_CANCEL, texte=_(u"Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png")
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def __set_properties(self):
        self.SetTitle(_(u"Saisie automatique des jours fériés variables"))
        self.ctrl_annees.SetToolTip(wx.ToolTip(_(u"Saisissez une année ou plusieurs années séparées de points-virgules (;). Exemple : '2011;2012;2013' ")))
        self.ctrl_jours.SetToolTip(wx.ToolTip(_(u"Cochez les jours fériés à créer")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour créer les jours fériés")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour annuler")))
        self.SetMinSize(_dip(self, 520, 400))
        self.SetSize(_dip(self, 620, 470))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_intro, 0, wx.EXPAND | wx.ALL, 16)

        sizer_form = wx.BoxSizer(wx.VERTICAL)
        sizer_form.Add(self.label_annees, 0, wx.BOTTOM, 4)
        sizer_form.Add(self.ctrl_annees, 0, wx.EXPAND | wx.BOTTOM, 14)
        sizer_form.Add(self.label_jours, 0, wx.BOTTOM, 4)
        sizer_form.Add(self.ctrl_jours, 1, wx.EXPAND)
        sizer_base.Add(sizer_form, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)

        sizer_boutons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_boutons.Add(self.bouton_aide, 0, wx.RIGHT, 8)
        sizer_boutons.AddStretchSpacer(1)
        sizer_boutons.Add(self.bouton_ok, 0, wx.RIGHT, 8)
        sizer_boutons.Add(self.bouton_annuler, 0)
        sizer_base.Add(sizer_boutons, 0, wx.EXPAND | wx.ALL, 16)

        self.SetSizer(sizer_base)
        self.Layout()
        self.CenterOnScreen()
        wx.CallAfter(self._wrap_intro)

    def _wrap_intro(self):
        width = max(280, self.GetClientSize().width - 32)
        self.label_intro.Wrap(width)
        self.Layout()

    def OnSize(self, event):
        self._wrap_intro()
        event.Skip()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lesjoursfris")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        # Récupération des années
        if self.ctrl_annees.GetValue() == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir une année !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        listeAnnees = []
        for annee in self.ctrl_annees.GetValue().split(";"):
            try:
                listeAnnees.append(int(annee))
                if int(annee) < 1900 or int(annee) > 3000:
                    raise Exception()
            except:
                dlg = wx.MessageDialog(self, _(u"Les années saisies ne semblent pas valides !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        # Récupération jours fériés à créer
        listeCoches = []
        for index in range(0, self.ctrl_jours.GetCount()):
            if self.ctrl_jours.IsChecked(index):
                listeCoches.append(index)

        if len(listeCoches) == 0:
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement cocher au moins un jour férié à créer !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Récupération des jours déjà présents dans la base de données
        DB = GestionDB.DB()
        req = """SELECT IDferie, nom, jour, mois, annee
        FROM jours_feries
        WHERE type='variable' ; """
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        listeJoursExistants = []
        for IDferie, nom, jour, mois, annee in listeDonnees:
            try:
                listeJoursExistants.append(datetime.date(annee, mois, jour))
            except:
                pass

        def SauvegarderDate(nom="", date=None):
            if date not in listeJoursExistants:
                IDferie = DB.ReqInsert("jours_feries", [("type", "variable"), ("nom", nom), ("annee", date.year), ("mois", date.month), ("jour", date.day)])

        # Calcul des jours fériés
        for annee in listeAnnees:
            dimanche_paques = easter(annee)

            lundi_paques = dimanche_paques + relativedelta(days=+1)
            if 0 in listeCoches:
                SauvegarderDate(_(u"Lundi de Pâques"), lundi_paques)

            ascension = dimanche_paques + relativedelta(days=+39)
            if 1 in listeCoches:
                SauvegarderDate(_(u"Jeudi de l'Ascension"), ascension)

            pentecote = dimanche_paques + relativedelta(days=+50)
            if 2 in listeCoches:
                SauvegarderDate(_(u"Lundi de Pentecôte"), pentecote)

        DB.Close()
        self.EndModal(wx.ID_OK)


if __name__ == _(u"__main__"):
    app = wx.App(0)
    dlg = MyDialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
