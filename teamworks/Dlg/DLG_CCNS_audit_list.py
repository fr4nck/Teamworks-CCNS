#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import wx

from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts
from teamworks.CcnsCore.audit_filters import filter_audit_rows
from teamworks.Ol.OL_CCNS_audit import ListView

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

        self.button_launch = wx.Button(self, -1, "Lancer l'audit")
        self.button_apply_filters = wx.Button(self, -1, "Appliquer filtres")
        self.button_reset_filters = wx.Button(self, -1, "Reinitialiser filtres")
        self.button_open_contract = wx.Button(self, -1, "Ouvrir le contrat")
        self.button_export = wx.Button(self, -1, "Exporter CSV")
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")

        self.button_open_contract.Enable(False)
        self.button_export.Enable(False)

        self.ctrl_resume = wx.StaticText(self, -1, "Aucun audit lance.")
        self.listview = ListView(self, donnees=[])

        self.button_launch.Bind(wx.EVT_BUTTON, self.OnLaunch)
        self.button_apply_filters.Bind(wx.EVT_BUTTON, self.OnApplyFilters)
        self.button_reset_filters.Bind(wx.EVT_BUTTON, self.OnResetFilters)
        self.button_open_contract.Bind(wx.EVT_BUTTON, self.OnOpenContract)
        self.button_export.Bind(wx.EVT_BUTTON, self.OnExport)

        self.listview.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChanged)
        self.listview.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChanged)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnOpenContract)

        self.__do_layout()
        self.SetSize((1360, 780))
        self.CentreOnScreen()

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_intro, 0, wx.ALL | wx.EXPAND, 10)

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        sizer_top.Add(self.label_limit, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        sizer_top.Add(self.ctrl_limit, 0, wx.RIGHT, 12)
        sizer_top.Add(self.button_launch, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_open_contract, 0, wx.RIGHT, 8)
        sizer_top.Add(self.button_export, 0, wx.RIGHT, 8)
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

        sizer_base.Add(self.ctrl_resume, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer_base.Add(self.listview, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(sizer_base)
        self.Layout()

    def _refresh_list(self):
        self.listview.donnees = self.filtered_rows
        self.listview.MAJ()
        nb_anomalies = sum(len(item.get("anomalies", [])) for item in self.filtered_rows)
        self.ctrl_resume.SetLabel(
            "Audit charge - %d ligne(s) affichee(s), %d anomalie(s) visible(s)." % (len(self.filtered_rows), nb_anomalies)
        )
        self.button_export.Enable(bool(self.filtered_rows))
        self.OnSelectionChanged(None)

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

        self.rows = []
        for row in rows:
            self.rows.append({
                "IDcontrat": row.IDcontrat,
                "nom_complet": row.nom_complet,
                "classification": row.classification or "",
                "type_contrat": row.type_contrat or "",
                "salaire_base": row.salaire_base,
                "anomalies": row.anomalies,
                "messages": row.messages,
            })
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
        )
        self._refresh_list()

    def OnResetFilters(self, event):
        self.checkbox_anomalies_only.SetValue(False)
        self.ctrl_group.SetSelection(0)
        self.ctrl_type.SetSelection(0)
        self.ctrl_min_salary.SetValue("")
        self.ctrl_max_salary.SetValue("")
        self.filtered_rows = list(self.rows)
        self._refresh_list()

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
                writer = csv.writer(f, delimiter=";")
                writer.writerow([
                    "IDcontrat", "Nom", "Classification", "Type contrat",
                    "Salaire base", "Nb anomalies", "Anomalies", "Messages"
                ])
                for row in self.filtered_rows:
                    writer.writerow([
                        row["IDcontrat"],
                        row["nom_complet"],
                        row["classification"],
                        row["type_contrat"],
                        row["salaire_base"] if row["salaire_base"] is not None else "",
                        len(row["anomalies"]),
                        ", ".join(row["anomalies"]),
                        " | ".join(row["messages"]),
                    ])
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
