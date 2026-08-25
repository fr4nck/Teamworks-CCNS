#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fiche Structure / Association de Teamworks CCNS."""

import os
import re

import wx

from Utils import UTILS_Branding
from Utils import UTILS_Organisation
from Utils import UTILS_Styles


FIELD_ROLES = {
    "code_postal": UTILS_Styles.FIELD_POSTAL_CODE,
    "telephone": UTILS_Styles.FIELD_PHONE,
    "rna": UTILS_Styles.FIELD_CODE,
    "siren": UTILS_Styles.FIELD_CODE,
    "siret": UTILS_Styles.FIELD_SIRET,
    "ape_naf": UTILS_Styles.FIELD_CODE,
    "agrement_js_date": UTILS_Styles.FIELD_DATE,
    "assurance_echeance": UTILS_Styles.FIELD_DATE,
    "police_assurance": UTILS_Styles.FIELD_CODE,
}


class Dialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Structure / Association",
            size=(860, 700),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.profile = UTILS_Organisation.GetProfil()
        self.initial_logo_path = UTILS_Branding.GetAssociationLogoPath()
        self.remove_logo = False
        self.controls = {}
        self.flags = {}

        panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        header = wx.BoxSizer(wx.HORIZONTAL)
        texts = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(panel, label="Structure / Association")
        font = title.GetFont()
        font.SetPointSize(max(12, font.GetPointSize() + 3))
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        texts.Add(title, 0)
        subtitle = wx.StaticText(
            panel,
            label="Identité administrative, coordonnées, agréments, assurance et mentions documentaires.",
        )
        texts.Add(subtitle, 0, wx.TOP, 4)
        header.Add(texts, 1, wx.ALIGN_CENTER_VERTICAL)
        main.Add(header, 0, wx.EXPAND | wx.ALL, 14)

        notebook = wx.Notebook(panel)
        notebook.AddPage(self._build_identity_page(notebook), "Identité")
        notebook.AddPage(self._build_legal_page(notebook), "Références & assurance")
        notebook.AddPage(self._build_documents_page(notebook), "Documents")
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

    def _text(self, parent, key):
        ctrl = wx.TextCtrl(parent, value=self.profile.get(key, ""))
        role = FIELD_ROLES.get(key, UTILS_Styles.FIELD_TEXT)
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

    def _build_identity_page(self, parent):
        page = wx.Panel(parent)
        main = wx.BoxSizer(wx.VERTICAL)

        identity_box = wx.StaticBoxSizer(wx.VERTICAL, page, "Identité")
        identity_parent = identity_box.GetStaticBox()
        grid = wx.FlexGridSizer(4, 2, 8, 12)
        grid.AddGrowableCol(1, 1)
        self._row(identity_parent, grid, "Nom officiel :", "nom_officiel")
        self._row(identity_parent, grid, "Nom d’usage :", "nom_usage")
        self._row(identity_parent, grid, "Représentant légal :", "representant_legal")
        self._row(identity_parent, grid, "Fonction :", "representant_fonction")
        identity_box.Add(grid, 0, wx.EXPAND | wx.ALL, 10)
        main.Add(identity_box, 0, wx.EXPAND | wx.ALL, 10)

        contact_box = wx.StaticBoxSizer(wx.VERTICAL, page, "Coordonnées")
        contact_parent = contact_box.GetStaticBox()
        contact_grid = wx.FlexGridSizer(7, 2, 8, 12)
        contact_grid.AddGrowableCol(1, 1)
        self._row(contact_parent, contact_grid, "Adresse :", "adresse")
        self._row(contact_parent, contact_grid, "Code postal :", "code_postal")
        self._row(contact_parent, contact_grid, "Ville :", "ville")
        self._row(contact_parent, contact_grid, "Téléphone :", "telephone")
        self._row(contact_parent, contact_grid, "Email :", "email")
        self._row(contact_parent, contact_grid, "Site web :", "site_web")
        contact_box.Add(contact_grid, 0, wx.EXPAND | wx.ALL, 10)
        main.Add(contact_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        logo_box = wx.StaticBoxSizer(wx.VERTICAL, page, "Logo")
        logo_parent = logo_box.GetStaticBox()
        logo_row = wx.BoxSizer(wx.HORIZONTAL)
        self.logo_picker = wx.FilePickerCtrl(
            logo_parent,
            path=self.initial_logo_path,
            message="Sélectionner le logo de la structure",
            wildcard="Images (*.png;*.jpg;*.jpeg;*.bmp)|*.png;*.jpg;*.jpeg;*.bmp",
            style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL,
        )
        logo_row.Add(self.logo_picker, 1, wx.EXPAND | wx.RIGHT, 8)
        remove = wx.Button(logo_parent, label="Retirer")
        logo_row.Add(remove, 0)
        logo_box.Add(logo_row, 0, wx.EXPAND | wx.ALL, 10)
        hint = wx.StaticText(
            logo_parent,
            label="PNG transparent recommandé. Ce logo sera réutilisé dans le splash et les documents.",
        )
        logo_box.Add(hint, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        main.Add(logo_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        remove.Bind(wx.EVT_BUTTON, self.OnRemoveLogo)
        self.logo_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnLogoChanged)

        page.SetSizer(main)
        return page

    def _build_legal_page(self, parent):
        page = wx.Panel(parent)
        main = wx.BoxSizer(wx.VERTICAL)

        legal_box = wx.StaticBoxSizer(wx.VERTICAL, page, "Identifiants légaux")
        legal_parent = legal_box.GetStaticBox()
        legal_grid = wx.FlexGridSizer(7, 2, 8, 12)
        legal_grid.AddGrowableCol(1, 1)
        self._row(legal_parent, legal_grid, "RNA / n° association :", "rna")
        self._row(legal_parent, legal_grid, "SIREN :", "siren")
        self._row(legal_parent, legal_grid, "SIRET :", "siret")
        self._row(legal_parent, legal_grid, "Code APE / NAF :", "ape_naf")
        self._row(legal_parent, legal_grid, "Préfecture / déclaration :", "declaration_prefecture")
        self._row(legal_parent, legal_grid, "Référence JOAFE :", "reference_joafe")
        legal_box.Add(legal_grid, 0, wx.EXPAND | wx.ALL, 10)
        main.Add(legal_box, 0, wx.EXPAND | wx.ALL, 10)

        approval_box = wx.StaticBoxSizer(wx.VERTICAL, page, "Agrément")
        approval_parent = approval_box.GetStaticBox()
        approval_grid = wx.FlexGridSizer(2, 2, 8, 12)
        approval_grid.AddGrowableCol(1, 1)
        self._row(approval_parent, approval_grid, "Agrément Jeunesse et Sports / JEP :", "agrement_js")
        self._row(approval_parent, approval_grid, "Date / validité :", "agrement_js_date")
        approval_box.Add(approval_grid, 0, wx.EXPAND | wx.ALL, 10)
        main.Add(approval_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        insurance_box = wx.StaticBoxSizer(wx.VERTICAL, page, "Assurance")
        insurance_parent = insurance_box.GetStaticBox()
        insurance_grid = wx.FlexGridSizer(3, 2, 8, 12)
        insurance_grid.AddGrowableCol(1, 1)
        self._row(insurance_parent, insurance_grid, "Assureur :", "assureur")
        self._row(insurance_parent, insurance_grid, "N° de police :", "police_assurance")
        self._row(insurance_parent, insurance_grid, "Échéance / validité :", "assurance_echeance")
        insurance_box.Add(insurance_grid, 0, wx.EXPAND | wx.ALL, 10)
        main.Add(insurance_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        page.SetSizer(main)
        return page

    def _build_documents_page(self, parent):
        page = wx.Panel(parent)
        main = wx.BoxSizer(wx.VERTICAL)

        explanation = wx.StaticText(
            page,
            label=(
                "Choisissez les mentions que Teamworks CCNS pourra afficher dans les en-têtes des PDF, "
                "impressions et documents imprimables."
            ),
        )
        explanation.Wrap(760)
        main.Add(explanation, 0, wx.ALL, 12)

        labels = [
            ("afficher_logo", "Afficher le logo"),
            ("afficher_coordonnees", "Afficher les coordonnées"),
            ("afficher_rna", "Afficher le RNA"),
            ("afficher_siret", "Afficher le SIRET"),
            ("afficher_agrement", "Afficher l’agrément"),
            ("afficher_assurance", "Afficher l’assurance / n° de police"),
        ]
        box = wx.StaticBoxSizer(wx.VERTICAL, page, "En-tête documentaire")
        box_parent = box.GetStaticBox()
        for key, label in labels:
            ctrl = wx.CheckBox(box_parent, label=label)
            ctrl.SetValue(bool(self.profile.get(key, False)))
            self.flags[key] = ctrl
            box.Add(ctrl, 0, wx.ALL, 6)
        main.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        preview_box = wx.StaticBoxSizer(wx.VERTICAL, page, "Aperçu textuel")
        preview_parent = preview_box.GetStaticBox()
        self.preview = wx.TextCtrl(
            preview_parent,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 150),
        )
        preview_box.Add(self.preview, 1, wx.EXPAND | wx.ALL, 8)
        main.Add(preview_box, 1, wx.EXPAND | wx.ALL, 12)
        refresh = wx.Button(page, label="Actualiser l’aperçu")
        main.Add(refresh, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 12)
        refresh.Bind(wx.EVT_BUTTON, self.OnPreview)
        self._refresh_preview()

        page.SetSizer(main)
        return page

    def _values(self):
        values = {key: ctrl.GetValue().strip() for key, ctrl in self.controls.items()}
        values.update({key: ctrl.GetValue() for key, ctrl in self.flags.items()})
        return values

    def _validate(self, values):
        errors = []
        rna = values.get("rna", "").replace(" ", "").upper()
        if rna and not re.fullmatch(r"W\d{9}", rna):
            errors.append("Le RNA doit être au format W suivi de 9 chiffres.")
        siren = re.sub(r"\s", "", values.get("siren", ""))
        if siren and not (siren.isdigit() and len(siren) == 9):
            errors.append("Le SIREN doit contenir 9 chiffres.")
        siret = re.sub(r"\s", "", values.get("siret", ""))
        if siret and not (siret.isdigit() and len(siret) == 14):
            errors.append("Le SIRET doit contenir 14 chiffres.")
        email = values.get("email", "")
        if email and "@" not in email:
            errors.append("L’adresse email semble invalide.")
        return errors

    def _refresh_preview(self):
        lines = UTILS_Organisation.BuildLignesEnteteDocument(self._values())
        self.preview.SetValue("\n".join(lines) or "Aucune mention configurée.")

    def OnPreview(self, event):
        self._refresh_preview()

    def OnRemoveLogo(self, event):
        self.remove_logo = True
        self.logo_picker.SetPath("")

    def OnLogoChanged(self, event):
        self.remove_logo = False
        event.Skip()

    def OnOk(self, event):
        values = self._values()
        errors = self._validate(values)
        if errors:
            wx.MessageBox("\n".join(errors), "Informations à vérifier", wx.OK | wx.ICON_WARNING, parent=self)
            return

        values["rna"] = values.get("rna", "").replace(" ", "").upper()
        values["siren"] = re.sub(r"\s", "", values.get("siren", ""))
        values["siret"] = re.sub(r"\s", "", values.get("siret", ""))

        try:
            selected_logo = self.logo_picker.GetPath().strip()
            if self.remove_logo:
                UTILS_Branding.ClearAssociationLogo()
            elif selected_logo and os.path.abspath(selected_logo) != os.path.abspath(self.initial_logo_path or ""):
                UTILS_Branding.SetAssociationLogo(selected_logo)
            UTILS_Organisation.SetProfil(values)
        except (OSError, ValueError) as exc:
            wx.MessageBox(str(exc), "Structure non enregistrée", wx.OK | wx.ICON_ERROR, parent=self)
            return

        self.EndModal(wx.ID_OK)
