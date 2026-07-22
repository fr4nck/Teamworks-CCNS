#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from application.presentation import (
    ContractSalaryControlDetailPresenter,
    ContractSalaryControlEmployeeSummaryViewModel,
)
from teamworks.Dlg.DLG_CCNS_salary_control_detail import Dialog as SalaryControlDetailDialog


class Dialog(wx.Dialog):
    def __init__(self, parent, summary, limited_scope_label="Synthèse limitée aux contrats chargés dans l'audit courant."):
        if type(summary) is not ContractSalaryControlEmployeeSummaryViewModel:
            raise TypeError("summary doit être un ContractSalaryControlEmployeeSummaryViewModel strict.")
        wx.Dialog.__init__(self, parent, -1, "Synthèse salariale du salarié", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        self.summary = summary
        self.limited_scope_label = limited_scope_label
        self.button_detail = wx.Button(self, -1, "Détail salarial")
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")
        self.list_ctrl = wx.ListCtrl(self, -1, style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SINGLE_SEL)
        self._init_columns()
        self._populate_rows()
        self.button_detail.Enable(False)
        self.button_detail.Bind(wx.EVT_BUTTON, self.OnOpenSalaryDetail)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChanged)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChanged)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnOpenSalaryDetail)
        self.__do_layout()
        self.SetSize((1100, 650))
        self.CentreOnParent()

    def _init_columns(self):
        for index, (label, width) in enumerate((("Contrat", 260), ("Classification", 110), ("Rémunération", 130), ("Minimum", 130), ("Source", 110), ("Écart", 110), ("Statut", 130))):
            self.list_ctrl.InsertColumn(index, label, width=width)

    def _populate_rows(self):
        for row in self.summary.rows:
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), row.contract_id_label)
            values = (row.classification_code_label, row.remuneration_amount_label, row.applicable_minimum_amount_label, row.minimum_source_label, row.shortfall_amount_label, row.status_label)
            for column, value in enumerate(values, start=1):
                self.list_ctrl.SetItem(index, column, value or "")

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._section("Salarié", (("Identifiant salarié", self.summary.employee_id_label), ("Date de référence", self.summary.reference_date_label), ("Périmètre", self.limited_scope_label))), 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self._section("Indicateurs", (("Total contrats", str(self.summary.total_count)), ("Conformes", str(self.summary.compliant_count)), ("Non conformes", str(self.summary.non_compliant_count)), ("Non évaluables", str(self.summary.not_evaluated_count)), ("Total des écarts", self.summary.total_shortfall_amount_label), ("Statut global", "Valide" if self.summary.valid else "Non valide"), ("Synthèse", self.summary.summary_label))), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer.Add(self.list_ctrl, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        buttons = wx.StdDialogButtonSizer()
        buttons.AddButton(self.button_detail)
        buttons.AddButton(self.button_close)
        buttons.Realize()
        sizer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(sizer)
        self.Layout()

    def _section(self, title, rows):
        box = wx.StaticBoxSizer(wx.StaticBox(self, -1, title), wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=6)
        grid.AddGrowableCol(1, 1)
        for label, value in rows:
            grid.Add(wx.StaticText(self, -1, label + " :"), 0, wx.ALIGN_TOP)
            text = wx.TextCtrl(self, -1, value or "Non renseigné", style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE)
            text.SetMinSize((-1, 36))
            grid.Add(text, 1, wx.EXPAND)
        box.Add(grid, 1, wx.ALL | wx.EXPAND, 8)
        return box

    def _get_selected_row(self):
        index = self.list_ctrl.GetFirstSelected()
        if index == -1 or index >= len(self.summary.rows):
            return None
        return self.summary.rows[index]

    def OnSelectionChanged(self, event):
        self.button_detail.Enable(self._get_selected_row() is not None)
        if event is not None:
            event.Skip()

    def OnOpenSalaryDetail(self, event):
        row = self._get_selected_row()
        if row is None:
            return
        detail = ContractSalaryControlDetailPresenter().present(row)
        dlg = SalaryControlDetailDialog(self, detail)
        dlg.ShowModal()
        dlg.Destroy()
