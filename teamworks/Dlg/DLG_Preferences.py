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
        super().__init__(parent, title="Préférences d'affichage", size=(540, 410))

        panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Affichage")
        font = title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(max(font.GetPointSize() + 3, 12))
        title.SetFont(font)
        main.Add(title, 0, wx.LEFT | wx.RIGHT | wx.TOP, 16)

        intro = wx.StaticText(
            panel,
            label=(
                "L'accent colore les actions et sélections. "
                "L'apparence pilote les surfaces claires ou sombres."
            ),
        )
        intro.Wrap(490)
        main.Add(intro, 0, wx.EXPAND | wx.ALL, 16)

        self.accent = wx.Choice(panel, choices=[label for code, label in self.ACCENTS])
        current_accent = UTILS_Interface.GetTheme()
        accent_codes = [code for code, label in self.ACCENTS]
        self.accent.SetSelection(
            accent_codes.index(current_accent) if current_accent in accent_codes else 0
        )
        main.Add(self._ligne(panel, "Accent :", self.accent), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

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
        main.Add(self._ligne(panel, "Apparence :", self.appearance), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

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

        scale_control = wx.BoxSizer(wx.HORIZONTAL)
        scale_control.Add(self.scale, 0)
        scale_control.Add(wx.StaticText(panel, label=" %"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
        main.Add(
            self._ligne(panel, "Échelle de l'interface :", scale_control),
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            16,
        )

        info = wx.StaticText(
            panel,
            label=(
                "L'échelle agit ensemble sur les textes, les icônes et les dimensions "
                "des contrôles. Les écrans modernisés redistribuent aussi l'espace disponible."
            ),
        )
        info.Wrap(490)
        main.Add(info, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

        main.AddStretchSpacer()

        buttons = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK)
        cancel_button = wx.Button(panel, wx.ID_CANCEL)
        buttons.AddButton(ok_button)
        buttons.AddButton(cancel_button)
        buttons.Realize()
        main.Add(buttons, 0, wx.EXPAND | wx.ALL, 16)
        panel.SetSizer(main)

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.CentreOnParent()

    @staticmethod
    def _ligne(parent, label, control):
        ligne = wx.BoxSizer(wx.HORIZONTAL)
        etiquette = wx.StaticText(parent, label=label)
        etiquette.SetMinSize((180, -1))
        ligne.Add(etiquette, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        if isinstance(control, wx.Sizer):
            ligne.Add(control, 1, wx.ALIGN_CENTER_VERTICAL)
        else:
            ligne.Add(control, 1, wx.EXPAND)
        return ligne

    def OnOk(self, event):
        accent_codes = [code for code, label in self.ACCENTS]
        appearance_codes = [code for code, label in self.APPEARANCES]

        accent_index = max(0, self.accent.GetSelection())
        appearance_index = max(0, self.appearance.GetSelection())

        # Chaque préférence a désormais une responsabilité unique. La couche
        # Interface maintient elle-même la vieille clé ``theme`` pour TW-121.
        UTILS_Interface.SetTheme(accent_codes[accent_index])
        UTILS_Interface.SetAppearanceMode(appearance_codes[appearance_index])

        scale = str(self.scale.GetValue())
        # Nouvelle clé explicite + miroir historique pour les profils existants.
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
