#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Préférences d'affichage et de branding de Teamworks CCNS."""

import wx

from Utils import UTILS_Customize


class Dialog(wx.Dialog):
    THEMES = ["Système", "Clair", "Sombre"]

    def __init__(self, parent):
        super().__init__(parent, title="Préférences d'affichage", size=(620, 390))

        panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Affichage")
        font = title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        main.Add(title, 0, wx.ALL, 12)

        grid = wx.FlexGridSizer(2, 2, 12, 12)
        grid.AddGrowableCol(1, 1)

        grid.Add(wx.StaticText(panel, label="Thème :"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.theme = wx.Choice(panel, choices=self.THEMES)
        current_theme = UTILS_Customize.GetValeur("interface", "theme", "Systeme")
        normalized = current_theme.lower().replace("è", "e")
        index = 0
        if normalized in ("clair", "light", "blanc"):
            index = 1
        elif normalized in ("sombre", "dark", "noir"):
            index = 2
        self.theme.SetSelection(index)
        grid.Add(self.theme, 1, wx.EXPAND)

        grid.Add(wx.StaticText(panel, label="Taille des polices :"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.scale = wx.SpinCtrl(panel, min=80, max=200, initial=100)
        try:
            current_scale = UTILS_Customize.GetValeur(
                "interface", "echelle_police", "100", type_valeur=int
            )
        except Exception:
            current_scale = 100
        self.scale.SetValue(max(80, min(200, current_scale)))

        scale_row = wx.BoxSizer(wx.HORIZONTAL)
        scale_row.Add(self.scale, 0)
        scale_row.Add(wx.StaticText(panel, label=" %"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
        grid.Add(scale_row, 0, wx.ALIGN_LEFT)
        main.Add(grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)

        organisation_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Structure / Association")
        description = wx.StaticText(
            panel,
            label=(
                "Identité, coordonnées, RNA/SIRET, agrément, assurance, représentant légal, logo "
                "et mentions affichées sur les documents."
            ),
        )
        description.Wrap(560)
        organisation_box.Add(description, 0, wx.EXPAND | wx.ALL, 10)
        self.organisation_button = wx.Button(panel, label="Configurer la structure / association…")
        organisation_box.Add(self.organisation_button, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        main.Add(organisation_box, 0, wx.EXPAND | wx.ALL, 16)

        main.Add(
            wx.StaticText(
                panel,
                label="Le changement de thème et de taille de police est appliqué après redémarrage.",
            ),
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM,
            16,
        )
        main.AddStretchSpacer()

        buttons = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK)
        cancel_button = wx.Button(panel, wx.ID_CANCEL)
        buttons.AddButton(ok_button)
        buttons.AddButton(cancel_button)
        buttons.Realize()
        main.Add(buttons, 0, wx.EXPAND | wx.ALL, 12)
        panel.SetSizer(main)

        self.Bind(wx.EVT_BUTTON, self.OnOrganisation, self.organisation_button)
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.CentreOnParent()

    def OnOrganisation(self, event):
        from Dlg import DLG_Organisation

        dialog = DLG_Organisation.Dialog(self)
        try:
            dialog.ShowModal()
        finally:
            dialog.Destroy()

    def OnOk(self, event):
        values = ["Systeme", "Clair", "Sombre"]
        UTILS_Customize.SetValeur(
            "interface", "theme", values[max(0, self.theme.GetSelection())]
        )
        UTILS_Customize.SetValeur(
            "interface", "echelle_police", str(self.scale.GetValue())
        )

        wx.MessageBox(
            "Les préférences d'affichage seront appliquées au prochain démarrage.",
            "Préférences enregistrées",
            wx.OK | wx.ICON_INFORMATION,
            parent=self,
        )
        self.EndModal(wx.ID_OK)
