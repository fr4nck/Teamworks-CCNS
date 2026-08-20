#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Préférences d'affichage de Teamworks-CCNS."""

import wx

from Utils import UTILS_Customize


class Dialog(wx.Dialog):
    THEMES = ["Système", "Clair", "Sombre"]

    def __init__(self, parent):
        super().__init__(parent, title="Préférences d'affichage", size=(480, 320))

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

        grid.Add(wx.StaticText(panel, label="Échelle de l'interface :"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.scale = wx.SpinCtrl(panel, min=80, max=200, initial=100)
        try:
            current_scale = UTILS_Customize.GetValeur(
                "interface",
                "echelle_interface",
                "",
                ajouter_si_manquant=False,
            )
            if current_scale in (None, ""):
                current_scale = UTILS_Customize.GetValeur(
                    "interface", "echelle_police", "100", type_valeur=int
                )
            else:
                current_scale = int(current_scale)
        except Exception:
            current_scale = 100
        self.scale.SetValue(max(80, min(200, current_scale)))

        scale_row = wx.BoxSizer(wx.HORIZONTAL)
        scale_row.Add(self.scale, 0)
        scale_row.Add(wx.StaticText(panel, label=" %"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
        grid.Add(scale_row, 0, wx.ALIGN_LEFT)

        main.Add(grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)
        main.Add(
            wx.StaticText(
                panel,
                label=(
                    "L'échelle agit ensemble sur les textes, les icônes, les barres d'outils "
                    "et la hauteur des contrôles."
                ),
            ),
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            16,
        )
        main.Add(
            wx.StaticText(
                panel,
                label="Les changements sont appliqués après redémarrage de Teamworks-CCNS.",
            ),
            0,
            wx.ALL,
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

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.CentreOnParent()

    def OnOk(self, event):
        values = ["Systeme", "Clair", "Sombre"]
        UTILS_Customize.SetValeur(
            "interface", "theme", values[max(0, self.theme.GetSelection())]
        )
        scale = str(self.scale.GetValue())
        # Nouvelle clé explicite + miroir historique pour les versions antérieures.
        UTILS_Customize.SetValeur("interface", "echelle_interface", scale)
        UTILS_Customize.SetValeur("interface", "echelle_police", scale)
        wx.MessageBox(
            "Les préférences seront appliquées au prochain démarrage.",
            "Préférences enregistrées",
            wx.OK | wx.ICON_INFORMATION,
            parent=self,
        )
        self.EndModal(wx.ID_OK)
