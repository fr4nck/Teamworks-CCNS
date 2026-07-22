#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts
from teamworks.CcnsCore.audit_employee_salary_summary import employee_salary_summary_from_audit_rows
from teamworks.CcnsCore.audit_filters import MINIMUM_SOURCE_FILTERS, SALARY_STATUS_FILTERS, filter_audit_rows
from teamworks.CcnsCore.audit_salary_dashboard import salary_dashboard_from_audit_rows
from teamworks.CcnsCore.audit_salary_history import save_salary_control_snapshot_from_audit_rows
from teamworks.CcnsCore.audit_salary_details import audit_row_to_dict, write_audit_csv
from teamworks.CcnsCore.audit_sorting import (
    SALARY_SORT_FIELDS,
    compute_row_severity,
    sort_audit_rows_by_person_and_severity,
    sort_audit_rows_by_salary,
)
from teamworks.Ol.OL_CCNS_audit import ListView

from teamworks.Dlg.DLG_CCNS_employee_salary_summary import Dialog as EmployeeSalarySummaryDialog
from teamworks.Dlg.DLG_CCNS_salary_control_detail import Dialog as SalaryControlDetailDialog
from teamworks.Dlg.DLG_CCNS_salary_control_history import Dialog as SalaryControlHistoryDialog

try:
    from Ctrl import CTRL_Page_contrats
except Exception:
    CTRL_Page_contrats = None


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Audit CCNS des contrats", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)

        self.rows = []
        self.filtered_rows = []

        self.label_intro = wx.StaticText(
            self,
            -1,
            "Cet audit relit les contrats Teamworks et applique les premiers controles CCNS.",
        )
        self.label_limit = wx.StaticText(self, -1, "Nombre maximal de contrats a auditer :")
        self.ctrl_limit = wx.SpinCtrl(self, -1, min=1, max=10000, initial=500)

        self.checkbox_anomalies_only = wx.CheckBox(self, -1, "Anomalies seulement")

        self.label_group = wx.StaticText(self, -1, "Groupe :")
        self.ctrl_group = wx.ComboBox(
            self,
            -1,
            choices=["", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "APPRENTI"],
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.ctrl_group.SetSelection(0)

        self.label_type = wx.StaticText(self, -1, "Type contrat :")
        self.ctrl_type = wx.ComboBox(
            self,
            -1,
            choices=["", "CDI", "CDD", "CDII", "APPRENTISSAGE", "CEE", "AUTRE"],
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.ctrl_type.SetSelection(0)

        self.label_min_salary = wx.StaticText(self, -1, "Salaire min :")
        self.ctrl_min_salary = wx.TextCtrl(self, -1, "")
        self.label_max_salary = wx.StaticText(self, -1, "Salaire max :")
        self.ctrl_max_salary = wx.TextCtrl(self, -1, "")

        self.label_salary_status = wx.StaticText(self, -1, "Statut salarial :")
        self.ctrl_salary_status = wx.ComboBox(self, -1, choices=["Tous"] + list(SALARY_STATUS_FILTERS), style=wx.CB_READONLY)
        self.ctrl_salary_status.SetSelection(0)
        self.label_minimum_source = wx.StaticText(self, -1, "Source :")
        self.ctrl_minimum_source = wx.ComboBox(self, -1, choices=["Toutes"] + list(MINIMUM_SOURCE_FILTERS), style=wx.CB_READONLY)
        self.ctrl_minimum_source.SetSelection(0)
        self.checkbox_positive_shortfall = wx.CheckBox(self, -1, "Écart positif")
        self.label_salary_sort = wx.StaticText(self, -1, "Trier par :")
        self.ctrl_salary_sort = wx.ComboBox(self, -1, choices=["Tri historique"] + list(SALARY_SORT_FIELDS), style=wx.CB_READONLY)
        self.ctrl_salary_sort.SetSelection(0)
        self.ctrl_sort_direction = wx.ComboBox(self, -1, choices=["Croissant", "Décroissant"], style=wx.CB_READONLY)
        self.ctrl_sort_direction.SetSelection(0)

        self.button_launch = wx.Button(self, -1, "Lancer l'audit")
        self.button_apply_filters = wx.Button(self, -1, "Appliquer filtres")
        self.button_reset_filters = wx.Button(self, -1, "Reinitialiser filtres")
        self.button_open_contract = wx.Button(self, -1, "Ouvrir le contrat")
        self.button_salary_detail = wx.Button(self, -1, "Détail salarial")
        self.button_employee_summary = wx.Button(self, -1, "Synthèse salarié")
        self.button_export = wx.Button(self, -1, "Exporter CSV")
        self.button_save_snapshot = wx.Button(self, -1, "Enregistrer ce contrôle")
        self.button_history = wx.Button(self, -1, "Historique salarial")
        self.button_show_non_compliant = wx.Button(self, -1, "Voir les non conformes")
        self.button_show_not_evaluated = wx.Button(self, -1, "Voir les non évaluables")
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")

        self.button_open_contract.Enable(False)
        self.button_salary_detail.Enable(False)
        self.button_employee_summary.Enable(False)
        self.button_export.Enable(False)
        self.button_save_snapshot.Enable(False)
        self.button_show_non_compliant.Enable(False)
        self.button_show_not_evaluated.Enable(False)

        self.ctrl_resume = wx.StaticText(self, -1, "Aucun audit lance.")
        self.dashboard_labels = {
            "total": wx.StaticText(self, -1, "Contrats contrôlés : 0"),
            "compliant": wx.StaticText(self, -1, "Conformes : 0"),
            "non_compliant": wx.StaticText(self, -1, "Non conformes : 0"),
            "not_evaluated": wx.StaticText(self, -1, "Non évaluables : 0"),
            "shortfall": wx.StaticText(self, -1, "Montant total des écarts : 0,00 €"),
            "compliant_pct": wx.StaticText(self, -1, "% conformes : 0 %"),
            "non_compliant_pct": wx.StaticText(self, -1, "% non conformes : 0 %"),
            "reference_date": wx.StaticText(self, -1, "Date de référence : Non disponible"),
            "summary": wx.StaticText(self, -1, "Aucun contrat salarial contrôlé dans le périmètre courant."),
        }
        self.legend = wx.StaticText(
            self,
            -1,
            "Tri : individu d'abord, puis gravite. Legende : rouge = bloquant, jaune = a revoir, vert = OK",
        )
        self.listview = ListView(self, donnees=[])

        self.button_launch.Bind(wx.EVT_BUTTON, self.OnLaunch)
        self.button_apply_filters.Bind(wx.EVT_BUTTON, self.OnApplyFilters)
        self.button_reset_filters.Bind(wx.EVT_BUTTON, self.OnResetFilters)
        self.button_open_contract.Bind(wx.EVT_BUTTON, self.OnOpenContract)
        self.button_salary_detail.Bind(wx.EVT_BUTTON, self.OnOpenSalaryDetail)
        self.button_employee_summary.Bind(wx.EVT_BUTTON, self.OnOpenEmployeeSalarySummary)
        self.button_export.Bind(wx.EVT_BUTTON, self.OnExport)
        self.button_save_snapshot.Bind(wx.EVT_BUTTON, self.OnSaveSalarySnapshot)
        self.button_history.Bind(wx.EVT_BUTTON, self.OnOpenSalaryHistory)
        self.button_show_non_compliant.Bind(wx.EVT_BUTTON, self.OnShowNonCompliant)
        self.button_show_not_evaluated.Bind(wx.EVT_BUTTON, self.OnShowNotEvaluated)

        self.listview.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChanged)
        self.listview.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChanged)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnOpenSalaryDetail)

        self.__do_layout()
        self.SetSize((1400, 800))
        self.CentreOnScreen()

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_intro, 0, wx.ALL | wx.EXPAND, 10)

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        sizer_top.Add(self.label_limit, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        sizer_top.Add(self.ctrl_limit, 0, wx.RIGHT, 12)
        sizer_top.Add(self.button_launch, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_open_contract, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_salary_detail, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_employee_summary, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_export, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_save_snapshot, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_history, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_show_non_compliant, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_show_not_evaluated, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_close, 0, 0, 0)
        sizer_base.Add(sizer_top, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        sizer_filters = wx.BoxSizer(wx.HORIZONTAL)
        sizer_filters.Add(self.checkbox_anomalies_only, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_filters.Add(self.label_group, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_filters.Add(self.ctrl_group, 0, wx.RIGHT, 10)
        sizer_filters.Add(self.label_type, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_filters.Add(self.ctrl_type, 0, wx.RIGHT, 10)
        sizer_filters.Add(self.label_min_salary, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_filters.Add(self.ctrl_min_salary, 0, wx.RIGHT, 10)
        sizer_filters.Add(self.label_max_salary, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_filters.Add(self.ctrl_max_salary, 0, wx.RIGHT, 10)
        sizer_filters.Add(self.button_apply_filters, 0, wx.RIGHT, 8)
        sizer_filters.Add(self.button_reset_filters, 0, 0, 0)
        sizer_base.Add(sizer_filters, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        sizer_salary_filters = wx.BoxSizer(wx.HORIZONTAL)
        sizer_salary_filters.Add(self.label_salary_status, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_salary_filters.Add(self.ctrl_salary_status, 0, wx.RIGHT, 10)
        sizer_salary_filters.Add(self.label_minimum_source, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_salary_filters.Add(self.ctrl_minimum_source, 0, wx.RIGHT, 10)
        sizer_salary_filters.Add(self.checkbox_positive_shortfall, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_salary_filters.Add(self.label_salary_sort, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_salary_filters.Add(self.ctrl_salary_sort, 0, wx.RIGHT, 10)
        sizer_salary_filters.Add(self.ctrl_sort_direction, 0, 0, 0)
        sizer_base.Add(sizer_salary_filters, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        sizer_dashboard = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Tableau de bord salarial"), wx.VERTICAL)
        grid_dashboard = wx.FlexGridSizer(rows=0, cols=4, vgap=4, hgap=18)
        for key in ("total", "compliant", "non_compliant", "not_evaluated", "shortfall", "compliant_pct", "non_compliant_pct", "reference_date"):
            grid_dashboard.Add(self.dashboard_labels[key], 0, wx.EXPAND, 0)
        sizer_dashboard.Add(grid_dashboard, 0, wx.ALL | wx.EXPAND, 8)
        sizer_dashboard.Add(self.dashboard_labels["summary"], 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        sizer_base.Add(sizer_dashboard, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer_base.Add(self.ctrl_resume, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer_base.Add(self.legend, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer_base.Add(self.listview, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(sizer_base)
        self.Layout()

    def _sort_rows(self, rows):
        for row in rows:
            severity_label, severity_rank = compute_row_severity(row)
            row["severity_label"] = severity_label
            row["severity_rank"] = severity_rank
        sort_label = self.ctrl_salary_sort.GetValue()
        if sort_label in SALARY_SORT_FIELDS:
            return sort_audit_rows_by_salary(
                rows,
                SALARY_SORT_FIELDS[sort_label],
                descending=self.ctrl_sort_direction.GetValue() == "Décroissant",
            )
        return sort_audit_rows_by_person_and_severity(rows)

    def _refresh_list(self):
        self.filtered_rows = self._sort_rows(self.filtered_rows)
        self.listview.donnees = self.filtered_rows
        self.listview.MAJ()

        nb_anomalies = sum(len(item.get("anomalies", [])) for item in self.filtered_rows)
        nb_bloquantes = sum(1 for item in self.filtered_rows if item.get("severity_label") == "blocking")
        nb_individus = len(set((item.get("nom_complet") or "").strip().upper() for item in self.filtered_rows))
        dashboard = salary_dashboard_from_audit_rows(self.filtered_rows)
        self._update_salary_dashboard(dashboard)

        self.ctrl_resume.SetLabel(
            "Audit charge - %d individu(s), %d ligne(s), %d anomalie(s), %d bloquante(s)." % (
                nb_individus,
                len(self.filtered_rows),
                nb_anomalies,
                nb_bloquantes,
            )
        )
        self.button_export.Enable(bool(self.filtered_rows))
        self.button_save_snapshot.Enable(bool(self.rows) and any(item.get("salary_control_row") is not None for item in self.rows))
        self.button_show_non_compliant.Enable(dashboard.non_compliant_contracts > 0)
        self.button_show_not_evaluated.Enable(dashboard.not_evaluated_contracts > 0)
        self.OnSelectionChanged(None)


    def _format_percentage_label(self, value):
        return str(value.normalize()).replace(".", ",") + " %"

    def _update_salary_dashboard(self, dashboard):
        self.dashboard_labels["total"].SetLabel("Contrats contrôlés : %d" % dashboard.total_contracts)
        self.dashboard_labels["compliant"].SetLabel("Conformes : %d" % dashboard.compliant_contracts)
        self.dashboard_labels["non_compliant"].SetLabel("Non conformes : %d" % dashboard.non_compliant_contracts)
        self.dashboard_labels["not_evaluated"].SetLabel("Non évaluables : %d" % dashboard.not_evaluated_contracts)
        self.dashboard_labels["shortfall"].SetLabel("Montant total des écarts : %s" % dashboard.total_shortfall_amount_label)
        self.dashboard_labels["compliant_pct"].SetLabel("% conformes : %s" % self._format_percentage_label(dashboard.compliant_percentage))
        self.dashboard_labels["non_compliant_pct"].SetLabel("% non conformes : %s" % self._format_percentage_label(dashboard.non_compliant_percentage))
        self.dashboard_labels["reference_date"].SetLabel("Date de référence : %s" % (dashboard.reference_date_label if dashboard.total_contracts else "Non disponible"))
        self.dashboard_labels["summary"].SetLabel(dashboard.summary_label)

    def _apply_salary_status_filter(self, label):
        if label not in SALARY_STATUS_FILTERS:
            raise ValueError("Filtre salarial inconnu : %s" % label)
        self.ctrl_salary_status.SetValue(label)
        self.OnApplyFilters(None)

    def OnShowNonCompliant(self, event):
        self._apply_salary_status_filter("Non conforme")

    def OnShowNotEvaluated(self, event):
        self._apply_salary_status_filter("Non évaluable")

    def _get_selected_row(self):
        index = self.listview.GetFirstSelected()
        if index == -1:
            return None
        if index >= len(self.filtered_rows):
            return None
        return self.filtered_rows[index]

    def OnSelectionChanged(self, event):
        row = self._get_selected_row()
        self.button_open_contract.Enable(row is not None)
        self.button_salary_detail.Enable(row is not None and row.get("salary_control_row") is not None)
        salary_row = row.get("salary_control_row") if row is not None else None
        self.button_employee_summary.Enable(salary_row is not None and salary_row.employee_id is not None)
        if event is not None:
            event.Skip()

    def OnLaunch(self, event):
        try:
            rows = audit_contracts(limit=self.ctrl_limit.GetValue())
        except Exception as exc:
            wx.MessageBox(
                "Une erreur est survenue pendant l'audit CCNS.\n\n%s" % exc,
                "Erreur",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        self.rows = [audit_row_to_dict(row) for row in rows]
        self._last_saved_snapshot_signature = None
        self.filtered_rows = list(self.rows)
        self._refresh_list()

    def _read_float(self, ctrl):
        value = ctrl.GetValue().strip()
        if value == "":
            return None
        try:
            return float(value.replace(",", "."))
        except Exception:
            return None

    def OnApplyFilters(self, event):
        self.filtered_rows = filter_audit_rows(
            self.rows,
            anomalies_only=self.checkbox_anomalies_only.GetValue(),
            classification_filter=self.ctrl_group.GetValue(),
            contract_type_filter=self.ctrl_type.GetValue(),
            min_salary=self._read_float(self.ctrl_min_salary),
            max_salary=self._read_float(self.ctrl_max_salary),
            salary_control_status=SALARY_STATUS_FILTERS.get(self.ctrl_salary_status.GetValue()),
            minimum_source=MINIMUM_SOURCE_FILTERS.get(self.ctrl_minimum_source.GetValue()),
            positive_shortfall_only=self.checkbox_positive_shortfall.GetValue(),
        )
        self._refresh_list()

    def OnResetFilters(self, event):
        self.checkbox_anomalies_only.SetValue(False)
        self.ctrl_group.SetSelection(0)
        self.ctrl_type.SetSelection(0)
        self.ctrl_min_salary.SetValue("")
        self.ctrl_max_salary.SetValue("")
        self.ctrl_salary_status.SetSelection(0)
        self.ctrl_minimum_source.SetSelection(0)
        self.checkbox_positive_shortfall.SetValue(False)
        self.ctrl_salary_sort.SetSelection(0)
        self.ctrl_sort_direction.SetSelection(0)
        self.filtered_rows = list(self.rows)
        self._refresh_list()

    def OnOpenEmployeeSalarySummary(self, event):
        row = self._get_selected_row()
        if row is None:
            return
        salary_row = row.get("salary_control_row")
        if salary_row is None:
            wx.MessageBox(
                "Aucune ligne salariale n'est disponible pour construire la synthèse.",
                "Synthèse salarié indisponible",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return
        if salary_row.employee_id is None:
            wx.MessageBox(
                "Aucun identifiant salarié stable n'est disponible pour cette ligne.",
                "Synthèse salarié indisponible",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return
        try:
            summary = employee_salary_summary_from_audit_rows(self.rows, salary_row.employee_id)
        except Exception as exc:
            wx.MessageBox(
                "Impossible de construire la synthèse salariale depuis l'audit chargé.\n\n%s" % exc,
                "Erreur",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return
        if summary.empty:
            wx.MessageBox(
                "Aucune ligne salariale du périmètre chargé ne correspond à ce salarié.",
                "Synthèse salarié vide",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return
        dlg = EmployeeSalarySummaryDialog(self, summary)
        dlg.ShowModal()
        dlg.Destroy()

    def OnOpenSalaryDetail(self, event):
        row = self._get_selected_row()
        if row is None:
            return
        if row.get("salary_control_row") is None:
            wx.MessageBox(
                "Aucun détail salarial n'est disponible pour cette ligne d'audit.",
                "Détail salarial indisponible",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return
        dlg = SalaryControlDetailDialog.from_audit_row(self, row)
        dlg.ShowModal()
        dlg.Destroy()

    def OnOpenContract(self, event):
        row = self._get_selected_row()
        if row is None:
            return

        if CTRL_Page_contrats is None:
            wx.MessageBox(
                "Le module d'ouverture de contrat n'est pas disponible dans cet environnement.",
                "Ouverture indisponible",
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        id_contrat = row["IDcontrat"]
        opened = False
        errors = []

        if hasattr(CTRL_Page_contrats, "Dialog"):
            try:
                dlg = CTRL_Page_contrats.Dialog(self, IDcontrat=id_contrat)
                dlg.ShowModal()
                dlg.Destroy()
                opened = True
            except Exception as exc:
                errors.append("Dialog(IDcontrat=...): %s" % exc)

        if not opened and hasattr(CTRL_Page_contrats, "CTRL"):
            try:
                dlg = wx.Dialog(self, -1, "Contrat %s" % id_contrat, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
                ctrl = CTRL_Page_contrats.CTRL(dlg, IDcontrat=id_contrat)
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(ctrl, 1, wx.EXPAND | wx.ALL, 8)
                dlg.SetSizer(sizer)
                dlg.SetSize((980, 720))
                dlg.CentreOnScreen()
                dlg.ShowModal()
                dlg.Destroy()
                opened = True
            except Exception as exc:
                errors.append("CTRL(IDcontrat=...): %s" % exc)

        if not opened:
            message = "Impossible d'ouvrir directement la fiche contrat %s." % id_contrat
            if errors:
                message += "\n\nTentatives effectuees :\n- " + "\n- ".join(errors)
            wx.MessageBox(
                message,
                "Ouverture impossible",
                wx.OK | wx.ICON_WARNING,
                self,
            )


    def _salary_snapshot_signature(self):
        return tuple(
            (row["salary_control_row"].contract_id, row["salary_control_row"].status, row["salary_control_row"].shortfall_amount, row["salary_control_row"].issue_code, row["salary_control_row"].failure_reason)
            for row in self.rows
            if row.get("salary_control_row") is not None
        )

    def OnSaveSalarySnapshot(self, event):
        salary_rows = [row for row in self.rows if row.get("salary_control_row") is not None]
        if not salary_rows:
            wx.MessageBox(
                "Aucun contrôle salarial complet n'est disponible pour l'enregistrement.",
                "Contrôle vide",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return
        signature = self._salary_snapshot_signature()
        if signature == getattr(self, "_last_saved_snapshot_signature", None):
            wx.MessageBox(
                "Ce contrôle vient déjà d'être enregistré dans cette session.",
                "Enregistrement déjà effectué",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return
        dashboard = salary_dashboard_from_audit_rows(self.rows)
        message = "Enregistrer ce contrôle salarial ?\n\nContrats : %d\nMontant total des écarts : %s" % (
            dashboard.total_contracts,
            dashboard.total_shortfall_amount_label,
        )
        if wx.MessageBox(message, "Confirmation", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self) != wx.YES:
            return
        try:
            snapshot = save_salary_control_snapshot_from_audit_rows(self.rows)
        except Exception as exc:
            wx.MessageBox(
                "Impossible d'enregistrer l'historique du contrôle salarial.\n\n%s" % exc,
                "Erreur",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return
        self._last_saved_snapshot_signature = signature
        wx.MessageBox(
            "Contrôle salarial enregistré.\n\nSnapshot : %s" % snapshot.snapshot_id,
            "Enregistrement terminé",
            wx.OK | wx.ICON_INFORMATION,
            self,
        )

    def OnOpenSalaryHistory(self, event):
        dlg = SalaryControlHistoryDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExport(self, event):
        if not self.filtered_rows:
            return

        wildcard = "Fichiers CSV (*.csv)|*.csv"
        dlg = wx.FileDialog(
            self,
            message="Exporter l'audit CCNS",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        dlg.SetFilename("audit_ccns_contrats.csv")

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        path = dlg.GetPath()
        dlg.Destroy()

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                write_audit_csv(f, self.filtered_rows)
        except Exception as exc:
            wx.MessageBox(
                "Impossible d'exporter le fichier CSV.\n\n%s" % exc,
                "Erreur",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        wx.MessageBox(
            "Export CSV termine.\n\n%s" % path,
            "Export termine",
            wx.OK | wx.ICON_INFORMATION,
            self,
        )
