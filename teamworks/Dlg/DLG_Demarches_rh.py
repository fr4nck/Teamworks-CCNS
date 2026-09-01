#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Cockpit CRH-24 des démarches RH, strictement en lecture seule.

L'écran consomme la façade applicative CRH-23. Il ne connaît ni GestionDB, ni les
repositories, ni l'identité logique de la structure et ne déclenche aucune
transition de workflow ou communication externe.
"""

from datetime import date

import wx

from application.bootstrap.hr_case_dashboard_factory import HrCaseDashboardRuntimeFactory
from domain.hr_connections import ExchangeStatus, HrCaseStatus, HrCaseSubjectKind
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


_STATUS_LABELS = {
    HrCaseStatus.TODO: _(u"À faire"),
    HrCaseStatus.PREPARED: _(u"Préparé"),
    HrCaseStatus.SUBMITTED: _(u"Transmis"),
    HrCaseStatus.ACCEPTED: _(u"Accepté"),
    HrCaseStatus.ANOMALY: _(u"Anomalie"),
    HrCaseStatus.REGULARIZATION: _(u"Régularisation"),
    HrCaseStatus.CANCELLED: _(u"Annulé"),
}

_EXCHANGE_LABELS = {
    ExchangeStatus.NOT_APPLICABLE: _(u"Non applicable"),
    ExchangeStatus.NOT_STARTED: _(u"Non commencé"),
    ExchangeStatus.READY: _(u"Prêt"),
    ExchangeStatus.IN_PROGRESS: _(u"En cours"),
    ExchangeStatus.SUCCEEDED: _(u"Réussi"),
    ExchangeStatus.FAILED: _(u"Échec"),
}


def _format_date(value):
    return value.strftime("%d/%m/%Y") if value is not None else u"—"


def _subject_label(row):
    if row.subject_kind is HrCaseSubjectKind.STRUCTURE:
        return _(u"Structure")
    return _(u"Salarié : %s") % row.subject_identifier


def _attention_label(row):
    labels = []
    if row.overdue:
        labels.append(_(u"Échéance dépassée"))
    if row.business_attention:
        labels.append(_(u"Attention métier"))
    if row.technical_attention:
        labels.append(_(u"Échec technique"))
    if row.configuration_attention:
        labels.append(_(u"Organisme à configurer"))
    return u" · ".join(labels) if labels else u"—"


def _organization_label(row):
    if row.organization_label:
        return row.organization_label
    return _(u"%s (non configuré)") % row.organization_code


def _pieces_label(row):
    if row.expected_document_count <= 0:
        return u"0"
    return u"%d (%d oblig.)" % (
        row.expected_document_count,
        row.required_document_count,
    )


class CounterPanel(wx.Panel):
    """Petit compteur descriptif sans logique métier propre."""

    def __init__(self, parent, label):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_low"))
        self.value = wx.StaticText(self, -1, u"0")
        self.value.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        value_font = self.value.GetFont()
        value_font.SetPointSize(max(value_font.GetPointSize() + 4, 12))
        value_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.value.SetFont(value_font)

        self.label = wx.StaticText(self, -1, label)
        self.label.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.value, 0, wx.BOTTOM, max(2, gap // 2))
        sizer.Add(self.label, 0)
        self.SetSizer(sizer)

    def SetValue(self, value):
        self.value.SetLabel(str(value))
        self.Layout()


class DetailDialog(wx.Dialog):
    """Détail descriptif d'une ligne du cockpit, sans action de workflow."""

    def __init__(self, parent, row):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Détail de la démarche RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        grid = wx.FlexGridSizer(cols=2, vgap=8, hgap=12)
        grid.AddGrowableCol(1, 1)
        fields = (
            (_(u"Démarche"), row.case_type_label),
            (_(u"Sujet"), _subject_label(row)),
            (_(u"Organisme"), _organization_label(row)),
            (_(u"Ouverture"), _format_date(row.opened_on)),
            (_(u"Échéance"), _format_date(row.due_on)),
            (_(u"Statut métier"), _STATUS_LABELS.get(row.status, row.status.value)),
            (_(u"Échange"), _EXCHANGE_LABELS.get(row.exchange_status, row.exchange_status.value)),
            (_(u"Pièces attendues"), _pieces_label(row)),
            (_(u"Attention"), _attention_label(row)),
        )
        for label, value in fields:
            label_ctrl = wx.StaticText(self, -1, label)
            label_ctrl.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))
            value_ctrl = wx.StaticText(self, -1, value)
            value_ctrl.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
            grid.Add(label_ctrl, 0, wx.ALIGN_TOP)
            grid.Add(value_ctrl, 1, wx.EXPAND)

        notes = wx.TextCtrl(
            self,
            value=u"\n\n".join(
                text
                for text in (
                    (_(u"Résultat :\n%s") % row.result) if row.result else u"",
                    (_(u"Commentaire :\n%s") % row.comment) if row.comment else u"",
                )
                if text
            )
            or _(u"Aucun résultat ou commentaire enregistré."),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
        )
        notes.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        notes.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        close = wx.Button(self, wx.ID_CLOSE, _(u"Fermer"))
        close.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE))

        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(notes, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(close, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        self.SetSizer(sizer)
        self.SetMinSize(
            (
                UTILS_Styles.Scale(650, minimum=560),
                UTILS_Styles.Scale(480, minimum=400),
            )
        )
        self.CentreOnParent()


class Dialog(wx.Dialog):
    """Cockpit structure CRH-24, lecture seule sur la base Teamworks active."""

    def __init__(self, parent, runtime_factory=None, today_provider=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Démarches RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._runtime_factory = runtime_factory or HrCaseDashboardRuntimeFactory
        self._today_provider = today_provider or date.today
        self._runtime = self._runtime_factory().create()
        self._rows = []
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.title = wx.StaticText(self, -1, _(u"Cockpit des démarches RH"))
        title_font = self.title.GetFont()
        title_font.SetPointSize(max(title_font.GetPointSize() + 3, 11))
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)
        self.title.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        self.subtitle = wx.StaticText(
            self,
            -1,
            _(u"Vue descriptive des démarches, échéances et anomalies de la structure."),
        )
        self.subtitle.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))
        self.snapshot = wx.StaticText(self, -1, u"")
        self.snapshot.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        self.counters = {
            "open": CounterPanel(self, _(u"Ouverts")),
            "attention": CounterPanel(self, _(u"À surveiller")),
            "overdue": CounterPanel(self, _(u"En retard")),
            "anomaly": CounterPanel(self, _(u"Anomalies")),
            "technical": CounterPanel(self, _(u"Échecs techniques")),
            "orphan": CounterPanel(self, _(u"Organismes à configurer")),
        }

        self.list = wx.ListCtrl(
            self,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
        )
        self.list.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.list.SetTextColour(UTILS_Interface.GetToken("on_surface"))
        columns = (
            (_(u"Démarche"), 190),
            (_(u"Sujet"), 150),
            (_(u"Organisme"), 190),
            (_(u"Échéance"), 105),
            (_(u"Statut"), 120),
            (_(u"Échange"), 115),
            (_(u"Pièces"), 100),
            (_(u"Attention"), 250),
        )
        for index, (label, width) in enumerate(columns):
            self.list.InsertColumn(
                index,
                label,
                width=UTILS_Styles.Scale(width, minimum=70),
            )

        self.refresh = wx.Button(self, -1, _(u"Actualiser"))
        self.details = wx.Button(self, -1, _(u"Voir le détail"))
        self.close = wx.Button(self, wx.ID_CLOSE, _(u"Fermer"))
        self.details.Enable(False)

        self.refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
        self.details.Bind(wx.EVT_BUTTON, self.OnDetails)
        self.close.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE))
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDetails)

        self._layout()
        self.RefreshData()
        self.SetMinSize(
            (
                UTILS_Styles.Scale(1180, minimum=920),
                UTILS_Styles.Scale(650, minimum=520),
            )
        )
        self.CentreOnParent()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")

        heading = wx.BoxSizer(wx.VERTICAL)
        heading.Add(self.title, 0, wx.BOTTOM, max(2, gap // 2))
        heading.Add(self.subtitle, 0, wx.BOTTOM, max(2, gap // 2))
        heading.Add(self.snapshot, 0)

        counters = wx.FlexGridSizer(cols=6, vgap=gap, hgap=gap)
        for panel in self.counters.values():
            counters.Add(panel, 1, wx.EXPAND | wx.ALL, gap)
        for column in range(6):
            counters.AddGrowableCol(column, 1)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(self.refresh, 0, wx.RIGHT, gap)
        buttons.Add(self.details, 0, wx.RIGHT, gap)
        buttons.AddStretchSpacer(1)
        buttons.Add(self.close, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(heading, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(counters, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)

    def RefreshData(self):
        as_of = self._today_provider()
        if not isinstance(as_of, date):
            raise TypeError("La date de référence du cockpit RH est invalide.")
        dashboard = self._runtime.build(as_of=as_of)
        self._rows = list(dashboard.rows)
        self.snapshot.SetLabel(_(u"Situation au %s") % _format_date(dashboard.as_of))

        self.counters["open"].SetValue(dashboard.open_count)
        self.counters["attention"].SetValue(dashboard.attention_count)
        self.counters["overdue"].SetValue(dashboard.overdue_count)
        self.counters["anomaly"].SetValue(
            dashboard.anomaly_count + dashboard.regularization_count
        )
        self.counters["technical"].SetValue(dashboard.exchange_failed_count)
        self.counters["orphan"].SetValue(dashboard.orphan_organization_count)

        self.list.Freeze()
        try:
            self.list.DeleteAllItems()
            for row in self._rows:
                values = (
                    row.case_type_label,
                    _subject_label(row),
                    _organization_label(row),
                    _format_date(row.due_on),
                    _STATUS_LABELS.get(row.status, row.status.value),
                    _EXCHANGE_LABELS.get(row.exchange_status, row.exchange_status.value),
                    _pieces_label(row),
                    _attention_label(row),
                )
                item = self.list.InsertItem(self.list.GetItemCount(), values[0])
                for column, value in enumerate(values[1:], 1):
                    self.list.SetItem(item, column, value)

                if row.business_attention or row.technical_attention:
                    self.list.SetItemTextColour(item, UTILS_Interface.GetToken("danger"))
                elif row.needs_attention:
                    self.list.SetItemTextColour(item, UTILS_Interface.GetToken("warning"))
                elif row.status in {HrCaseStatus.ACCEPTED, HrCaseStatus.CANCELLED}:
                    self.list.SetItemTextColour(
                        item,
                        UTILS_Interface.GetToken("on_surface_variant"),
                    )
        finally:
            self.list.Thaw()
        self.details.Enable(False)
        self.Layout()

    def OnRefresh(self, event):
        try:
            self.RefreshData()
        except Exception as exc:
            wx.MessageBox(
                _(u"Le cockpit des démarches RH n'a pas pu être actualisé.\n\n%s")
                % str(exc),
                _(u"Démarches RH"),
                wx.OK | wx.ICON_ERROR,
                self,
            )

    def OnSelection(self, event):
        self.details.Enable(self.list.GetFirstSelected() >= 0)
        event.Skip()

    def OnDetails(self, event):
        index = self.list.GetFirstSelected()
        if index < 0 or index >= len(self._rows):
            return
        dlg = DetailDialog(self, self._rows[index])
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
