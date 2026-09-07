#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging

import wx

from Ctrl import CTRL_Bouton_image
from teamworks.CcnsCore.seed_teamworks_reference_data import seed_teamworks_reference_data
from Utils import UTILS_Styles


LOGGER = logging.getLogger(__name__)


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Initialiser les données CCNS", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.label_intro = wx.StaticText(
            self,
            -1,
            "Cet assistant injecte des données de référence CCNS dans Teamworks.\n"
            "Il peut alimenter les tables historiques et les nouvelles tables de référence.",
        )

        self.checkbox_sync_legacy = wx.CheckBox(self, -1, "Synchroniser aussi les tables historiques (contrats_class, contrats_types)")
        self.checkbox_sync_legacy.SetValue(True)

        self.checkbox_show_details = wx.CheckBox(self, -1, "Afficher le détail des insertions")
        self.checkbox_show_details.SetValue(True)

        self.text_result = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)

        self.button_launch = CTRL_Bouton_image.CTRL(
            self,
            texte="Lancer l'initialisation",
            role="primary",
        )
        self.button_close = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte="Fermer",
            role="quiet",
        )

        self.button_launch.Bind(wx.EVT_BUTTON, self.OnLaunch)

        self.__do_layout()
        UTILS_Styles.ApplyWindowProfile(self, "standard")
        self.checkbox_sync_legacy.SetFocus()

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
        except Exception:
            LOGGER.exception("Échec de l'initialisation des données CCNS")
            wx.MessageBox(
                "Les données de référence CCNS n'ont pas pu être initialisées. Vérifiez l'accès aux données puis réessayez.",
                "Initialisation impossible",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        lines = ["Initialisation CCNS terminée."]
        if show_details:
            for key in sorted(result.keys()):
                lines.append("- %s : %d" % (key, result[key]))
        else:
            total = sum(result.values())
            lines.append("- total des insertions : %d" % total)

        self.text_result.SetValue("\n".join(lines))
        wx.MessageBox(
            "Les données de référence CCNS ont été initialisées.",
            "Opération terminée",
            wx.OK | wx.ICON_INFORMATION,
            self,
        )


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
