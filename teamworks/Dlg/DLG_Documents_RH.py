#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sélecteur commun des documents RH salarié et contrat."""

import wx

from domain.documents import DocumentScope, list_document_types
from Utils import UTILS_Documents_RH
from Utils.UTILS_Traduction import _


_FIELD_LABELS = {
    "STRUCTURE_RAISON_SOCIALE": u"Nom officiel de la structure",
    "STRUCTURE_ADRESSE": u"Adresse de la structure",
    "SALARIE_NOM": u"Nom du salarié",
    "SALARIE_PRENOM": u"Prénom du salarié",
    "CONTRAT_DATE_DEBUT": u"Date de début du contrat",
}


class Dialog(wx.Dialog):
    def __init__(self, parent, IDpersonne=None, IDcontrat=None):
        self.IDpersonne = IDpersonne
        self.IDcontrat = IDcontrat
        self.scope = DocumentScope.CONTRACT if IDcontrat not in (None, 0, "") else DocumentScope.EMPLOYEE
        self.document_types = list_document_types(scope=self.scope)
        self.prepared = None

        titre = _(u"Documents RH du contrat") if self.scope is DocumentScope.CONTRACT else _(u"Documents RH du salarié")
        super().__init__(
            parent,
            title=titre,
            size=(700, 520),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        titre_ctrl = wx.StaticText(panel, label=titre)
        font = titre_ctrl.GetFont()
        font.SetPointSize(max(12, font.GetPointSize() + 3))
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        titre_ctrl.SetFont(font)
        main.Add(titre_ctrl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 16)

        intro = wx.StaticText(
            panel,
            label=_(u"Choisissez le document à préparer. Teamworks vérifie les données disponibles avant d'ouvrir le publipostage."),
        )
        intro.Wrap(650)
        main.Add(intro, 0, wx.EXPAND | wx.ALL, 16)

        content = wx.BoxSizer(wx.HORIZONTAL)
        self.list_documents = wx.ListBox(
            panel,
            choices=[item.label for item in self.document_types],
            style=wx.LB_SINGLE,
        )
        content.Add(self.list_documents, 1, wx.EXPAND | wx.RIGHT, 12)

        details = wx.StaticBoxSizer(wx.VERTICAL, panel, _(u"Préparation"))
        details_parent = details.GetStaticBox()
        self.label_type = wx.StaticText(details_parent, label="")
        font_type = self.label_type.GetFont()
        font_type.SetWeight(wx.FONTWEIGHT_BOLD)
        self.label_type.SetFont(font_type)
        details.Add(self.label_type, 0, wx.EXPAND | wx.ALL, 8)

        self.label_description = wx.StaticText(details_parent, label="")
        self.label_description.Wrap(330)
        details.Add(self.label_description, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.label_mode = wx.StaticText(details_parent, label="")
        details.Add(self.label_mode, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.label_etat = wx.StaticText(details_parent, label="")
        self.label_etat.Wrap(330)
        details.Add(self.label_etat, 1, wx.EXPAND | wx.ALL, 8)
        content.Add(details, 2, wx.EXPAND)
        main.Add(content, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.AddStretchSpacer(1)
        self.bouton_action = wx.Button(panel, label=_(u"Ouvrir le publiposteur"))
        self.bouton_fermer = wx.Button(panel, wx.ID_CANCEL, label=_(u"Fermer"))
        buttons.Add(self.bouton_action, 0, wx.RIGHT, 8)
        buttons.Add(self.bouton_fermer, 0)
        main.Add(buttons, 0, wx.EXPAND | wx.ALL, 16)

        panel.SetSizer(main)
        self.list_documents.Bind(wx.EVT_LISTBOX, self.OnSelection)
        self.list_documents.Bind(wx.EVT_LISTBOX_DCLICK, self.OnAction)
        self.bouton_action.Bind(wx.EVT_BUTTON, self.OnAction)

        if self.document_types:
            self.list_documents.SetSelection(0)
            self._refresh_details()
        else:
            self.bouton_action.Enable(False)
            self.label_etat.SetLabel(_(u"Aucun type de document n'est disponible dans ce contexte."))

        self.CentreOnParent()

    def _current_document_type(self):
        index = self.list_documents.GetSelection()
        if index == wx.NOT_FOUND:
            return None
        return self.document_types[index]

    def _missing_text(self, missing_fields):
        labels = [
            _FIELD_LABELS.get(item.field, item.field.replace("_", " ").title())
            for item in missing_fields
        ]
        return u"\n".join(u"• %s" % label for label in labels)

    def _refresh_details(self):
        document_type = self._current_document_type()
        if document_type is None:
            self.prepared = None
            self.bouton_action.Enable(False)
            return

        self.label_type.SetLabel(document_type.label)
        description = document_type.description or _(u"Document RH alimenté à partir du dossier salarié et de la structure.")
        self.label_description.SetLabel(description)
        self.label_description.Wrap(330)

        try:
            self.prepared = UTILS_Documents_RH.PrepareDocument(
                document_type.code,
                IDpersonne=self.IDpersonne,
                IDcontrat=self.IDcontrat,
            )
        except (KeyError, ValueError) as exc:
            self.prepared = None
            self.label_mode.SetLabel("")
            self.label_etat.SetLabel(str(exc))
            self.bouton_action.Enable(False)
            return

        if self.prepared.generated_by_teamworks:
            self.label_mode.SetLabel(_(u"Production : modèle Teamworks / publipostage"))
            self.bouton_action.SetLabel(_(u"Ouvrir le publiposteur"))
        else:
            self.label_mode.SetLabel(_(u"Production : service réglementaire externe"))
            self.bouton_action.SetLabel(_(u"Voir la procédure"))

        if self.prepared.ready:
            self.label_etat.SetLabel(_(u"Prêt : les données indispensables sont renseignées."))
        else:
            self.label_etat.SetLabel(
                _(u"Données à compléter avant finalisation :\n")
                + self._missing_text(self.prepared.missing_fields)
            )
        self.label_etat.Wrap(330)
        self.bouton_action.Enable(True)
        self.Layout()

    def _confirm_missing_fields(self):
        if self.prepared is None or self.prepared.ready:
            return True
        message = (
            _(u"Certaines données indispensables ne sont pas renseignées :\n\n")
            + self._missing_text(self.prepared.missing_fields)
            + _(u"\n\nVous pouvez continuer pour utiliser un modèle historique, mais le document devra être vérifié avant utilisation. Continuer ?")
        )
        dlg = wx.MessageDialog(
            self,
            message,
            _(u"Document RH incomplet"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
        )
        result = dlg.ShowModal() == wx.ID_YES
        dlg.Destroy()
        return result

    def OnSelection(self, event):
        self._refresh_details()
        event.Skip()

    def OnAction(self, event):
        document_type = self._current_document_type()
        if document_type is None or self.prepared is None:
            return

        if not self.prepared.generated_by_teamworks:
            message = (
                _(u"Teamworks prépare et contrôle les données nécessaires pour ce document, mais le document officiel doit rester produit et transmis via le service réglementaire externe compétent.\n\n")
            )
            if not self.prepared.ready:
                message += _(u"Données à compléter :\n") + self._missing_text(self.prepared.missing_fields)
            else:
                message += _(u"Les données nécessaires disponibles dans Teamworks sont prêtes.")
            wx.MessageBox(
                message,
                document_type.label,
                wx.OK | wx.ICON_INFORMATION,
                parent=self,
            )
            return

        if not self._confirm_missing_fields():
            return

        try:
            dict_donnees = UTILS_Documents_RH.GetDictDonneesDocument(
                document_type.code,
                IDpersonne=self.IDpersonne,
                IDcontrat=self.IDcontrat,
            )
        except (KeyError, ValueError) as exc:
            wx.MessageBox(str(exc), _(u"Document RH"), wx.OK | wx.ICON_ERROR, parent=self)
            return

        if self.scope is DocumentScope.CONTRACT:
            from Dlg import DLG_Publiposteur_contrat as publiposteur
        else:
            from Dlg import DLG_Publiposteur_rh as publiposteur

        dlg = publiposteur.Dialog(
            self,
            "",
            dictDonnees=dict_donnees,
        )
        dlg.ShowModal()
        dlg.Destroy()
