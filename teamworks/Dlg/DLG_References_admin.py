#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pense-bête des références administratives RH de Teamworks CCNS."""

import wx

from Utils import UTILS_References_admin
from Utils import UTILS_Styles


FIELD_ROLES = {
    "medecine_identifiant": UTILS_Styles.FIELD_CODE,
    "medecine_telephone": UTILS_Styles.FIELD_PHONE,
    "urssaf_identifiant": UTILS_Styles.FIELD_CODE,
    "mutuelle_reference": UTILS_Styles.FIELD_CODE,
    "prevoyance_reference": UTILS_Styles.FIELD_CODE,
    "opco_identifiant": UTILS_Styles.FIELD_CODE,
    "retraite_identifiant": UTILS_Styles.FIELD_CODE,
    "assurance_reference": UTILS_Styles.FIELD_CODE,
    "assurance_telephone": UTILS_Styles.FIELD_PHONE,
}


class Dialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Références administratives RH", size=(860, 720))
        self.profile = UTILS_References_admin.GetProfil()
        self.controls = {}

        panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Références administratives RH")
        font = title.GetFont()
        font.SetPointSize(max(12, font.GetPointSize() + 3))
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        main.Add(title, 0, wx.LEFT | wx.RIGHT | wx.TOP, 14)

        subtitle = wx.StaticText(
            panel,
            label=(
                "Pense-bête interne pour les organismes RH et leurs références. "
                "Ne stockez ici aucun mot de passe ni secret."
            ),
        )
        subtitle.Wrap(810)
        main.Add(subtitle, 0, wx.ALL, 14)

        notebook = wx.Notebook(panel)
        notebook.AddPage(self._build_health_page(notebook), "Santé au travail")
        notebook.AddPage(self._build_social_page(notebook), "Social & protection")
        notebook.AddPage(self._build_insurance_page(notebook), "Assurance employeur")
        notebook.AddPage(self._build_notes_page(notebook), "Notes")
        main.Add(notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 14)

        buttons = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK)
        cancel_button = wx.Button(panel, wx.ID_CANCEL)
        buttons.AddButton(ok_button)
        buttons.AddButton(cancel_button)
        buttons.Realize()
        main.Add(buttons, 0, wx.EXPAND | wx.ALL, 14)
        panel.SetSizer(main)

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.CentreOnParent()

    def _text(self, parent, key, style=0):
        ctrl = wx.TextCtrl(parent, value=self.profile.get(key, ""), style=style)
        role = UTILS_Styles.FIELD_LONG_TEXT if style & wx.TE_MULTILINE else FIELD_ROLES.get(
            key, UTILS_Styles.FIELD_TEXT
        )
        UTILS_Styles.ApplyFieldRole(ctrl, role)
        self.controls[key] = ctrl
        return ctrl

    def _row(self, parent, grid, label, key):
        grid.Add(wx.StaticText(parent, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
        role = FIELD_ROLES.get(key, UTILS_Styles.FIELD_TEXT)
        grid.Add(
            self._text(parent, key),
            1 if UTILS_Styles.FieldExpands(role) else 0,
            UTILS_Styles.GetFieldSizerFlag(role),
        )

    def _grid_page(self, parent, rows):
        page = wx.Panel(parent)
        grid = wx.FlexGridSizer(len(rows), 2, 9, 12)
        grid.AddGrowableCol(1, 1)
        for label, key in rows:
            self._row(page, grid, label, key)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 14)
        sizer.AddStretchSpacer()
        page.SetSizer(sizer)
        return page

    def _build_health_page(self, parent):
        return self._grid_page(parent, [
            ("Organisme :", "medecine_nom"),
            ("Identifiant adhérent :", "medecine_identifiant"),
            ("Contact :", "medecine_contact"),
            ("Téléphone :", "medecine_telephone"),
            ("Email :", "medecine_email"),
            ("Portail / site :", "medecine_portail"),
        ])

    def _build_social_page(self, parent):
        return self._grid_page(parent, [
            ("URSSAF / MSA — organisme :", "urssaf_organisme"),
            ("URSSAF / MSA — identifiant :", "urssaf_identifiant"),
            ("Mutuelle — organisme :", "mutuelle_organisme"),
            ("Mutuelle — référence :", "mutuelle_reference"),
            ("Prévoyance — organisme :", "prevoyance_organisme"),
            ("Prévoyance — référence :", "prevoyance_reference"),
            ("OPCO — organisme :", "opco_organisme"),
            ("OPCO — identifiant :", "opco_identifiant"),
            ("Retraite — organisme :", "retraite_organisme"),
            ("Retraite — identifiant :", "retraite_identifiant"),
        ])

    def _build_insurance_page(self, parent):
        return self._grid_page(parent, [
            ("Assureur / contrat employeur :", "assurance_employeur"),
            ("Référence / n° police :", "assurance_reference"),
            ("Contact :", "assurance_contact"),
            ("Téléphone :", "assurance_telephone"),
            ("Email :", "assurance_email"),
        ])

    def _build_notes_page(self, parent):
        page = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        hint = wx.StaticText(
            page,
            label="Notes internes non sensibles : échéances, procédures, rappels, contacts utiles…",
        )
        sizer.Add(hint, 0, wx.ALL, 14)
        sizer.Add(self._text(page, "notes", wx.TE_MULTILINE), 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)
        page.SetSizer(sizer)
        return page

    def OnOk(self, event):
        values = {key: ctrl.GetValue().strip() for key, ctrl in self.controls.items()}
        UTILS_References_admin.SetProfil(values)
        self.EndModal(wx.ID_OK)
