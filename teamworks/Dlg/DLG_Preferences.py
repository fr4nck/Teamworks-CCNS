#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Préférences d'affichage de Teamworks-CCNS."""

import wx

from Ctrl import CTRL_Texte
from Utils import UTILS_Customize, UTILS_Interface, UTILS_Styles


class Dialog(wx.Dialog):
    # Contrat historique TW-121 conservé pour compatibilité et tests.
    THEMES = ["Système", "Clair", "Sombre"]

    # Source unique : tout thème ajouté dans UTILS_Interface apparaît ici
    # automatiquement, sans seconde liste à maintenir dans le dialogue.
    ACCENTS = list(UTILS_Interface.THEMES)
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
        UTILS_Styles.ApplyWindowProfile(self, "compact")

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        main = wx.BoxSizer(wx.VERTICAL)
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")

        title = CTRL_Texte.H1(self.panel, "Affichage")
        main.Add(title, 0, wx.LEFT | wx.RIGHT | wx.TOP, padding)

        self.intro = CTRL_Texte.BodySecondary(
            self.panel,
            (
                "L'accent colore les actions et sélections. "
                "L'apparence pilote les surfaces claires ou sombres."
            ),
        )
        main.Add(self.intro, 0, wx.EXPAND | wx.ALL, padding)

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
            padding,
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
            padding,
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
            CTRL_Texte.Body(self.panel, " %"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
            field_gap // 2,
        )
        main.Add(
            self._ligne(self.panel, "Échelle de l'interface :", scale_control),
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            padding,
        )

        self.info = CTRL_Texte.BodySecondary(
            self.panel,
            (
                "L'échelle agit ensemble sur les textes, les icônes et les dimensions "
                "des contrôles. Les écrans modernisés redistribuent aussi l'espace disponible."
            ),
        )
        main.Add(
            self.info,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            padding,
        )

        main.AddStretchSpacer()

        buttons = wx.StdDialogButtonSizer()
        ok_button = wx.Button(self.panel, wx.ID_OK)
        cancel_button = wx.Button(self.panel, wx.ID_CANCEL)
        buttons.AddButton(ok_button)
        buttons.AddButton(cancel_button)
        buttons.Realize()
        main.Add(buttons, 0, wx.EXPAND | wx.ALL, padding)
        self.panel.SetSizer(main)

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(shell)

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        wx.CallAfter(self._ajuster_textes)

    @staticmethod
    def _ligne(parent, label, control):
        """Ligne flexible : le libellé et le contrôle partagent l'espace."""
        ligne = wx.BoxSizer(wx.HORIZONTAL)
        etiquette = CTRL_Texte.Label(parent, label)
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        ligne.Add(etiquette, 2, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, gap)
        if isinstance(control, wx.Sizer):
            ligne.Add(control, 3, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        else:
            ligne.Add(control, 3, wx.EXPAND)
        return ligne

    def OnSize(self, event):
        wx.CallAfter(self._ajuster_textes)
        event.Skip()

    def _ajuster_textes(self):
        try:
            padding = UTILS_Styles.GetLayoutSpacing("dialog_padding") * 2
            largeur = max(
                UTILS_Styles.Scale(240),
                self.panel.GetClientSize().GetWidth() - padding,
            )
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
