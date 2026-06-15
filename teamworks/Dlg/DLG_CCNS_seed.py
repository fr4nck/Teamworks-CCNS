#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from teamworks.CcnsCore.seed_teamworks_reference_data import seed_teamworks_reference_data


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Initialiser les donnees CCNS", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.label_intro = wx.StaticText(
            self,
            -1,
            "Cet assistant injecte des donnees de reference CCNS dans Teamworks.\n"
            "Il peut alimenter les tables historiques et les nouvelles tables tw_*.",
        )

        self.checkbox_sync_legacy = wx.CheckBox(self, -1, "Synchroniser aussi les tables historiques (contrats_class, contrats_types)")
        self.checkbox_sync_legacy.SetValue(True)

        self.checkbox_show_details = wx.CheckBox(self, -1, "Afficher le detail des insertions")
        self.checkbox_show_details.SetValue(True)

        self.text_result = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)

        self.button_launch = wx.Button(self, -1, "Lancer l'initialisation")
        self.button_close = wx.Button(self, wx.ID_CANCEL, "Fermer")

        self.button_launch.Bind(wx.EVT_BUTTON, self.OnLaunch)

        self.__do_layout()
        self.SetMinSize((620, 420))
        self.CentreOnScreen()

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_intro, 0, wx.ALL | wx.EXPAND, 10)
        sizer_base.Add(self.checkbox_sync_legacy, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        sizer_base.Add(self.checkbox_show_details, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        sizer_base.Add(self.text_result, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons.Add(self.button_launch, 0, wx.RIGHT, 8)
        sizer_buttons.Add(self.button_close, 0, 0, 0)

        sizer_base.Add(sizer_buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(sizer_base)
        self.Layout()

    def OnLaunch(self, event):
        sync_legacy = self.checkbox_sync_legacy.GetValue()
        show_details = self.checkbox_show_details.GetValue()

        try:
            result = seed_teamworks_reference_data(sync_legacy_tables=sync_legacy)
        except Exception as exc:
            wx.MessageBox(
                "Une erreur est survenue pendant l'initialisation CCNS.\n\n%s" % exc,
                "Erreur",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        lines = ["Initialisation CCNS terminee."]
        if show_details:
            for key in sorted(result.keys()):
                lines.append("- %s : %d" % (key, result[key]))
        else:
            total = sum(result.values())
            lines.append("- total inserts : %d" % total)

        self.text_result.SetValue("\n".join(lines))
        wx.MessageBox(
            "Les donnees de reference CCNS ont ete initialisees.",
            "Operation terminee",
            wx.OK | wx.ICON_INFORMATION,
            self,
        )


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
