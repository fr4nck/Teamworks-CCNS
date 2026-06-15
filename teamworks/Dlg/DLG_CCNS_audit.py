#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Audit CCNS des contrats", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.label_intro = wx.StaticText(
            self,
            -1,
            "Cet outil relit les contrats Teamworks et applique les premiers controles CCNS disponibles.",
        )

        self.label_limit = wx.StaticText(self, -1, "Nombre maximal de contrats a auditer :")
        self.ctrl_limit = wx.SpinCtrl(self, -1, min=1, max=5000, initial=200)

        self.button_launch = wx.Button(self, -1, "Lancer l'audit")
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")
        self.text_result = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)

        self.button_launch.Bind(wx.EVT_BUTTON, self.OnLaunch)

        self.__do_layout()
        self.SetMinSize((760, 500))
        self.CentreOnScreen()

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_intro, 0, wx.ALL | wx.EXPAND, 10)

        sizer_limit = wx.BoxSizer(wx.HORIZONTAL)
        sizer_limit.Add(self.label_limit, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        sizer_limit.Add(self.ctrl_limit, 0, 0, 0)
        sizer_base.Add(sizer_limit, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        sizer_base.Add(self.text_result, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons.Add(self.button_launch, 0, wx.RIGHT, 8)
        sizer_buttons.Add(self.button_close, 0, 0, 0)
        sizer_base.Add(sizer_buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        self.SetSizer(sizer_base)
        self.Layout()

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

        lines = []
        lines.append("Audit CCNS termine")
        lines.append("Contrats audites : %d" % len(rows))
        lines.append("")

        for row in rows:
            lines.append("[%s] %s" % (row.IDcontrat, row.nom_complet))
            lines.append("  - classification : %s" % (row.classification or ""))
            lines.append("  - type : %s" % (row.type_contrat or ""))
            lines.append("  - anomalies : %s" % (", ".join(row.anomalies) if row.anomalies else "aucune"))
            for message in row.messages:
                lines.append("    * %s" % message)
            lines.append("")

        self.text_result.SetValue("\n".join(lines))
