#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Préférences d'affichage de Teamworks-CCNS."""

import wx

from Utils import UTILS_Customize
from Utils import UTILS_Interface


class Dialog(wx.Dialog):
    # Contrat historique TW-121 conservé pour compatibilité et tests.
    THEMES = ["Système", "Clair", "Sombre"]

    ACCENTS = [
        ("Vert", "Vert"),
        ("Bleu", "Bleu"),
        ("Noir", "Neutre"),
    ]
    APPEARANCES = [
        ("system", "Système"),
        ("light", "Clair"),
        ("dark", "Sombre"),
    ]

    def __init__(self, parent):
        super().__init__(parent, title="Préférences d'affichage", size=(500, 350))

        panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Affichage")
        font = title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        main.Add(title, 0, wx.ALL, 12)

        intro = wx.StaticText(
            panel,
            label=(
                "L'accent colore les actions et sélections. "
                "L'apparence pilote les surfaces claires ou sombres."
            ),
        )
        intro.Wrap(440)
        main.Add(intro, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        grid = wx.FlexGridSizer(3, 2, 12, 12)
        grid.AddGrowableCol(1, 1)

        grid.Add(wx.StaticText(panel, label="Accent :"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.accent = wx.Choice(panel, choices=[label for code, label in self.ACCENTS])
        current_accent = UTILS_Interface.GetTheme()
        accent_codes = [code for code, label in self.ACCENTS]
        self.accent.SetSelection(
            accent_codes.index(current_accent) if current_accent in accent_codes else 0
        )
        grid.Add(self.accent, 1, wx.EXPAND)

        grid.Add(wx.StaticText(panel, label="Apparence :"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.appearance = wx.Choice(
            panel,
            choices=[label for code, label in self.APPEARANCES],
        )
        current_appearance = UTILS_Interface.GetAppearanceMode()
        appearance_codes = [code for code, label in self.APPEARANCES]
        self.appearance.SetSelection(
            appearance_codes.index(current_appearance)
            if current_appearance in appearance_codes
            else 0
        )
        grid.Add(self.appearance, 1, wx.EXPAND)

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
        main.Add(
            wx.StaticText(
                panel,
                label=(
                    "La palette est enregistrée immédiatement. Un redémarrage reste "
                    "recommandé pour appliquer complètement le mode sombre natif de Windows."
                ),
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
        accent_codes = [code for code, label in self.ACCENTS]
        appearance_codes = [code for code, label in self.APPEARANCES]

        accent_index = max(0, self.accent.GetSelection())
        appearance_index = max(0, self.appearance.GetSelection())

        UTILS_Interface.SetTheme(accent_codes[accent_index])
        UTILS_Interface.SetAppearanceMode(appearance_codes[appearance_index])
        UTILS_Customize.SetValeur(
            "interface",
            "echelle_police",
            str(self.scale.GetValue()),
        )

        try:
            from Utils import UTILS_Theme
            UTILS_Theme.refresh_preferences()
            top = wx.GetApp().GetTopWindow()
            UTILS_Theme.apply_to_window(top, True)
        except Exception:
            pass

        wx.MessageBox(
            "Préférences enregistrées. Le mode sombre natif sera complet au prochain démarrage.",
            "Préférences enregistrées",
            wx.OK | wx.ICON_INFORMATION,
            parent=self,
        )
        self.EndModal(wx.ID_OK)
