#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Checklist CRH-32 des pièces attendues d'une démarche RH.

Le dialogue reste une couche de présentation : il charge paresseusement la façade
CRH-31, ne connaît ni GestionDB ni les repositories et n'ouvre aucun fichier.
Une pièce marquée « reçue » signifie seulement qu'une réception administrative a
été enregistrée ; aucune authenticité, validité ou conformité n'est déduite.
"""

from datetime import date, datetime

import wx

from domain.hr_connections import HrCaseDocumentState
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


def _format_date(value):
    return value.strftime("%d/%m/%Y") if value is not None else u"—"


def _parse_date(value):
    text = value.strip()
    if not text:
        raise ValueError("La date de réception de la pièce est obligatoire.")
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        raise ValueError("La date doit être saisie au format JJ/MM/AAAA.")


def _optional_text(value):
    value = value.strip()
    return value or None


def _state_label(row):
    if row.receipt is None:
        return _(u"Non reçue")
    if row.receipt.state is HrCaseDocumentState.RECEIVED:
        return _(u"Reçue")
    if row.receipt.state is HrCaseDocumentState.WITHDRAWN:
        return _(u"Retirée")
    return row.receipt.state.value


class ReceiveDocumentDialog(wx.Dialog):
    """Saisie minimale d'une réception administrative explicite."""

    def __init__(self, parent, row, today):
        if not isinstance(today, date):
            raise TypeError("La date de référence du suivi de pièce RH est invalide.")
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Enregistrer la réception d'une pièce"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self._row = row

        title = wx.StaticText(self, -1, row.expected_document.label)
        title_font = title.GetFont()
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        nature = _(
            u"Pièce obligatoire"
            if row.expected_document.required
            else u"Pièce facultative"
        )
        info = wx.StaticText(
            self,
            -1,
            _(
                u"%s. L'enregistrement constate uniquement une réception administrative ; "
                u"il ne valide ni l'authenticité, ni la validité, ni la conformité de la pièce."
            )
            % nature,
        )
        info.Wrap(UTILS_Styles.Scale(560, minimum=420))
        info.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        self.received_on = wx.TextCtrl(self, value=_format_date(today))
        previous_ref = (
            row.receipt.artifact_ref
            if row.receipt is not None and row.receipt.artifact_ref
            else u""
        )
        self.artifact_ref = wx.TextCtrl(self, value=previous_ref)

        grid = wx.FlexGridSizer(cols=2, vgap=10, hgap=12)
        grid.AddGrowableCol(1, 1)
        grid.Add(
            wx.StaticText(self, -1, _(u"Date de réception")),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        grid.Add(self.received_on, 1, wx.EXPAND)
        grid.Add(
            wx.StaticText(self, -1, _(u"Référence documentaire")),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        grid.Add(self.artifact_ref, 1, wx.EXPAND)

        hint = wx.StaticText(
            self,
            -1,
            _(
                u"Référence facultative : identifiant interne ou référence documentaire opaque. "
                u"Aucun fichier ni chemin local n'est enregistré par cet écran."
            ),
        )
        hint.Wrap(UTILS_Styles.Scale(560, minimum=420))
        hint.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        validate = wx.Button(self, wx.ID_OK, _(u"Continuer"))
        cancel = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))
        validate.SetDefault()
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.AddStretchSpacer(1)
        buttons.Add(cancel, 0, wx.RIGHT, UTILS_Styles.GetLayoutSpacing("field_gap"))
        buttons.Add(validate, 0)

        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(title, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(info, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(hint, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        self.SetSizer(sizer)
        self.SetMinSize(
            (
                UTILS_Styles.Scale(650, minimum=560),
                UTILS_Styles.Scale(340, minimum=300),
            )
        )
        self.CentreOnParent()

    def GetValues(self):
        return (
            _parse_date(self.received_on.GetValue()),
            _optional_text(self.artifact_ref.GetValue()),
        )


class Dialog(wx.Dialog):
    """Checklist des pièces d'une démarche, avec écritures CRH-31 contrôlées."""

    def __init__(
        self,
        parent,
        case_id,
        read_only=False,
        runtime_factory=None,
        today_provider=None,
    ):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Pièces de la démarche RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._case_id = str(case_id).strip()
        if not self._case_id:
            raise ValueError("L'identifiant de la démarche RH est obligatoire.")
        self._read_only = bool(read_only)
        self._runtime_factory = runtime_factory
        self._today_provider = today_provider or date.today
        self._runtime = None
        self._rows = []
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.title = wx.StaticText(self, -1, _(u"Pièces attendues de la démarche"))
        title_font = self.title.GetFont()
        title_font.SetPointSize(max(title_font.GetPointSize() + 3, 11))
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)
        self.title.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        self.subtitle = wx.StaticText(
            self,
            -1,
            _(
                u"Suivi administratif uniquement : « reçue » ne signifie pas vérifiée, "
                u"valide ou conforme."
            ),
        )
        self.subtitle.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))
        self.summary = wx.StaticText(self, -1, u"")
        self.summary.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))
        self.feedback = wx.StaticText(self, -1, u"")
        self.feedback.SetForegroundColour(UTILS_Interface.GetToken("success"))

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
            (_(u"Pièce"), 260),
            (_(u"Caractère"), 110),
            (_(u"État"), 110),
            (_(u"Réception"), 105),
            (_(u"Retrait"), 105),
            (_(u"Référence"), 260),
        )
        for index, (label, width) in enumerate(columns):
            self.list.InsertColumn(
                index,
                label,
                width=UTILS_Styles.Scale(width, minimum=80),
            )

        self.refresh = wx.Button(self, -1, _(u"Actualiser"))
        self.received = wx.Button(self, -1, _(u"Marquer reçue"))
        self.withdraw = wx.Button(self, -1, _(u"Retirer l'état reçue"))
        self.close = wx.Button(self, wx.ID_CLOSE, _(u"Fermer"))
        self.received.Enable(False)
        self.withdraw.Enable(False)

        self.refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
        self.received.Bind(wx.EVT_BUTTON, self.OnReceived)
        self.withdraw.Bind(wx.EVT_BUTTON, self.OnWithdraw)
        self.close.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE))
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelection)

        self._layout()
        self.RefreshData()
        self.SetMinSize(
            (
                UTILS_Styles.Scale(1040, minimum=820),
                UTILS_Styles.Scale(560, minimum=460),
            )
        )
        self.CentreOnParent()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")

        heading = wx.BoxSizer(wx.VERTICAL)
        heading.Add(self.title, 0, wx.BOTTOM, max(2, gap // 2))
        heading.Add(self.subtitle, 0, wx.BOTTOM, max(2, gap // 2))
        heading.Add(self.summary, 0, wx.BOTTOM, max(2, gap // 2))
        heading.Add(self.feedback, 0)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(self.refresh, 0, wx.RIGHT, gap)
        buttons.Add(self.received, 0, wx.RIGHT, gap)
        buttons.Add(self.withdraw, 0, wx.RIGHT, gap)
        buttons.AddStretchSpacer(1)
        buttons.Add(self.close, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(heading, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)

    def _get_runtime(self):
        if self._runtime is not None:
            return self._runtime
        factory = self._runtime_factory
        if factory is None:
            from application.bootstrap.hr_case_documents_factory import (
                HrCaseDocumentTrackingRuntimeFactory,
            )

            factory = HrCaseDocumentTrackingRuntimeFactory
        self._runtime = factory().create()
        return self._runtime

    def _today(self):
        value = self._today_provider()
        if not isinstance(value, date):
            raise TypeError("La date de référence du suivi de pièce RH est invalide.")
        return value

    def _selected_row(self):
        index = self.list.GetFirstSelected()
        if index < 0 or index >= len(self._rows):
            return None
        return self._rows[index]

    def _update_action_state(self):
        row = self._selected_row()
        writable = row is not None and not self._read_only
        self.received.Enable(writable and not row.received if row is not None else False)
        self.withdraw.Enable(writable and row.received if row is not None else False)

    def RefreshData(self, select_document_code=None):
        checklist = self._get_runtime().build_checklist(case_id=self._case_id)
        self._rows = list(checklist.rows)
        summary = _(
            u"%d pièce(s) attendue(s) · %d reçue(s) · %d pièce(s) obligatoire(s) manquante(s)"
        ) % (
            checklist.expected_count,
            checklist.received_count,
            checklist.required_missing_count,
        )
        if self._read_only:
            summary += _(u" · lecture seule : démarche clôturée")
        self.summary.SetLabel(summary)

        selected_index = -1
        self.list.Freeze()
        try:
            self.list.DeleteAllItems()
            for row_index, row in enumerate(self._rows):
                receipt = row.receipt
                values = (
                    row.expected_document.label,
                    _(u"Obligatoire") if row.expected_document.required else _(u"Facultative"),
                    _state_label(row),
                    _format_date(receipt.received_on if receipt is not None else None),
                    _format_date(receipt.withdrawn_on if receipt is not None else None),
                    receipt.artifact_ref if receipt is not None and receipt.artifact_ref else u"—",
                )
                item = self.list.InsertItem(self.list.GetItemCount(), values[0])
                for column, value in enumerate(values[1:], 1):
                    self.list.SetItem(item, column, value)

                if row.received:
                    self.list.SetItemTextColour(item, UTILS_Interface.GetToken("success"))
                elif row.required_missing:
                    self.list.SetItemTextColour(item, UTILS_Interface.GetToken("warning"))
                elif receipt is not None and receipt.state is HrCaseDocumentState.WITHDRAWN:
                    self.list.SetItemTextColour(
                        item,
                        UTILS_Interface.GetToken("on_surface_variant"),
                    )
                if (
                    select_document_code is not None
                    and row.expected_document.code == select_document_code
                ):
                    selected_index = row_index
        finally:
            self.list.Thaw()

        if selected_index >= 0:
            self.list.Select(selected_index)
            self.list.Focus(selected_index)
            self.list.EnsureVisible(selected_index)
        self._update_action_state()
        self.Layout()

    def OnSelection(self, event):
        self._update_action_state()
        event.Skip()

    def OnRefresh(self, event):
        self.feedback.SetLabel(u"")
        row = self._selected_row()
        try:
            self.RefreshData(
                select_document_code=(
                    row.expected_document.code if row is not None else None
                )
            )
        except Exception as exc:
            self._show_error(
                _(u"Le suivi des pièces n'a pas pu être actualisé."),
                exc,
            )

    def OnReceived(self, event):
        row = self._selected_row()
        if row is None or self._read_only:
            return
        self.feedback.SetLabel(u"")
        try:
            today = self._today()
            dlg = ReceiveDocumentDialog(self, row, today)
        except Exception as exc:
            self._show_error(_(u"La réception de la pièce n'a pas pu être préparée."), exc)
            return

        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            received_on, artifact_ref = dlg.GetValues()
        except Exception as exc:
            self._show_error(_(u"Les informations de réception sont invalides."), exc)
            return
        finally:
            dlg.Destroy()

        confirm = wx.MessageDialog(
            self,
            _(
                u"Enregistrer « %s » comme reçue le %s ?\n\n"
                u"Cette action constate uniquement une réception administrative. "
                u"Elle ne valide ni l'authenticité, ni la validité, ni la conformité de la pièce."
            )
            % (row.expected_document.label, _format_date(received_on)),
            _(u"Confirmer la réception de la pièce"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        try:
            if confirm.ShowModal() != wx.ID_YES:
                return
        finally:
            confirm.Destroy()

        code = row.expected_document.code
        try:
            self._get_runtime().record_received(
                case_id=self._case_id,
                document_code=code,
                received_on=received_on,
                artifact_ref=artifact_ref,
            )
            self.RefreshData(select_document_code=code)
            self.feedback.SetForegroundColour(UTILS_Interface.GetToken("success"))
            self.feedback.SetLabel(_(u"Réception administrative enregistrée et journalisée."))
            self.Layout()
        except Exception as exc:
            self._refresh_after_error(code)
            self._show_error(_(u"La réception de la pièce n'a pas été enregistrée."), exc)

    def OnWithdraw(self, event):
        row = self._selected_row()
        if row is None or self._read_only or not row.received:
            return
        try:
            withdrawn_on = self._today()
        except Exception as exc:
            self._show_error(_(u"Le retrait de la pièce n'a pas pu être préparé."), exc)
            return

        confirm = wx.MessageDialog(
            self,
            _(
                u"Retirer l'état « reçue » de « %s » au %s ?\n\n"
                u"Aucune suppression de document n'est effectuée. Le retrait devient un état "
                u"historisé de la démarche."
            )
            % (row.expected_document.label, _format_date(withdrawn_on)),
            _(u"Confirmer le retrait de la pièce"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        try:
            if confirm.ShowModal() != wx.ID_YES:
                return
        finally:
            confirm.Destroy()

        code = row.expected_document.code
        try:
            self._get_runtime().withdraw_received(
                case_id=self._case_id,
                document_code=code,
                withdrawn_on=withdrawn_on,
            )
            self.RefreshData(select_document_code=code)
            self.feedback.SetForegroundColour(UTILS_Interface.GetToken("success"))
            self.feedback.SetLabel(_(u"Retrait administratif enregistré et journalisé."))
            self.Layout()
        except Exception as exc:
            self._refresh_after_error(code)
            self._show_error(_(u"Le retrait de la pièce n'a pas été enregistré."), exc)

    def _refresh_after_error(self, document_code):
        try:
            self.RefreshData(select_document_code=document_code)
        except Exception:
            pass

    def _show_error(self, message, exc):
        self.feedback.SetForegroundColour(UTILS_Interface.GetToken("danger"))
        self.feedback.SetLabel(message)
        self.Layout()
        wx.MessageBox(
            _(u"%s\n\n%s") % (message, str(exc)),
            _(u"Pièces de la démarche RH"),
            wx.OK | wx.ICON_ERROR,
            self,
        )
