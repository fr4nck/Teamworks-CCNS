#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Préférences d'affichage et de branding de Teamworks CCNS."""

import os

import wx

from Utils import UTILS_Branding
from Utils import UTILS_Customize


class Dialog(wx.Dialog):
    THEMES = ["Système", "Clair", "Sombre"]

    def __init__(self, parent):
        super().__init__(parent, title="Préférences d'affichage", size=(620, 430))

        self.initial_logo_path = UTILS_Branding.GetAssociationLogoPath()
        self.remove_logo = False

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

        branding_title = wx.StaticText(panel, label="Personnalisation de l'organisation")
        branding_font = branding_title.GetFont()
        branding_font.SetWeight(wx.FONTWEIGHT_BOLD)
        branding_title.SetFont(branding_font)
        main.Add(branding_title, 0, wx.LEFT | wx.RIGHT | wx.TOP, 16)

        logo_row = wx.BoxSizer(wx.HORIZONTAL)
        self.logo_picker = wx.FilePickerCtrl(
            panel,
            path=self.initial_logo_path,
            message="Sélectionner le logo de l'organisation",
            wildcard="Images (*.png;*.jpg;*.jpeg;*.bmp)|*.png;*.jpg;*.jpeg;*.bmp",
            style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL,
        )
        logo_row.Add(self.logo_picker, 1, wx.EXPAND | wx.RIGHT, 8)
        self.remove_button = wx.Button(panel, label="Retirer")
        logo_row.Add(self.remove_button, 0)
        main.Add(logo_row, 0, wx.EXPAND | wx.ALL, 16)

        hint = wx.StaticText(
            panel,
            label=(
                "PNG transparent recommandé. Le fichier est copié dans le dossier utilisateur de "
                "Teamworks CCNS : une mise à jour du logiciel ne l'écrasera pas."
            ),
        )
        hint.Wrap(570)
        main.Add(hint, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

        main.Add(
            wx.StaticText(
                panel,
                label="Les changements sont appliqués après redémarrage de Teamworks CCNS.",
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

        self.Bind(wx.EVT_BUTTON, self.OnRemoveLogo, self.remove_button)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnLogoChanged, self.logo_picker)
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.CentreOnParent()

    def OnRemoveLogo(self, event):
        self.remove_logo = True
        self.logo_picker.SetPath("")

    def OnLogoChanged(self, event):
        self.remove_logo = False
        event.Skip()

    def OnOk(self, event):
        values = ["Systeme", "Clair", "Sombre"]
        UTILS_Customize.SetValeur(
            "interface", "theme", values[max(0, self.theme.GetSelection())]
        )
        UTILS_Customize.SetValeur(
            "interface", "echelle_police", str(self.scale.GetValue())
        )

        try:
            selected_logo = self.logo_picker.GetPath().strip()
            if self.remove_logo:
                UTILS_Branding.ClearAssociationLogo()
            elif selected_logo and os.path.abspath(selected_logo) != os.path.abspath(self.initial_logo_path or ""):
                UTILS_Branding.SetAssociationLogo(selected_logo)
        except (OSError, ValueError) as exc:
            wx.MessageBox(
                str(exc),
                "Logo non enregistré",
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
            return

        wx.MessageBox(
            "Les préférences seront appliquées au prochain démarrage.",
            "Préférences enregistrées",
            wx.OK | wx.ICON_INFORMATION,
            parent=self,
        )
        self.EndModal(wx.ID_OK)
