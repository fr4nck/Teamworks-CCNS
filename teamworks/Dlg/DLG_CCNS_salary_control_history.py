#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from application.control import BuildContractSalaryControlConsolidatedReportUseCase
from application.presentation import ContractSalaryAlertPresenter, ContractSalaryControlConsolidatedExporter, ContractSalaryControlExportFormat, ContractSalaryControlIssueHistoryPresenter, ContractSalaryControlSnapshotComparisonPresenter, format_euro_amount, format_french_date
from teamworks.CcnsCore.audit_salary_alerts import generate_salary_control_alerts
from teamworks.CcnsCore.audit_salary_history import compare_salary_control_snapshots, list_salary_control_snapshots, track_salary_control_issues
from Utils import UTILS_Interface, UTILS_Theme


class Dialog(wx.Dialog):
    def __init__(self, parent, repository=None):
        wx.Dialog.__init__(self, parent, -1, "Historique des contrôles salariaux", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.repository = repository
        self.snapshots = list(list_salary_control_snapshots(repository=repository))
        self.listbox = wx.ListBox(box_snapshots, -1, choices=[self._summary(s) for s in self.snapshots], style=wx.LB_EXTENDED)
        self.details = wx.TextCtrl(box_details, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.filter = wx.ComboBox(self, -1, choices=["Tous", "Améliorations", "Dégradations", "Nouveaux contrats", "Contrats absents", "Changements de statut", "Écarts modifiés", "Inchangés"], style=wx.CB_READONLY)
        self.filter.SetSelection(0)
        self.button_compare = wx.Button(self, -1, "Comparer")
        self.button_track_issues = wx.Button(self, -1, "Suivi des anomalies")
        self.button_alerts = wx.Button(self, -1, "Alertes")
        self.button_export_csv = wx.Button(self, -1, "Exporter le rapport consolidé CSV")
        self.button_export_json = wx.Button(self, -1, "Exporter le rapport consolidé JSON")
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")
        self.listbox.Bind(wx.EVT_LISTBOX, self.OnSelect)
        self.button_compare.Bind(wx.EVT_BUTTON, self.OnCompare)
        self.button_track_issues.Bind(wx.EVT_BUTTON, self.OnTrackIssues)
        self.button_alerts.Bind(wx.EVT_BUTTON, self.OnAlerts)
        self.button_export_csv.Bind(wx.EVT_BUTTON, self.OnExportConsolidatedCsv)
        self.button_export_json.Bind(wx.EVT_BUTTON, self.OnExportConsolidatedJson)
        self.filter.Bind(wx.EVT_COMBOBOX, self.OnFilter)
        self._last_comparison = None
        self._last_issue_history = None
        self._last_alerts = None
        self.__do_layout()
        self.SetSize((1120, 700))
        self.SetMinSize((900, 560))
        if self.snapshots:
            self.listbox.SetSelection(0)
            self._show(self.snapshots[0])

    def __do_layout(self):
        ui = UTILS_Theme.metrics()
        surface = UTILS_Interface.GetToken("surface_container")
        text_colour = UTILS_Interface.GetToken("on_surface")
        text_variant = UTILS_Interface.GetToken("on_surface_variant")

        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.details.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.details.SetForegroundColour(text_colour)
        self.listbox.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.listbox.SetForegroundColour(text_colour)

        sizer = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(self, -1, "Comparez les contrôles enregistrés, suivez les anomalies et exportez un rapport consolidé.")
        intro.SetForegroundColour(text_variant)
        sizer.Add(intro, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, ui["space_m"])

        body = wx.BoxSizer(wx.HORIZONTAL)

        box_snapshots = wx.StaticBox(self, -1, "Contrôles enregistrés")
        box_snapshots.SetBackgroundColour(surface)
        box_snapshots.SetForegroundColour(text_colour)
        snapshots_sizer = wx.StaticBoxSizer(box_snapshots, wx.VERTICAL)
        self.listbox.Reparent(box_snapshots)
        snapshots_sizer.Add(self.listbox, 1, wx.ALL | wx.EXPAND, ui["space_s"])
        body.Add(snapshots_sizer, 1, wx.RIGHT | wx.EXPAND, ui["space_m"])

        box_details = wx.StaticBox(self, -1, "Détail et analyse")
        box_details.SetBackgroundColour(surface)
        box_details.SetForegroundColour(text_colour)
        details_sizer = wx.StaticBoxSizer(box_details, wx.VERTICAL)
        self.details.Reparent(box_details)
        details_sizer.Add(self.details, 1, wx.ALL | wx.EXPAND, ui["space_s"])
        body.Add(details_sizer, 2, wx.EXPAND)

        sizer.Add(body, 1, wx.ALL | wx.EXPAND, ui["space_m"])

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(wx.StaticText(self, -1, "Filtrer :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, ui["space_xs"])
        actions.Add(self.filter, 0, wx.RIGHT, ui["space_m"])
        actions.Add(self.button_compare, 0, wx.RIGHT, ui["space_s"])
        actions.Add(self.button_track_issues, 0, wx.RIGHT, ui["space_s"])
        actions.Add(self.button_alerts, 0, wx.RIGHT, ui["space_m"])
        actions.AddStretchSpacer(1)
        actions.Add(self.button_export_csv, 0, wx.RIGHT, ui["space_s"])
        actions.Add(self.button_export_json, 0, wx.RIGHT, ui["space_m"])
        actions.Add(self.button_close, 0)
        sizer.Add(actions, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, ui["space_m"])

        self.SetSizer(sizer)
        self.Layout()

    def _summary(self, snapshot):
        return "%s | exécuté %s | %d contrats | écart %s | %s" % (
            format_french_date(snapshot.reference_date),
            snapshot.executed_at.isoformat(timespec="seconds"),
            snapshot.total_contracts,
            format_euro_amount(snapshot.total_shortfall_amount),
            snapshot.snapshot_id,
        )

    def _show(self, snapshot):
        lines = [
            "Snapshot : %s" % snapshot.snapshot_id,
            "Date de référence : %s" % format_french_date(snapshot.reference_date),
            "Date d'exécution : %s" % snapshot.executed_at.isoformat(timespec="seconds"),
            "Contrats : %d | conformes : %d | non conformes : %d | non évaluables : %d" % (snapshot.total_contracts, snapshot.compliant_contracts, snapshot.non_compliant_contracts, snapshot.not_evaluated_contracts),
            "Montant total des écarts : %s" % format_euro_amount(snapshot.total_shortfall_amount),
            "",
        ]
        for row in snapshot.rows:
            lines.append("%s | salarié %s | %s | rémunération %s | minimum %s | écart %s | anomalie %s" % (
                row.contract_id,
                row.employee_id or "Non renseigné",
                row.status.value,
                row.remuneration_amount if row.remuneration_amount is not None else "Non disponible",
                row.applicable_minimum_amount if row.applicable_minimum_amount is not None else "Non disponible",
                row.shortfall_amount,
                row.issue_code or row.failure_reason.value if row.failure_reason is not None else row.issue_code or "",
            ))
        self.details.SetValue("\n".join(lines))

    def OnSelect(self, event):
        index = self.listbox.GetSelection()
        if 0 <= index < len(self.snapshots):
            self._show(self.snapshots[index])

    def _filter_key(self):
        return (
            ContractSalaryControlSnapshotComparisonPresenter.FILTER_ALL,
            ContractSalaryControlSnapshotComparisonPresenter.FILTER_IMPROVEMENTS,
            ContractSalaryControlSnapshotComparisonPresenter.FILTER_DEGRADATIONS,
            ContractSalaryControlSnapshotComparisonPresenter.FILTER_NEW_CONTRACTS,
            ContractSalaryControlSnapshotComparisonPresenter.FILTER_REMOVED_CONTRACTS,
            ContractSalaryControlSnapshotComparisonPresenter.FILTER_STATUS_CHANGES,
            ContractSalaryControlSnapshotComparisonPresenter.FILTER_SHORTFALL_CHANGED,
            ContractSalaryControlSnapshotComparisonPresenter.FILTER_UNCHANGED,
        )[self.filter.GetSelection()]

    def OnFilter(self, event):
        if self._last_alerts is not None:
            self._show_alerts(self._last_alerts)
        elif self._last_issue_history is not None:
            self._show_issue_history(self._last_issue_history)
        elif self._last_comparison is not None:
            self._show_comparison(self._last_comparison)

    def OnCompare(self, event):
        selections = list(self.listbox.GetSelections())
        if len(selections) != 2:
            wx.MessageBox("Sélectionnez exactement deux snapshots à comparer.", "Comparaison impossible", wx.OK | wx.ICON_WARNING)
            return
        before = self.snapshots[selections[0]]
        after = self.snapshots[selections[1]]
        if before.snapshot_id == after.snapshot_id:
            wx.MessageBox("Un snapshot ne peut pas être comparé avec lui-même.", "Comparaison impossible", wx.OK | wx.ICON_WARNING)
            return
        try:
            self._last_alerts = None
            self._last_issue_history = None
            self._last_comparison = compare_salary_control_snapshots(before.snapshot_id, after.snapshot_id, repository=self.repository)
            self.filter.SetItems(["Tous", "Améliorations", "Dégradations", "Nouveaux contrats", "Contrats absents", "Changements de statut", "Écarts modifiés", "Inchangés"])
            self.filter.SetSelection(0)
        except Exception as exc:
            wx.MessageBox("Impossible de comparer les snapshots.\n\n%s" % exc, "Comparaison impossible", wx.OK | wx.ICON_ERROR)
            return
        self._show_comparison(self._last_comparison)

    def _show_comparison(self, comparison):
        presenter = ContractSalaryControlSnapshotComparisonPresenter()
        vm = presenter.present(comparison, filter_key=self._filter_key())
        lines = ["Comparaison", "==========", *vm.summary_lines, "", "Contrats", "========"]
        for row in vm.rows:
            lines.append("%s | salarié %s | %s → %s | %s | rémunération %s → %s | minimum %s → %s | écart %s → %s | delta %s" % (
                row.contract_id_label, row.employee_id_label, row.status_before_label, row.status_after_label, row.change_type_label,
                row.remuneration_before_label, row.remuneration_after_label, row.minimum_before_label, row.minimum_after_label,
                row.shortfall_before_label, row.shortfall_after_label, row.shortfall_delta_label,
            ))
        self.details.SetValue("\n".join(lines))

    def OnTrackIssues(self, event):
        selections = list(self.listbox.GetSelections())
        if len(selections) != 2:
            wx.MessageBox("Sélectionnez exactement deux snapshots pour suivre les anomalies.", "Suivi impossible", wx.OK | wx.ICON_WARNING)
            return
        before = self.snapshots[selections[0]]
        after = self.snapshots[selections[1]]
        try:
            self._last_alerts = None
            self._last_comparison = None
            self._last_issue_history = track_salary_control_issues(before.snapshot_id, after.snapshot_id, repository=self.repository)
            self.filter.SetItems(["Toutes", "Nouvelles", "Persistantes", "Résolues"])
            self.filter.SetSelection(0)
        except Exception as exc:
            wx.MessageBox("Impossible de suivre les anomalies.\n\n%s" % exc, "Suivi impossible", wx.OK | wx.ICON_ERROR)
            return
        self._show_issue_history(self._last_issue_history)

    def _issue_filter_key(self):
        return (
            ContractSalaryControlIssueHistoryPresenter.FILTER_ALL,
            ContractSalaryControlIssueHistoryPresenter.FILTER_NEW,
            ContractSalaryControlIssueHistoryPresenter.FILTER_ONGOING,
            ContractSalaryControlIssueHistoryPresenter.FILTER_RESOLVED,
        )[self.filter.GetSelection()]

    def _show_issue_history(self, history):
        presenter = ContractSalaryControlIssueHistoryPresenter()
        vm = presenter.present(history, filter_key=self._issue_filter_key())
        lines = ["Suivi des anomalies", "===================", *vm.summary_lines, "", "Anomalies", "========="]
        for row in vm.rows:
            lines.append("%s | salarié %s | anomalie %s | %s | %s | motif %s → %s | snapshots %s → %s" % (
                row.contract_id_label, row.employee_id_label, row.issue_label, row.status_label, row.evolution_label,
                row.before_reason_label, row.after_reason_label, row.before_snapshot_date_label, row.after_snapshot_date_label,
            ))
        self.details.SetValue("\n".join(lines))

    def OnAlerts(self, event):
        try:
            self._last_comparison = None
            self._last_issue_history = None
            self._last_alerts = generate_salary_control_alerts(repository=self.repository)
            self.filter.SetItems(["Toutes", "Critiques", "Avertissements", "Informations", "Non conformités", "Nouvelles anomalies", "Résolues"])
            self.filter.SetSelection(0)
        except Exception as exc:
            wx.MessageBox("Impossible de générer les alertes.\n\n%s" % exc, "Alertes indisponibles", wx.OK | wx.ICON_ERROR)
            return
        self._show_alerts(self._last_alerts)

    def _alert_filter_key(self):
        return (
            ContractSalaryAlertPresenter.FILTER_ALL,
            ContractSalaryAlertPresenter.FILTER_CRITICAL,
            ContractSalaryAlertPresenter.FILTER_WARNING,
            ContractSalaryAlertPresenter.FILTER_INFO,
            ContractSalaryAlertPresenter.FILTER_NON_COMPLIANCE,
            ContractSalaryAlertPresenter.FILTER_NEW_ANOMALIES,
            ContractSalaryAlertPresenter.FILTER_RESOLVED,
        )[self.filter.GetSelection()]

    def _show_alerts(self, alerts):
        presenter = ContractSalaryAlertPresenter()
        vm = presenter.present(alerts, filter_key=self._alert_filter_key())
        lines = ["Alertes", "=======", *vm.summary_lines, "", "Liste", "====="]
        for row in vm.rows:
            lines.append("%s | salarié %s | contrat %s | %s | %s | %s" % (
                row.severity_label, row.employee_label, row.contract_label, row.type_label, row.summary, row.date_label,
            ))
            lines.append("  %s" % row.detail)
        self.details.SetValue("\n".join(lines))

    def _selected_current_and_previous(self):
        selections = list(self.listbox.GetSelections())
        if not selections:
            index = self.listbox.GetSelection()
            selections = [index] if 0 <= index < len(self.snapshots) else []
        if not selections:
            wx.MessageBox("Sélectionnez au moins le snapshot courant à exporter.", "Export impossible", wx.OK | wx.ICON_WARNING)
            return None, None
        if len(selections) > 2:
            wx.MessageBox("Sélectionnez un snapshot courant, et éventuellement un snapshot précédent.", "Export impossible", wx.OK | wx.ICON_WARNING)
            return None, None
        snapshots = [self.snapshots[index] for index in selections]
        snapshots.sort(key=lambda snapshot: (snapshot.executed_at, snapshot.snapshot_id))
        if len(snapshots) == 1:
            return snapshots[0], None
        return snapshots[1], snapshots[0]

    def OnExportConsolidatedCsv(self, event):
        self._export_consolidated(ContractSalaryControlExportFormat.CSV)

    def OnExportConsolidatedJson(self, event):
        self._export_consolidated(ContractSalaryControlExportFormat.JSON)

    def _export_consolidated(self, format):
        current, previous = self._selected_current_and_previous()
        if current is None:
            return
        try:
            report = BuildContractSalaryControlConsolidatedReportUseCase().execute(current, previous)
            export = ContractSalaryControlConsolidatedExporter().export(report, format)
        except Exception as exc:
            wx.MessageBox("Impossible de construire le rapport consolidé.\n\n%s" % exc, "Export impossible", wx.OK | wx.ICON_ERROR)
            return
        wildcard = "CSV (*.csv)|*.csv" if format is ContractSalaryControlExportFormat.CSV else "JSON (*.json)|*.json"
        with wx.FileDialog(self, "Exporter le rapport consolidé", wildcard=wildcard, defaultFile=export.suggested_filename, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            with open(dialog.GetPath(), "w", encoding="utf-8", newline="") as file_obj:
                file_obj.write(export.content)
