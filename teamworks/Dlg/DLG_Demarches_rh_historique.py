#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Historique CRH-27 d'une démarche RH, en lecture seule."""

import wx

from application.bootstrap.hr_case_history_factory import HrCaseHistoryRuntimeFactory
from domain.hr_connections import HrCaseStatus, HrEventKind
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


_EVENT_LABELS = {
    HrEventKind.CASE_CREATED: _(u"Dossier créé"),
    HrEventKind.CASE_STATUS_CHANGED: _(u"Statut modifié"),
    HrEventKind.DOCUMENT_ADDED: _(u"Document ajouté"),
    HrEventKind.DOCUMENT_REMOVED: _(u"Document retiré"),
    HrEventKind.EXPORT_GENERATED: _(u"Export généré"),
    HrEventKind.RETURN_IMPORTED: _(u"Retour importé"),
    HrEventKind.SYNC_STARTED: _(u"Synchronisation démarrée"),
    HrEventKind.SYNC_SUCCEEDED: _(u"Synchronisation réussie"),
    HrEventKind.SYNC_FAILED: _(u"Synchronisation en échec"),
    HrEventKind.CONNECTOR_CONFIGURATION_CHANGED: _(u"Configuration modifiée"),
}

_FIELD_LABELS = {
    "from_status": _(u"Statut précédent"),
    "to_status": _(u"Nouveau statut"),
}

_STATUS_VALUE_LABELS = {
    status.value: label
    for status, label in {
        HrCaseStatus.TODO: _(u"À faire"),
        HrCaseStatus.PREPARED: _(u"Préparé"),
        HrCaseStatus.SUBMITTED: _(u"Transmis"),
        HrCaseStatus.ACCEPTED: _(u"Accepté"),
        HrCaseStatus.ANOMALY: _(u"Anomalie"),
        HrCaseStatus.REGULARIZATION: _(u"Régularisation"),
        HrCaseStatus.CANCELLED: _(u"Annulé"),
    }.items()
}


def _format_datetime(value):
    return value.strftime("%d/%m/%Y %H:%M %z")


def _format_field(field):
    label = _FIELD_LABELS.get(field.key, field.key.replace("_", " "))
    value = _STATUS_VALUE_LABELS.get(field.value, field.value)
    return u"%s : %s" % (label, value)


def _format_fields(row):
    if not row.fields:
        return u"—"
    return u" · ".join(_format_field(field) for field in row.fields)


class Dialog(wx.Dialog):
    """Journal append-only d'une démarche, sans action ni persistance directe."""

    def __init__(self, parent, case_id, runtime_factory=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Historique de la démarche RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        factory = runtime_factory or HrCaseHistoryRuntimeFactory
        self._runtime = factory().create()
        self._history = self._runtime.build(case_id=case_id)

        self.title = wx.StaticText(self, -1, _(u"Historique de la démarche RH"))
        title_font = self.title.GetFont()
        title_font.SetPointSize(max(title_font.GetPointSize() + 3, 11))
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)
        self.title.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        self.summary = wx.StaticText(
            self,
            -1,
            _(u"%d événement(s), dont %d changement(s) de statut")
            % (
                self._history.total_count,
                self._history.status_change_count,
            ),
        )
        self.summary.SetForegroundColour(
            UTILS_Interface.GetToken("on_surface_variant")
        )

        self.list = wx.ListCtrl(
            self,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
        )
        self.list.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.list.SetTextColour(UTILS_Interface.GetToken("on_surface"))
        columns = (
            (_(u"Date"), 170),
            (_(u"Événement"), 210),
            (_(u"Acteur"), 150),
            (_(u"Source"), 150),
            (_(u"Détail"), 420),
        )
        for index, (label, width) in enumerate(columns):
            self.list.InsertColumn(
                index,
                label,
                width=UTILS_Styles.Scale(width, minimum=80),
            )

        for row in self._history.rows:
            values = (
                _format_datetime(row.occurred_at),
                _EVENT_LABELS.get(row.kind, row.kind.value),
                row.actor_ref or u"—",
                row.source or u"—",
                _format_fields(row),
            )
            item = self.list.InsertItem(self.list.GetItemCount(), values[0])
            for column, value in enumerate(values[1:], 1):
                self.list.SetItem(item, column, value)

        if self._history.is_empty:
            self.empty = wx.StaticText(
                self,
                -1,
                _(
                    u"Aucun événement n'est encore enregistré pour cette démarche. "
                    u"Le journal affichera notamment les futures transitions de statut."
                ),
            )
            self.empty.SetForegroundColour(
                UTILS_Interface.GetToken("on_surface_variant")
            )
        else:
            self.empty = None

        close = wx.Button(self, wx.ID_CLOSE, _(u"Fermer"))
        close.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE))

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        heading = wx.BoxSizer(wx.VERTICAL)
        heading.Add(self.title, 0, wx.BOTTOM, gap)
        heading.Add(self.summary, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(heading, 0, wx.EXPAND | wx.ALL, page_gap)
        if self.empty is not None:
            sizer.Add(
                self.empty,
                0,
                wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                page_gap,
            )
        sizer.Add(
            self.list,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        sizer.Add(
            close,
            0,
            wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        self.SetSizer(sizer)
        self.SetMinSize(
            (
                UTILS_Styles.Scale(1120, minimum=860),
                UTILS_Styles.Scale(560, minimum=440),
            )
        )
        self.CentreOnParent()
