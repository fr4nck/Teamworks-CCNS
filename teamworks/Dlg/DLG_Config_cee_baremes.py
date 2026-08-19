#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from decimal import Decimal, InvalidOperation

import wx
if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN, EVT_DATE_CHANGED
else:
    from wx import DatePickerCtrl, DP_DROPDOWN
    EVT_DATE_CHANGED = wx.EVT_DATE_CHANGED

import GestionDB
from Utils import UTILS_CEE_baremes


QUALIFICATIONS = (
    ("BAFA_HOLDER", u"BAFA titulaire"),
    ("BAFA_TRAINEE", u"BAFA stagiaire"),
    ("UNQUALIFIED", u"Non diplômé"),
    ("EQUIVALENT", u"Qualification équivalente"),
    ("BAFD_HOLDER", u"BAFD titulaire"),
    ("BAFD_TRAINEE", u"BAFD stagiaire"),
)


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title=u"Barèmes employeur CEE", size=(570, 440))
        panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            panel,
            label=(u"Définissez les montants bruts journaliers internes par qualification. "
                   u"Le minimum légal CEE est contrôlé séparément à la date du contrat."),
        )
        intro.Wrap(520)
        main.Add(intro, 0, wx.EXPAND | wx.ALL, 12)

        date_row = wx.BoxSizer(wx.HORIZONTAL)
        date_row.Add(wx.StaticText(panel, label=u"Date d'effet :"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.date_effet = DatePickerCtrl(panel, style=DP_DROPDOWN)
        date_row.Add(self.date_effet, 0)
        main.Add(date_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        box = wx.StaticBoxSizer(wx.VERTICAL, panel, u"Montants bruts par jour")
        grid = wx.FlexGridSizer(rows=len(QUALIFICATIONS), cols=3, vgap=7, hgap=8)
        grid.AddGrowableCol(0, 1)
        self.controls = {}
        for code, label in QUALIFICATIONS:
            grid.Add(wx.StaticText(panel, label=label + u" :"), 0, wx.ALIGN_CENTER_VERTICAL)
            ctrl = wx.TextCtrl(panel, size=(100, -1))
            self.controls[code] = ctrl
            grid.Add(ctrl, 0)
            grid.Add(wx.StaticText(panel, label=u"€ brut / jour"), 0, wx.ALIGN_CENTER_VERTICAL)
        box.Add(grid, 1, wx.EXPAND | wx.ALL, 10)
        main.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        note = wx.StaticText(
            panel,
            label=(u"Un champ vide ne crée pas de nouveau barème. Les anciens barèmes sont conservés "
                   u"pour que les contrats passés restent calculables avec la valeur applicable à leur date."),
        )
        note.Wrap(520)
        main.Add(note, 0, wx.EXPAND | wx.ALL, 12)

        # Sous wxWidgets 3.3.x, tous les contrôles gérés par le sizer d'un panel
        # doivent avoir ce même panel comme parent. CreateStdDialogButtonSizer()
        # créerait ici les boutons avec le dialogue comme parent, ce qui déclenche
        # une assertion SetContainingWindow au moment de l'ouverture.
        buttons = wx.StdDialogButtonSizer()
        self.bouton_ok = wx.Button(panel, wx.ID_OK)
        self.bouton_annuler = wx.Button(panel, wx.ID_CANCEL)
        buttons.AddButton(self.bouton_ok)
        buttons.AddButton(self.bouton_annuler)
        buttons.Realize()

        main.AddStretchSpacer()
        main.Add(buttons, 0, wx.EXPAND | wx.ALL, 12)
        panel.SetSizer(main)

        self.bouton_ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.date_effet.Bind(EVT_DATE_CHANGED, self.OnDateChanged)
        self._load_applicable_rates()
        self.CentreOnParent()

    def _get_date(self):
        value = self.date_effet.GetValue()
        return datetime.date(value.GetYear(), value.GetMonth() + 1, value.GetDay())

    def _load_applicable_rates(self):
        DB = GestionDB.DB()
        try:
            reference_date = self._get_date()
            for code, label in QUALIFICATIONS:
                ctrl = self.controls[code]
                ctrl.SetValue("")
                rate = UTILS_CEE_baremes.GetApplicableRate(DB, code, reference_date)
                if rate is not None:
                    ctrl.SetValue(str(rate["montant_journalier"]).replace(".", ","))
        finally:
            DB.Close()

    def OnDateChanged(self, event):
        self._load_applicable_rates()
        if event:
            event.Skip()

    @staticmethod
    def _parse_amount(text):
        text = text.strip().replace(",", ".")
        if not text:
            return None
        try:
            value = Decimal(text)
        except InvalidOperation:
            raise ValueError(u"Le montant doit être un nombre.")
        if value <= 0:
            raise ValueError(u"Le montant doit être strictement positif.")
        return value

    def OnOk(self, event):
        values = {}
        try:
            for code, label in QUALIFICATIONS:
                values[code] = self._parse_amount(self.controls[code].GetValue())
        except ValueError as err:
            wx.MessageBox(str(err), u"Barème CEE invalide", wx.OK | wx.ICON_ERROR, parent=self)
            return

        DB = GestionDB.DB()
        try:
            date_effet = self._get_date()
            for code, value in values.items():
                if value is not None:
                    UTILS_CEE_baremes.SaveRate(DB, code, value, date_effet)
            DB.Commit()
        finally:
            DB.Close()
        self.EndModal(wx.ID_OK)
