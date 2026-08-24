#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts
from Utils import UTILS_Interface, UTILS_Theme


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Audit CCNS des contrats", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.palette = UTILS_Interface.GetPalette()
        self.ui = UTILS_Theme.metrics()

        self.label_intro = wx.StaticText(
            self,
            -1,
            "Cet outil relit les contrats Teamworks et applique les premiers contrôles CCNS disponibles.",
        )
        self.label_intro.SetForegroundColour(self.palette["on_surface_variant"])

        self.box_parameters = wx.StaticBox(self, -1, "Périmètre de l'audit")
        self.box_parameters.SetBackgroundColour(self.palette["surface_container"])
        self.box_parameters.SetForegroundColour(self.palette["on_surface"])
        self.label_limit = wx.StaticText(self.box_parameters, -1, "Nombre maximal de contrats à auditer :")
        self.ctrl_limit = wx.SpinCtrl(self.box_parameters, -1, min=1, max=5000, initial=200)

        self.box_result = wx.StaticBox(self, -1, "Résultat")
        self.box_result.SetBackgroundColour(self.palette["surface_container"])
        self.box_result.SetForegroundColour(self.palette["on_surface"])
        self.text_result = wx.TextCtrl(
            self.box_result,
            -1,
            "",
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
        )
        self.text_result.SetBackgroundColour(self.palette["surface_container_lowest"])
        self.text_result.SetForegroundColour(self.palette["on_surface"])

        self.button_launch = wx.Button(self, -1, "Lancer l'audit")
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")

        self.button_launch.Bind(wx.EVT_BUTTON, self.OnLaunch)

        self.__do_layout()
        self.SetMinSize((760, 500))
        self.CentreOnScreen()

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(
            self.label_intro,
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            self.ui["space_l"],
        )

        sizer_parameters = wx.StaticBoxSizer(self.box_parameters, wx.VERTICAL)
        row_parameters = wx.BoxSizer(wx.HORIZONTAL)
        row_parameters.Add(
            self.label_limit,
            0,
            wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
            self.ui["space_s"],
        )
        row_parameters.Add(self.ctrl_limit, 0, 0, 0)
        sizer_parameters.Add(row_parameters, 0, wx.ALL, self.ui["space_m"])
        sizer_base.Add(
            sizer_parameters,
            0,
            wx.ALL | wx.EXPAND,
            self.ui["space_l"],
        )

        sizer_result = wx.StaticBoxSizer(self.box_result, wx.VERTICAL)
        sizer_result.Add(
            self.text_result,
            1,
            wx.ALL | wx.EXPAND,
            self.ui["space_m"],
        )
        sizer_base.Add(
            sizer_result,
            1,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            self.ui["space_l"],
        )

        sizer_buttons = wx.StdDialogButtonSizer()
        sizer_buttons.AddButton(self.button_launch)
        sizer_buttons.AddButton(self.button_close)
        sizer_buttons.Realize()
        sizer_base.Add(
            sizer_buttons,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT,
            self.ui["space_l"],
        )

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
        lines.append("Audit CCNS terminé")
        lines.append("Contrats audités : %d" % len(rows))
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
