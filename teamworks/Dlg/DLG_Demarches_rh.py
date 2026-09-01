#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Cockpit CRH-24/26/28 des démarches RH.

La consultation reste portée par la façade CRH-23. CRH-26 ajoute uniquement des
transitions métier explicitement autorisées par la frontière CRH-25. CRH-28
raccorde la consultation du journal CRH-27 par chargement paresseux. L'écran ne
connaît ni GestionDB, ni les repositories, ni l'identité logique de la structure
et ne modifie jamais le statut technique d'échange.
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


def _optional_text(value):
    value = value.strip()
    return value or None


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
    """Détail descriptif d'une ligne du cockpit."""

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
            (
                _(u"Échange"),
                _EXCHANGE_LABELS.get(row.exchange_status, row.exchange_status.value),
            ),
            (_(u"Pièces attendues"), _pieces_label(row)),
            (_(u"Attention"), _attention_label(row)),
        )
        for label, value in fields:
            label_ctrl = wx.StaticText(self, -1, label)
            label_ctrl.SetForegroundColour(
                UTILS_Interface.GetToken("on_surface_variant")
            )
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
        notes.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        notes.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        close = wx.Button(self, wx.ID_CLOSE, _(u"Fermer"))
        close.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE))

        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(notes, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(
            close,
            0,
            wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        self.SetSizer(sizer)
        self.SetMinSize(
            (
                UTILS_Styles.Scale(650, minimum=560),
                UTILS_Styles.Scale(480, minimum=400),
            )
        )
        self.CentreOnParent()


class TransitionDialog(wx.Dialog):
    """Saisie d'une transition métier parmi celles autorisées par CRH-25."""

    def __init__(self, parent, case, allowed_statuses):
        allowed_statuses = tuple(allowed_statuses)
        if not allowed_statuses:
            raise ValueError("Aucune transition métier n'est disponible pour ce dossier RH.")

        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Faire évoluer la démarche RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._case = case
        self._allowed_statuses = allowed_statuses
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        title = wx.StaticText(
            self,
            -1,
            _(u"Statut actuel : %s")
            % _STATUS_LABELS.get(case.status, case.status.value),
        )
        title_font = title.GetFont()
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        exchange = wx.StaticText(
            self,
            -1,
            _(u"État technique inchangé : %s")
            % _EXCHANGE_LABELS.get(case.exchange_status, case.exchange_status.value),
        )
        exchange.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        self.status = wx.Choice(
            self,
            choices=[
                _STATUS_LABELS.get(status, status.value)
                for status in self._allowed_statuses
            ],
        )
        self.status.SetSelection(0)

        self.result = wx.TextCtrl(self, value=case.result or u"")
        self.comment = wx.TextCtrl(
            self,
            value=case.comment or u"",
            style=wx.TE_MULTILINE | wx.BORDER_SIMPLE,
        )

        grid = wx.FlexGridSizer(cols=2, vgap=10, hgap=12)
        grid.AddGrowableCol(1, 1)
        grid.Add(wx.StaticText(self, -1, _(u"Nouveau statut")), 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.status, 1, wx.EXPAND)
        grid.Add(wx.StaticText(self, -1, _(u"Résultat / référence")), 0, wx.ALIGN_TOP)
        grid.Add(self.result, 1, wx.EXPAND)
        grid.Add(wx.StaticText(self, -1, _(u"Commentaire")), 0, wx.ALIGN_TOP)
        grid.Add(self.comment, 1, wx.EXPAND)

        info = wx.StaticText(
            self,
            -1,
            _(
                u"Seul le statut métier sera modifié. La transition sera journalisée "
                u"et devra être confirmée avant enregistrement."
            ),
        )
        info.Wrap(UTILS_Styles.Scale(560, minimum=420))
        info.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

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
        sizer.Add(exchange, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(info, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        self.SetSizer(sizer)
        self.SetMinSize(
            (
                UTILS_Styles.Scale(650, minimum=560),
                UTILS_Styles.Scale(430, minimum=360),
            )
        )
        self.CentreOnParent()

    def GetValues(self):
        selection = self.status.GetSelection()
        if selection < 0 or selection >= len(self._allowed_statuses):
            raise ValueError("Le nouveau statut métier n'est pas sélectionné.")
        return (
            self._allowed_statuses[selection],
            _optional_text(self.result.GetValue()),
            _optional_text(self.comment.GetValue()),
        )


class Dialog(wx.Dialog):
    """Cockpit structure CRH-24/26/28 sur la base Teamworks active."""

    def __init__(
        self,
        parent,
        runtime_factory=None,
        today_provider=None,
        workflow_runtime_factory=None,
    ):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Démarches RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._runtime_factory = runtime_factory or HrCaseDashboardRuntimeFactory
        self._today_provider = today_provider or date.today
        self._workflow_runtime_factory = workflow_runtime_factory
        self._runtime = self._runtime_factory().create()
        self._workflow_runtime = None
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
            _(u"Démarches, échéances, anomalies et suivi administratif de la structure."),
        )
        self.subtitle.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))
        self.snapshot = wx.StaticText(self, -1, u"")
        self.snapshot.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))
        self.feedback = wx.StaticText(self, -1, u"")
        self.feedback.SetForegroundColour(UTILS_Interface.GetToken("success"))

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
        self.list.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
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
        self.history = wx.Button(self, -1, _(u"Historique"))
        self.advance = wx.Button(self, -1, _(u"Faire évoluer"))
        self.close = wx.Button(self, wx.ID_CLOSE, _(u"Fermer"))
        self.details.Enable(False)
        self.history.Enable(False)
        self.advance.Enable(False)

        self.refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
        self.details.Bind(wx.EVT_BUTTON, self.OnDetails)
        self.history.Bind(wx.EVT_BUTTON, self.OnHistory)
        self.advance.Bind(wx.EVT_BUTTON, self.OnAdvance)
        self.close.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE))
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDetails)

        self._layout()
        self.RefreshData()
        self.SetMinSize(
            (
                UTILS_Styles.Scale(1180, minimum=920),
                UTILS_Styles.Scale(680, minimum=540),
            )
        )
        self.CentreOnParent()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")

        heading = wx.BoxSizer(wx.VERTICAL)
        heading.Add(self.title, 0, wx.BOTTOM, max(2, gap // 2))
        heading.Add(self.subtitle, 0, wx.BOTTOM, max(2, gap // 2))
        heading.Add(self.snapshot, 0, wx.BOTTOM, max(2, gap // 2))
        heading.Add(self.feedback, 0)

        counters = wx.FlexGridSizer(cols=6, vgap=gap, hgap=gap)
        for panel in self.counters.values():
            counters.Add(panel, 1, wx.EXPAND | wx.ALL, gap)
        for column in range(6):
            counters.AddGrowableCol(column, 1)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(self.refresh, 0, wx.RIGHT, gap)
        buttons.Add(self.details, 0, wx.RIGHT, gap)
        buttons.Add(self.history, 0, wx.RIGHT, gap)
        buttons.Add(self.advance, 0, wx.RIGHT, gap)
        buttons.AddStretchSpacer(1)
        buttons.Add(self.close, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(heading, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(counters, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)

    def _selected_row(self):
        index = self.list.GetFirstSelected()
        if index < 0 or index >= len(self._rows):
            return None
        return self._rows[index]

    def _update_action_state(self):
        row = self._selected_row()
        has_selection = row is not None
        self.details.Enable(has_selection)
        self.history.Enable(has_selection)
        self.advance.Enable(has_selection and row.status not in {
            HrCaseStatus.ACCEPTED,
            HrCaseStatus.CANCELLED,
        })

    def _get_workflow_runtime(self):
        if self._workflow_runtime is not None:
            return self._workflow_runtime

        factory = self._workflow_runtime_factory
        if factory is None:
            from application.bootstrap.hr_case_workflow_factory import (
                HrCaseWorkflowRuntimeFactory,
            )

            factory = HrCaseWorkflowRuntimeFactory
        self._workflow_runtime = factory().create()
        return self._workflow_runtime

    def RefreshData(self, select_case_id=None):
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

        selected_index = -1
        self.list.Freeze()
        try:
            self.list.DeleteAllItems()
            for row_index, row in enumerate(self._rows):
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
                    self.list.SetItemTextColour(
                        item,
                        UTILS_Interface.GetToken("danger"),
                    )
                elif row.needs_attention:
                    self.list.SetItemTextColour(
                        item,
                        UTILS_Interface.GetToken("warning"),
                    )
                elif row.status in {HrCaseStatus.ACCEPTED, HrCaseStatus.CANCELLED}:
                    self.list.SetItemTextColour(
                        item,
                        UTILS_Interface.GetToken("on_surface_variant"),
                    )
                if select_case_id is not None and row.case_id == select_case_id:
                    selected_index = row_index
        finally:
            self.list.Thaw()

        if selected_index >= 0:
            self.list.Select(selected_index)
            self.list.Focus(selected_index)
            self.list.EnsureVisible(selected_index)
        self._update_action_state()
        self.Layout()

    def OnRefresh(self, event):
        self.feedback.SetLabel(u"")
        try:
            row = self._selected_row()
            self.RefreshData(select_case_id=row.case_id if row else None)
        except Exception as exc:
            wx.MessageBox(
                _(u"Le cockpit des démarches RH n'a pas pu être actualisé.\n\n%s")
                % str(exc),
                _(u"Démarches RH"),
                wx.OK | wx.ICON_ERROR,
                self,
            )

    def OnSelection(self, event):
        self._update_action_state()
        event.Skip()

    def OnDetails(self, event):
        row = self._selected_row()
        if row is None:
            return
        dlg = DetailDialog(self, row)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    def OnHistory(self, event):
        row = self._selected_row()
        if row is None:
            return

        try:
            from Dlg import DLG_Demarches_rh_historique

            dlg = DLG_Demarches_rh_historique.Dialog(
                self,
                case_id=row.case_id,
            )
        except Exception as exc:
            wx.MessageBox(
                _(u"L'historique de cette démarche est momentanément indisponible.\n\n%s")
                % str(exc),
                _(u"Historique de la démarche RH"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    def OnAdvance(self, event):
        row = self._selected_row()
        if row is None:
            return

        self.feedback.SetLabel(u"")
        try:
            workflow = self._get_workflow_runtime()
            options = workflow.available_transitions(case_id=row.case_id)
        except Exception as exc:
            self._show_transition_error(row.case_id, exc)
            return

        if options.case.status is not row.status:
            self.RefreshData(select_case_id=row.case_id)
            wx.MessageBox(
                _(
                    u"Cette démarche a changé depuis l'affichage du cockpit. "
                    u"La liste vient d'être actualisée ; vérifiez son nouveau statut avant de continuer."
                ),
                _(u"Démarches RH"),
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return

        if not options.allowed_statuses:
            self.RefreshData(select_case_id=row.case_id)
            wx.MessageBox(
                _(u"Aucune transition métier n'est autorisée depuis le statut actuel."),
                _(u"Démarches RH"),
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return

        dlg = TransitionDialog(self, options.case, options.allowed_statuses)
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            status, result, comment = dlg.GetValues()
        finally:
            dlg.Destroy()

        current_label = _STATUS_LABELS.get(options.case.status, options.case.status.value)
        target_label = _STATUS_LABELS.get(status, status.value)
        confirm = wx.MessageDialog(
            self,
            _(
                u"Confirmer le passage de « %s » à « %s » ?\n\n"
                u"Cette action modifiera le statut métier du dossier et ajoutera "
                u"une trace d'audit. L'état technique d'échange ne sera pas modifié."
            )
            % (current_label, target_label),
            _(u"Confirmer la transition RH"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        try:
            if confirm.ShowModal() != wx.ID_YES:
                return
        finally:
            confirm.Destroy()

        try:
            workflow.transition(
                case_id=row.case_id,
                status=status,
                result=result,
                comment=comment,
            )
            self.RefreshData(select_case_id=row.case_id)
            self.feedback.SetForegroundColour(UTILS_Interface.GetToken("success"))
            self.feedback.SetLabel(
                _(u"Démarche mise à jour : nouveau statut « %s ».") % target_label
            )
            self.Layout()
        except Exception as exc:
            self._show_transition_error(row.case_id, exc)

    def _show_transition_error(self, case_id, exc):
        try:
            self.RefreshData(select_case_id=case_id)
        except Exception:
            pass
        self.feedback.SetForegroundColour(UTILS_Interface.GetToken("danger"))
        self.feedback.SetLabel(_(u"La transition n'a pas été enregistrée."))
        self.Layout()
        wx.MessageBox(
            _(
                u"La transition n'a pas pu être enregistrée. Le cockpit a été "
                u"actualisé afin de tenir compte d'une éventuelle modification concurrente.\n\n%s"
            )
            % str(exc),
            _(u"Démarches RH"),
            wx.OK | wx.ICON_ERROR,
            self,
        )
