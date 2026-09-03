#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Préférences d'affichage de Teamworks-CCNS."""

import wx

from Ctrl import CTRL_Texte
from Utils import (
    UTILS_Customize,
    UTILS_Envoi_rapport_bug,
    UTILS_Interface,
    UTILS_Styles,
)


_APPEARANCE_LABELS = {
    "system": "Système",
    "light": "Clair",
    "dark": "Sombre",
}


class Dialog(wx.Dialog):
    THEMES = ["Système", "Clair", "Sombre"]
    ACCENTS = list(UTILS_Interface.THEMES)
    APPEARANCES = [
        (code, _APPEARANCE_LABELS.get(code, code))
        for code in UTILS_Interface.APPEARANCE_MODES
    ]

    def __init__(self, parent):
        super().__init__(
            parent,
            title="Préférences Teamworks-CCNS",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        # Ce dialogue contient désormais plusieurs sections : un profil compact
        # le tronquait sur les écrans portables. Le corps défile, le pied reste
        # toujours visible et la fenêtre reste redimensionnable.
        UTILS_Styles.ApplyWindowProfile(self, "standard")

        surface = UTILS_Interface.GetToken("surface")
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(surface)
        shell = wx.BoxSizer(wx.VERTICAL)

        self.body = wx.ScrolledWindow(
            self.panel,
            style=wx.VSCROLL | wx.TAB_TRAVERSAL,
        )
        self.body.SetBackgroundColour(surface)
        self.body.SetScrollRate(0, max(8, UTILS_Styles.Scale(12)))
        main = wx.BoxSizer(wx.VERTICAL)

        title = CTRL_Texte.H1(self.body, "Affichage")
        main.Add(title, 0, wx.LEFT | wx.RIGHT | wx.TOP, padding)

        self.intro = CTRL_Texte.BodySecondary(
            self.body,
            "L'accent colore les actions et sélections. L'apparence pilote les surfaces claires ou sombres.",
        )
        main.Add(self.intro, 0, wx.EXPAND | wx.ALL, padding)

        self.accent = wx.Choice(
            self.body,
            choices=[label for code, label in self.ACCENTS],
        )
        current_accent = UTILS_Interface.GetTheme()
        accent_codes = [code for code, label in self.ACCENTS]
        self.accent.SetSelection(
            accent_codes.index(current_accent) if current_accent in accent_codes else 0
        )
        main.Add(
            self._ligne(self.body, "Accent :", self.accent),
            0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding,
        )

        self.appearance = wx.Choice(
            self.body,
            choices=[label for code, label in self.APPEARANCES],
        )
        current_appearance = UTILS_Interface.GetAppearanceMode()
        appearance_codes = [code for code, label in self.APPEARANCES]
        self.appearance.SetSelection(
            appearance_codes.index(current_appearance)
            if current_appearance in appearance_codes else 0
        )
        main.Add(
            self._ligne(self.body, "Apparence :", self.appearance),
            0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding,
        )

        scale_min = UTILS_Interface.INTERFACE_SCALE_MIN
        scale_default = UTILS_Interface.INTERFACE_SCALE_DEFAULT
        scale_max = UTILS_Interface.INTERFACE_SCALE_MAX
        self.scale = wx.SpinCtrl(
            self.body,
            min=scale_min,
            max=scale_max,
            initial=scale_default,
        )
        try:
            current_scale = UTILS_Customize.GetValeur(
                "interface", "echelle_interface", "",
                ajouter_si_manquant=False,
            )
            if current_scale in (None, ""):
                current_scale = UTILS_Customize.GetValeur(
                    "interface", "echelle_police", str(scale_default),
                    type_valeur=int,
                )
            else:
                current_scale = int(current_scale)
        except Exception:
            current_scale = scale_default
        self.scale.SetValue(max(scale_min, min(scale_max, current_scale)))

        scale_control = wx.BoxSizer(wx.HORIZONTAL)
        scale_control.Add(self.scale, 0)
        scale_control.Add(
            CTRL_Texte.Body(self.body, " %"),
            0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, field_gap // 2,
        )
        main.Add(
            self._ligne(self.body, "Échelle de l'interface :", scale_control),
            0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding,
        )

        self.info = CTRL_Texte.BodySecondary(
            self.body,
            "L'échelle agit ensemble sur les textes, les icônes et les dimensions des contrôles. Les écrans modernisés redistribuent aussi l'espace disponible.",
        )
        main.Add(
            self.info, 0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding,
        )

        main.Add(
            CTRL_Texte.Label(self.body, "Maintenance / Diagnostic"),
            0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding,
        )
        self.adresse_rapport_bugs = wx.TextCtrl(self.body)
        self.adresse_rapport_bugs.SetValue(
            UTILS_Envoi_rapport_bug.GetAdresseRapportBugsConfiguree()
        )
        self.reset_adresse_rapport_bugs = wx.Button(
            self.body,
            label="Rétablir le réglage d'origine",
        )
        adresse_rapport_bugs = wx.BoxSizer(wx.HORIZONTAL)
        adresse_rapport_bugs.Add(self.adresse_rapport_bugs, 1, wx.EXPAND)
        adresse_rapport_bugs.Add(
            self.reset_adresse_rapport_bugs, 0, wx.LEFT, field_gap,
        )
        main.Add(
            self._ligne(
                self.body,
                "Adresse de réception des rapports d'erreurs :",
                adresse_rapport_bugs,
            ),
            0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding,
        )
        self.maintenance_info = CTRL_Texte.BodySecondary(
            self.body,
            "Laissez ce champ vide pour conserver le destinataire historique de l'auteur : noethys@gmail.com. Ce réglage est partagé par la base.",
        )
        main.Add(
            self.maintenance_info, 0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, padding,
        )

        main.Add(
            CTRL_Texte.Label(self.body, "Organisation et références RH"),
            0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding,
        )
        self.organisation_button = wx.Button(
            self.body, label="Structure / association…",
        )
        self.admin_button = wx.Button(
            self.body, label="Références administratives RH…",
        )
        main.Add(
            self.organisation_button, 0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding,
        )
        main.Add(
            self.admin_button, 0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, padding,
        )

        self.body.SetSizer(main)
        self.body.Layout()
        self.body.FitInside()
        shell.Add(self.body, 1, wx.EXPAND)

        # Pied hors de la zone défilante : Valider/Annuler restent accessibles
        # quelle que soit la hauteur de l'écran ou l'échelle de l'interface.
        self.footer = wx.Panel(self.panel)
        self.footer.SetBackgroundColour(surface)
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        footer_sizer.AddStretchSpacer()
        buttons = wx.StdDialogButtonSizer()
        ok_button = wx.Button(self.footer, wx.ID_OK)
        cancel_button = wx.Button(self.footer, wx.ID_CANCEL)
        buttons.AddButton(ok_button)
        buttons.AddButton(cancel_button)
        buttons.Realize()
        footer_sizer.Add(buttons, 0, wx.ALL, padding)
        self.footer.SetSizer(footer_sizer)
        shell.Add(self.footer, 0, wx.EXPAND)

        self.panel.SetSizer(shell)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(outer)

        self.Bind(wx.EVT_BUTTON, self.OnOrganisation, self.organisation_button)
        self.Bind(wx.EVT_BUTTON, self.OnReferencesAdmin, self.admin_button)
        self.Bind(wx.EVT_BUTTON, self.OnResetAdresseRapportBugs, self.reset_adresse_rapport_bugs)
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # Stabilise le premier rendu avant ShowModal : aucun CallAfter de layout.
        self._ajuster_textes()
        self.Layout()
        self.body.FitInside()

    @staticmethod
    def _ligne(parent, label, control):
        ligne = wx.BoxSizer(wx.HORIZONTAL)
        etiquette = CTRL_Texte.Label(parent, label)
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        ligne.Add(etiquette, 2, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, gap)
        ligne.Add(control, 3, wx.EXPAND)
        return ligne

    def OnSize(self, event):
        self._ajuster_textes()
        event.Skip()

    def _ajuster_textes(self):
        try:
            padding = UTILS_Styles.GetLayoutSpacing("dialog_padding") * 2
            largeur = max(
                UTILS_Styles.Scale(240),
                self.body.GetClientSize().GetWidth() - padding,
            )
            for control in (self.intro, self.info, self.maintenance_info):
                control.Wrap(largeur)
            self.body.Layout()
            self.body.FitInside()
        except Exception:
            pass

    def OnOrganisation(self, event):
        from Dlg import DLG_Organisation
        dialog = DLG_Organisation.Dialog(self)
        try:
            dialog.ShowModal()
        finally:
            dialog.Destroy()

    def OnReferencesAdmin(self, event):
        from Dlg import DLG_References_admin
        dialog = DLG_References_admin.Dialog(self)
        try:
            dialog.ShowModal()
        finally:
            dialog.Destroy()

    def OnResetAdresseRapportBugs(self, event):
        self.adresse_rapport_bugs.SetValue("")
        self.adresse_rapport_bugs.SetFocus()

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
            UTILS_Envoi_rapport_bug.SetAdresseRapportBugsConfiguree(
                self.adresse_rapport_bugs.GetValue()
            )
        except Exception:
            wx.MessageBox(
                "Impossible d’enregistrer le destinataire des rapports d’erreurs dans la base.",
                "Préférences non enregistrées",
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
            return

        # Ne plus recolorer à moitié toute l'application pendant la fermeture du
        # dialogue. Sur Windows cela produisait le fond blanc/noir tardif et des
        # icônes qui apparaissaient seulement au rollover. Le prochain démarrage
        # applique l'apparence native avant la création des fenêtres.
        try:
            from Utils import UTILS_Theme
            UTILS_Theme.refresh_preferences()
        except Exception:
            pass

        wx.MessageBox(
            "Préférences enregistrées. Redémarrez Teamworks-CCNS pour appliquer complètement l'apparence et l'échelle.",
            "Préférences enregistrées",
            wx.OK | wx.ICON_INFORMATION,
            parent=self,
        )
        self.EndModal(wx.ID_OK)
