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
        super().__init__(
            parent,
            title="Préférences d'affichage",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetMinSize((460, 340))
        self.SetSize((560, 430))

        self.panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(self.panel, label="Affichage")
        font = title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(max(font.GetPointSize() + 3, 12))
        title.SetFont(font)
        main.Add(title, 0, wx.LEFT | wx.RIGHT | wx.TOP, 16)

        self.intro = wx.StaticText(
            self.panel,
            label=(
                "L'accent colore les actions et sélections. "
                "L'apparence pilote les surfaces claires ou sombres."
            ),
        )
        main.Add(self.intro, 0, wx.EXPAND | wx.ALL, 16)

        self.accent = wx.Choice(
            self.panel,
            choices=[label for code, label in self.ACCENTS],
        )
        current_accent = UTILS_Interface.GetTheme()
        accent_codes = [code for code, label in self.ACCENTS]
        self.accent.SetSelection(
            accent_codes.index(current_accent) if current_accent in accent_codes else 0
        )
        main.Add(
            self._ligne(self.panel, "Accent :", self.accent),
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            16,
        )

        self.appearance = wx.Choice(
            self.panel,
            choices=[label for code, label in self.APPEARANCES],
        )
        current_appearance = UTILS_Interface.GetAppearanceMode()
        appearance_codes = [code for code, label in self.APPEARANCES]
        self.appearance.SetSelection(
            appearance_codes.index(current_appearance)
            if current_appearance in appearance_codes
            else 0
        )
        main.Add(
            self._ligne(self.panel, "Apparence :", self.appearance),
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            16,
        )

        self.scale = wx.SpinCtrl(self.panel, min=80, max=200, initial=100)
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

        scale_control = wx.BoxSizer(wx.HORIZONTAL)
        scale_control.Add(self.scale, 0)
        scale_control.Add(
            wx.StaticText(self.panel, label=" %"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
            4,
        )
        main.Add(
            self._ligne(self.panel, "Échelle de l'interface :", scale_control),
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            16,
        )

        self.info = wx.StaticText(
            self.panel,
            label=(
                "L'échelle agit ensemble sur les textes, les icônes et les dimensions "
                "des contrôles. Les écrans modernisés redistribuent aussi l'espace disponible."
            ),
        )
        main.Add(
            self.info,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            16,
        )

        main.AddStretchSpacer()

        buttons = wx.StdDialogButtonSizer()
        ok_button = wx.Button(self.panel, wx.ID_OK)
        cancel_button = wx.Button(self.panel, wx.ID_CANCEL)
        buttons.AddButton(ok_button)
        buttons.AddButton(cancel_button)
        buttons.Realize()
        main.Add(buttons, 0, wx.EXPAND | wx.ALL, 16)
        self.panel.SetSizer(main)

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(shell)

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.CentreOnParent()
        wx.CallAfter(self._ajuster_textes)

    @staticmethod
    def _ligne(parent, label, control):
        """Ligne sans séparateur à largeur figée : le texte garde son BestSize."""
        ligne = wx.BoxSizer(wx.HORIZONTAL)
        etiquette = wx.StaticText(parent, label=label)
        ligne.Add(etiquette, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        if isinstance(control, wx.Sizer):
            ligne.Add(control, 1, wx.ALIGN_CENTER_VERTICAL)
        else:
            ligne.Add(control, 1, wx.EXPAND)
        return ligne

    def OnSize(self, event):
        wx.CallAfter(self._ajuster_textes)
        event.Skip()

    def _ajuster_textes(self):
        try:
            largeur = max(240, self.panel.GetClientSize().GetWidth() - 32)
            self.intro.Wrap(largeur)
            self.info.Wrap(largeur)
            self.panel.Layout()
        except Exception:
            pass

    def OnOk(self, event):
        accent_codes = [code for code, label in self.ACCENTS]
        appearance_codes = [code for code, label in self.APPEARANCES]

        accent_index = max(0, self.accent.GetSelection())
        appearance_index = max(0, self.appearance.GetSelection())

        UTILS_Interface.SetTheme(accent_codes[accent_index])
        UTILS_Interface.SetAppearanceMode(appearance_codes[appearance_index])

        scale = str(self.scale.GetValue())
        UTILS_Customize.SetValeur("interface", "echelle_interface", scale)
        UTILS_Customize.SetValeur("interface", "echelle_police", scale)

        try:
            from Utils import UTILS_Theme
            UTILS_Theme.refresh_preferences()
            top = wx.GetApp().GetTopWindow()
            UTILS_Theme.apply_to_window(top, True)
        except Exception:
            pass

        wx.MessageBox(
            "Préférences enregistrées. Un redémarrage reste recommandé pour le mode sombre natif.",
            "Préférences enregistrées",
            wx.OK | wx.ICON_INFORMATION,
            parent=self,
        )
        self.EndModal(wx.ID_OK)
