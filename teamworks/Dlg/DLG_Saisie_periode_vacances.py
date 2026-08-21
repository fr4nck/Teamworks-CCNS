#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
import datetime
import FonctionsPerso
if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else:
    from wx import DatePickerCtrl, DP_DROPDOWN


def _dip(window, width, height):
    try:
        return window.FromDIP(wx.Size(width, height))
    except Exception:
        return wx.Size(width, height)


def _section_title(parent, label):
    ctrl = wx.StaticText(parent, -1, label)
    font = ctrl.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(max(10, font.GetPointSize() + 1))
    ctrl.SetFont(font)
    ctrl.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
    return ctrl


class Dialog(wx.Dialog):
    def __init__(self, parent, title="", IDperiode=0):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.panel_base = wx.Panel(self, -1)
        self.panel_base.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre_periode = _section_title(self.panel_base, _(u"Nom de la période"))
        choices = [_(u"Février"), _(u"Pâques"), _(u"Eté"), _(u"Toussaint"), _(u"Noël")]
        self.label_nom = wx.StaticText(self.panel_base, -1, _(u"Nom"))
        self.choice_nom = wx.Choice(self.panel_base, -1, choices=choices)
        self.choice_nom.SetMinSize(_dip(self, 180, -1))
        self.label_annee = wx.StaticText(self.panel_base, -1, _(u"Année"))
        self.text_annee = wx.TextCtrl(self.panel_base, -1, "", style=wx.TE_CENTRE)
        self.text_annee.SetMinSize(_dip(self, 110, -1))

        self.titre_dates = _section_title(self.panel_base, _(u"Dates de la période"))
        self.label_dateDebut = wx.StaticText(self.panel_base, -1, _(u"Du"))
        self.datepicker_dateDebut = DatePickerCtrl(self.panel_base, -1, style=DP_DROPDOWN)
        self.label_dateFin = wx.StaticText(self.panel_base, -1, _(u"Au"))
        self.datepicker_dateFin = DatePickerCtrl(self.panel_base, -1, style=DP_DROPDOWN)

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self.panel_base,
            id=wx.ID_OK,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self.panel_base,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )

        self.IDperiode = IDperiode
        if IDperiode != 0:
            self.Importation()

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des périodes de vacances"))
        self.choice_nom.SetToolTip(wx.ToolTip(_(u"Choisissez ici le nom de la période")))
        self.text_annee.SetToolTip(wx.ToolTip(_(u"Saisissez ici l'année de la période. Ex. : '2008'")))
        self.datepicker_dateDebut.SetToolTip(wx.ToolTip(_(u"Saisissez ici la date de début de la période")))
        self.datepicker_dateFin.SetToolTip(wx.ToolTip(_(u"Saisissez ici la date de fin de la période")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour annuler la saisie")))
        self.SetMinSize(_dip(self, 520, 390))
        self.SetSize(_dip(self, 650, 460))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)

        sizer_periode = wx.BoxSizer(wx.VERTICAL)
        sizer_periode.Add(self.titre_periode, 0, wx.BOTTOM, 8)
        row_periode = wx.BoxSizer(wx.HORIZONTAL)
        row_periode.Add(self.label_nom, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row_periode.Add(self.choice_nom, 1, wx.RIGHT, 16)
        row_periode.Add(self.label_annee, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row_periode.Add(self.text_annee, 0)
        sizer_periode.Add(row_periode, 0, wx.EXPAND)
        sizer_base.Add(sizer_periode, 0, wx.EXPAND | wx.ALL, 16)

        sizer_dates = wx.BoxSizer(wx.VERTICAL)
        sizer_dates.Add(self.titre_dates, 0, wx.BOTTOM, 8)
        row_dates = wx.BoxSizer(wx.HORIZONTAL)
        row_dates.Add(self.label_dateDebut, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row_dates.Add(self.datepicker_dateDebut, 1, wx.RIGHT, 16)
        row_dates.Add(self.label_dateFin, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row_dates.Add(self.datepicker_dateFin, 1)
        sizer_dates.Add(row_dates, 0, wx.EXPAND)
        sizer_base.Add(sizer_dates, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

        sizer_boutons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_boutons.Add(self.bouton_aide, 0, wx.RIGHT, 8)
        sizer_boutons.AddStretchSpacer(1)
        sizer_boutons.Add(self.bouton_ok, 0, wx.RIGHT, 8)
        sizer_boutons.Add(self.bouton_annuler, 0)
        sizer_base.Add(sizer_boutons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

        self.panel_base.SetSizer(sizer_base)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(outer)
        self.Layout()
        self.CenterOnScreen()

    def Importation(self):
        DB = GestionDB.DB()
        req = "SELECT * FROM periodes_vacances WHERE IDperiode=%d" % self.IDperiode
        DB.ExecuterReq(req)
        resultats = DB.ResultatReq()
        DB.Close()
        if not resultats:
            return
        donnees = resultats[0]
        self.SelectChoice(self.choice_nom, donnees[1])
        self.text_annee.SetValue(str(donnees[2]))
        jour = int(donnees[3][8:10])
        mois = int(donnees[3][5:7]) - 1
        annee = int(donnees[3][:4])
        date = wx.DateTime()
        date.Set(jour, mois, annee)
        self.datepicker_dateDebut.SetValue(date)
        jour = int(donnees[4][8:10])
        mois = int(donnees[4][5:7]) - 1
        annee = int(donnees[4][:4])
        date = wx.DateTime()
        date.Set(jour, mois, annee)
        self.datepicker_dateFin.SetValue(date)

    def SelectChoice(self, controle, data):
        nbreItems = controle.GetCount()
        index = 0
        for item in range(nbreItems):
            if controle.GetString(index) == data:
                controle.SetSelection(index)
                return
            index += 1

    def GetChoiceValue(self, controle):
        selection = controle.GetSelection()
        if selection != -1:
            IDselection = controle.GetString(selection)
        else:
            IDselection = None
        return IDselection

    def Sauvegarde(self):
        """ Sauvegarde des données dans la base de données """
        varNom = self.GetChoiceValue(self.choice_nom)
        varAnnee = self.text_annee.GetValue()
        varDateDebut = self.datepicker_dateDebut.GetValue()
        varTxtDateDebut = str(datetime.date(varDateDebut.GetYear(), varDateDebut.GetMonth() + 1, varDateDebut.GetDay()))
        varDateFin = self.datepicker_dateFin.GetValue()
        varTxtDateFin = str(datetime.date(varDateFin.GetYear(), varDateFin.GetMonth() + 1, varDateFin.GetDay()))

        DB = GestionDB.DB()
        listeDonnees = [
            ("nom", varNom),
            ("annee", varAnnee),
            ("date_debut", varTxtDateDebut),
            ("date_fin", varTxtDateFin),
        ]
        if self.IDperiode == 0:
            newID = DB.ReqInsert("periodes_vacances", listeDonnees)
            ID = newID
        else:
            DB.ReqMAJ("periodes_vacances", listeDonnees, "IDperiode", self.IDperiode)
            ID = self.IDperiode
        DB.Commit()
        DB.Close()
        return ID

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lespriodesdevacances")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        """ Validation des données saisies """
        valeur = self.GetChoiceValue(self.choice_nom)
        if valeur == None:
            dlg = wx.MessageDialog(self, _(u"Vous devez sélectionner un nom de période dans la liste proposée !"), "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.choice_nom.SetFocus()
            return

        valeur = self.text_annee.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez saisir une année valide."), "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.text_annee.SetFocus()
            return
        incoherences = ""
        for lettre in valeur:
            if lettre not in "0123456789.":
                incoherences += "'" + lettre + "', "
        if len(incoherences) != 0:
            dlg = wx.MessageDialog(self, _(u"L'année que vous avez saisie n'est pas correcte."), "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.text_annee.SetFocus()
            return
        valeur = int(valeur)
        if valeur < 1000 or valeur > 3000:
            dlg = wx.MessageDialog(self, _(u"L'année que vous avez saisie n'est pas correcte."), "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.text_annee.SetFocus()
            return

        date_debut = self.datepicker_dateDebut.GetValue()
        date_fin = self.datepicker_dateFin.GetValue()
        if date_debut > date_fin:
            dlg = wx.MessageDialog(self, _(u"La date de fin de vacances doit être supérieure à la date de début !"), "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.datepicker_dateFin.SetFocus()
            return

        self.Sauvegarde()
        if FonctionsPerso.FrameOuverte("panel_config_periodes_vacs") != None:
            self.GetParent().MAJ_ListCtrl()

        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, "", IDperiode=1)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
