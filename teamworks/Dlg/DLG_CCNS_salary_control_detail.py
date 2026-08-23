#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from application.presentation import ContractSalaryControlDetailViewModel, detail_from_audit_row
from Utils import UTILS_Interface


class Dialog(wx.Dialog):
    def __init__(self, parent, detail):
        if type(detail) is not ContractSalaryControlDetailViewModel:
            raise TypeError("detail doit être un ContractSalaryControlDetailViewModel strict.")
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            "Détail du contrôle salarial",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )
        self.detail = detail
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")
        self.__do_layout()
        self.SetSize((760, 620))
        self.CentreOnParent()

    @classmethod
    def from_audit_row(cls, parent, row):
        return cls(parent, detail_from_audit_row(row))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self._section("Identité", (
            ("Identifiant salarié", self.detail.employee_id_label),
            ("Identifiant contrat", str(self.detail.contract_id)),
            ("Date de référence", self.detail.reference_date_label),
        )), 0, wx.ALL | wx.EXPAND, 10)
        sizer_base.Add(self._section("Classification et rémunération", (
            ("Classification CCNS", self.detail.classification_code_label),
            ("Rémunération mensuelle brute", self.detail.remuneration_amount_label),
            ("Minimum applicable", self.detail.applicable_minimum_amount_label),
            ("Source du minimum", self._with_code(self.detail.minimum_source_label, self.detail.minimum_source)),
            ("Territoire", self._with_code(self.detail.territory_label, self.detail.territory)),
            ("Écart salarial", self.detail.shortfall_amount_label),
        )), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer_base.Add(self._section("Résultat", (
            ("Statut", self._with_code(self.detail.status_label, self.detail.status)),
            ("Libellé du statut", self.detail.status_label),
            ("Anomalie", self._pair(self.detail.issue_code_label, self.detail.issue_message_label)),
            ("Motif de non-évaluation", self._pair(self.detail.failure_reason_label, self.detail.failure_message_label)),
            ("Message métier", self.detail.issue_message_label or self.detail.failure_message_label or "Aucun"),
        )), 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer_buttons = wx.StdDialogButtonSizer()
        sizer_buttons.AddButton(self.button_close)
        sizer_buttons.Realize()
        sizer_base.Add(sizer_buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(sizer_base)
        self.Layout()

    def _section(self, title, rows):
        static_box = wx.StaticBox(self, -1, title)
        static_box.SetBackgroundColour(UTILS_Interface.GetToken("surface_container"))
        static_box.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        box = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=8)
        grid.AddGrowableCol(1, 1)
        for label, value in rows:
            grid.Add(wx.StaticText(static_box, -1, label + " :"), 0, wx.ALIGN_TOP)
            text = wx.TextCtrl(
                static_box,
                -1,
                value or "Non renseigné",
                style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE,
            )
            text.SetMinSize((-1, 44))
            grid.Add(text, 1, wx.EXPAND)
        box.Add(grid, 1, wx.ALL | wx.EXPAND, 8)
        return box

    def _with_code(self, label, enum_value):
        if enum_value is None:
            return label or "Non renseigné"
        return "%s (%s)" % (label, enum_value.value)

    def _pair(self, code, message):
        if code and message:
            return "%s — %s" % (code, message)
        return code or message or "Aucun"
