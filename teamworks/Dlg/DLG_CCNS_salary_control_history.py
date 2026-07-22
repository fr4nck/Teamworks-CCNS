#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from application.presentation import format_euro_amount, format_french_date
from teamworks.CcnsCore.audit_salary_history import list_salary_control_snapshots


class Dialog(wx.Dialog):
    def __init__(self, parent, repository=None):
        wx.Dialog.__init__(self, parent, -1, "Historique des contrôles salariaux", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.repository = repository
        self.snapshots = list(list_salary_control_snapshots(repository=repository))
        self.listbox = wx.ListBox(self, -1, choices=[self._summary(s) for s in self.snapshots])
        self.details = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")
        self.listbox.Bind(wx.EVT_LISTBOX, self.OnSelect)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.listbox, 1, wx.ALL | wx.EXPAND, 8)
        sizer.Add(self.details, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        sizer.Add(self.button_close, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 8)
        self.SetSizer(sizer)
        self.SetSize((980, 680))
        if self.snapshots:
            self.listbox.SetSelection(0)
            self._show(self.snapshots[0])

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
