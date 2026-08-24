#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sélection de période harmonisée avec la charte Teamworks."""

import calendar
import datetime

import wx

import GestionDB
from Ctrl import CTRL_Bouton_image, CTRL_Section, CTRL_Texte
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _

if "phoenix" in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else:
    from wx import DatePickerCtrl, DP_DROPDOWN


class ListCtrl_vacances(wx.ListCtrl):
    """Périodes enregistrées, sans liste virtuelle ni zébrage décoratif."""

    def __init__(self, parent):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES,
        )
        self.parent = parent
        self.rows = []
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.InsertColumn(0, _(u"Période"))
        self.InsertColumn(1, _(u"Dates"))
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemSelected)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Remplissage()

    def Remplissage(self):
        self.DeleteAllItems()
        DB = GestionDB.DB()
        req = """SELECT IDperiode, nom, annee, date_debut, date_fin
        FROM periodes_vacances ORDER BY date_debut DESC;"""
        DB.ExecuterReq(req)
        self.rows = DB.ResultatReq()
        DB.Close()
        for index, (IDperiode, nom, annee, date_debut, date_fin) in enumerate(self.rows):
            self.InsertItem(index, u"%s %s" % (nom or "", annee or ""))
            self.SetItem(
                index,
                1,
                _(u"Du %s au %s") % (self.DateEngFr(date_debut), self.DateEngFr(date_fin)),
            )
            self.SetItemData(index, index)
        self._ajuster_colonnes()

    def MAJListeCtrl(self):
        self.Remplissage()

    def DateEngFr(self, textDate):
        if not textDate:
            return ""
        return "%s/%s/%s" % (textDate[8:10], textDate[5:7], textDate[:4])

    def _ajuster_colonnes(self):
        largeur = max(360, self.GetClientSize().width)
        self.SetColumnWidth(0, max(150, int(largeur * 0.38)))
        self.SetColumnWidth(1, max(200, largeur - self.GetColumnWidth(0) - 8))

    def OnSize(self, event):
        self._ajuster_colonnes()
        event.Skip()

    def OnItemSelected(self, event):
        index = self.GetFirstSelected()
        if index == -1 or index >= len(self.rows):
            return
        IDperiode, nom, annee, date_debut, date_fin = self.rows[index]
        debut = datetime.date(int(date_debut[:4]), int(date_debut[5:7]), int(date_debut[8:10]))
        fin = datetime.date(int(date_fin[:4]), int(date_fin[5:7]), int(date_fin[8:10]))
        self.parent.ctrl_mois.SetSelection(0)
        self.parent.ctrl_annee.SetSelection(0)
        self.parent.SetDates(debut, fin)
        event.Skip()


class SelectionPeriode(wx.Dialog):
    """Renvoie la période avec ``GetDates`` et conserve l'API historique."""

    def __init__(self, parent, id=-1, title=_(u"Sélection d'une période"), nomFichier=""):
        wx.Dialog.__init__(
            self,
            parent,
            id,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.introduction = CTRL_Texte.BodySecondary(
            self,
            _(u"Choisissez une période de vacances existante, un mois, une année ou saisissez directement les dates."),
        )
        self.section_vacances = CTRL_Section.Section(self, titre=_(u"Périodes de vacances"), niveau=2)
        self.section_calendrier = CTRL_Section.Section(self, titre=_(u"Mois et année"), niveau=2)
        self.section_dates = CTRL_Section.Section(self, titre=_(u"Dates"), niveau=2)

        self.ctrl_vacances = ListCtrl_vacances(self.section_vacances.GetContentPanel())
        self.ctrl_vacances.SetMinSize((-1, UTILS_Styles.Scale(150)))
        vac_sizer = wx.BoxSizer(wx.VERTICAL)
        vac_sizer.Add(self.ctrl_vacances, 1, wx.EXPAND)
        self.section_vacances.GetContentPanel().SetSizer(vac_sizer)

        self.listeMois = [
            u"", _(u"Janvier"), _(u"Février"), _(u"Mars"), _(u"Avril"), _(u"Mai"), _(u"Juin"),
            _(u"Juillet"), _(u"Août"), _(u"Septembre"), _(u"Octobre"), _(u"Novembre"), _(u"Décembre"),
        ]
        self.listeAnnees = [""] + [str(annee) for annee in range(2000, 2050)]
        cal = self.section_calendrier.GetContentPanel()
        self.label_mois = CTRL_Texte.Label(cal, _(u"Mois"))
        self.ctrl_mois = wx.Choice(cal, -1, choices=self.listeMois)
        self.label_annee = CTRL_Texte.Label(cal, _(u"Année"))
        self.ctrl_annee = wx.Choice(cal, -1, choices=self.listeAnnees)
        self.ctrl_mois.SetSelection(0)
        self.ctrl_annee.SetSelection(0)
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        cal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for label, control in ((self.label_mois, self.ctrl_mois), (self.label_annee, self.ctrl_annee)):
            bloc = wx.BoxSizer(wx.VERTICAL)
            bloc.Add(label, 0, wx.EXPAND)
            bloc.AddSpacer(gap)
            bloc.Add(control, 0, wx.EXPAND)
            cal_sizer.Add(bloc, 1, wx.EXPAND | wx.RIGHT, gap)
        cal.SetSizer(cal_sizer)

        dates = self.section_dates.GetContentPanel()
        self.label_date_debut = CTRL_Texte.Label(dates, _(u"Du"))
        self.ctrl_date_debut = DatePickerCtrl(dates, -1, style=DP_DROPDOWN)
        self.label_date_fin = CTRL_Texte.Label(dates, _(u"Au"))
        self.ctrl_date_fin = DatePickerCtrl(dates, -1, style=DP_DROPDOWN)
        dates_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for label, control in ((self.label_date_debut, self.ctrl_date_debut), (self.label_date_fin, self.ctrl_date_fin)):
            bloc = wx.BoxSizer(wx.VERTICAL)
            bloc.Add(label, 0, wx.EXPAND)
            bloc.AddSpacer(gap)
            bloc.Add(control, 0, wx.EXPAND)
            dates_sizer.Add(bloc, 1, wx.EXPAND | wx.RIGHT, gap)
        dates.SetSizer(dates_sizer)

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"))
        self._layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_CHOICE, self.On_maj_mois, self.ctrl_mois)
        self.Bind(wx.EVT_CHOICE, self.On_maj_annee, self.ctrl_annee)
        UTILS_Styles.ApplyWindowProfile(self, "standard")

    def _layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        actions_gap = UTILS_Styles.GetLayoutSpacing("control_gap")
        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, actions_gap)
        actions.Add(self.bouton_annuler, 0)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.introduction, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.AddSpacer(gap)
        sizer.Add(self.section_vacances, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, padding)
        sizer.AddSpacer(gap)
        sizer.Add(self.section_calendrier, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, padding)
        sizer.AddSpacer(gap)
        sizer.Add(self.section_dates, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, padding)
        sizer.AddSpacer(gap)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)

    def GetDates(self):
        return self.GetDatePickerValue(self.ctrl_date_debut), self.GetDatePickerValue(self.ctrl_date_fin)

    def SetDates(self, date_debut=None, date_fin=None):
        if date_debut is not None:
            self.SetDatePicker(self.ctrl_date_debut, date_debut)
        if date_fin is not None:
            self.SetDatePicker(self.ctrl_date_fin, date_fin)

    def SetDatePicker(self, controle, date):
        date_wx = wx.DateTime()
        date_wx.Set(int(date.day), int(date.month) - 1, int(date.year))
        controle.SetValue(date_wx)

    def GetDatePickerValue(self, controle):
        date_tmp = controle.GetValue()
        return datetime.date(date_tmp.GetYear(), date_tmp.GetMonth() + 1, date_tmp.GetDay())

    def OnBoutonOk(self, event):
        debut, fin = self.GetDates()
        if fin < debut:
            wx.MessageBox(
                _(u"La date de fin doit être postérieure ou égale à la date de début."),
                _(u"Période invalide"),
                wx.OK | wx.ICON_WARNING,
            )
            return
        self.EndModal(wx.ID_OK)

    def ctrl_mois_EvtComboBox(self, event):
        self.On_maj_mois(event)

    def On_maj_mois(self, event):
        mois = self.ctrl_mois.GetSelection()
        if mois <= 0:
            return
        annee_index = self.ctrl_annee.GetSelection()
        if annee_index <= 0:
            annee = datetime.date.today().year
            self.ctrl_annee.SetStringSelection(str(annee))
        else:
            annee = int(self.listeAnnees[annee_index])
        self.SetDates(
            datetime.date(annee, mois, 1),
            datetime.date(annee, mois, calendar.monthrange(annee, mois)[1]),
        )

    def ctrl_annee_EvtComboBox(self, event):
        self.On_maj_annee(event)

    def On_maj_annee(self, event):
        index = self.ctrl_annee.GetSelection()
        if index <= 0:
            return
        annee = int(self.listeAnnees[index])
        mois = self.ctrl_mois.GetSelection()
        if mois > 0:
            self.SetDates(
                datetime.date(annee, mois, 1),
                datetime.date(annee, mois, calendar.monthrange(annee, mois)[1]),
            )
        else:
            self.SetDates(datetime.date(annee, 1, 1), datetime.date(annee, 12, 31))

    def GetPersonnesPresentes(self):
        date_debut, date_fin = self.GetDates()
        DB = GestionDB.DB()
        req = """SELECT IDpersonne FROM presences
        WHERE date>='%s' AND date<='%s' GROUP BY IDpersonne""" % (date_debut, date_fin)
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()
        return [row[0] for row in rows]


if __name__ == "__main__":
    app = wx.App(0)
    dlg = SelectionPeriode(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
