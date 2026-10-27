#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Champs historiques facultatifs d'un contrat, hors du parcours principal.

Le moteur métier et le stockage restent inchangés : l'utilisateur choisit
seulement les champs supplémentaires d'un modèle historique.
"""
import wx

import Chemins
from Ctrl import CTRL_Bouton_image
from Utils.UTILS_Traduction import _


class Dialog(wx.Dialog):
    def __init__(self, parent, definitions, initial_values):
        super().__init__(
            parent, -1, _(u"Champs spécifiques du contrat"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.champs = None
        self._fields = {}
        values = dict(initial_values or {})
        definitions = dict(definitions or {})

        root = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(
            self, -1,
            _(u"Compléments nécessaires à un ancien modèle de contrat"),
        )
        description = wx.StaticText(
            self, -1,
            _(u"Ces champs sont facultatifs. La durée, les dates et les "
              u"rémunérations sont déjà gérées dans le formulaire principal."),
        )
        root.Add(title, 0, wx.ALL, 12)
        description.Wrap(620)
        root.Add(description, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        scroll = wx.ScrolledWindow(
            self, -1, style=wx.VSCROLL | wx.TAB_TRAVERSAL,
        )
        fields_sizer = wx.BoxSizer(wx.VERTICAL)
        for field_id, definition in sorted(
            definitions.items(),
            key=lambda entry: str(entry[1][1]).casefold(),
        ):
            label = str(definition[1] or "")
            help_text = str(definition[2] or "")
            default = definition[4] if len(definition) > 4 else ""
            checked = field_id in values
            value = values.get(field_id, default)
            check = wx.CheckBox(scroll, -1, label)
            check.SetValue(checked)
            if help_text:
                check.SetToolTip(help_text)
            edit = wx.TextCtrl(
                scroll, -1, "" if value is None else str(value),
            )
            edit.Enable(checked)
            check.Bind(
                wx.EVT_CHECKBOX,
                lambda event, field=edit: field.Enable(event.IsChecked()),
            )
            fields_sizer.Add(check, 0, wx.TOP | wx.BOTTOM, 6)
            fields_sizer.Add(edit, 0, wx.EXPAND | wx.BOTTOM, 8)
            self._fields[field_id] = (check, edit, label)
        scroll.SetSizer(fields_sizer)
        scroll.SetScrollRate(0, 12)
        root.Add(scroll, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.AddStretchSpacer(1)
        self.bouton_valider = CTRL_Bouton_image.CTRL(
            self, id=wx.ID_OK, texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
            role="primary",
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self, id=wx.ID_CANCEL, texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )
        actions.Add(self.bouton_valider, 0, wx.RIGHT, 10)
        actions.Add(self.bouton_annuler)
        root.Add(actions, 0, wx.EXPAND | wx.ALL, 12)
        self.SetSizer(root)
        self.SetMinSize((540, 350))
        self.SetSize((680, 520))
        self.CentreOnParent()
        self.bouton_valider.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.OnValider, self.bouton_valider)
        self.Bind(wx.EVT_BUTTON, self.OnAnnuler, self.bouton_annuler)

    def OnValider(self, event):
        selected = {}
        empty = []
        for field_id, (check, edit, label) in self._fields.items():
            if not check.GetValue():
                continue
            value = edit.GetValue()
            if value.strip():
                selected[field_id] = value
            else:
                empty.append(label)
        if empty:
            message = _(
                u"Les champs suivants sont sélectionnés mais vides :\n\n%s\n\n"
                u"Continuer sans les enregistrer ?"
            ) % "\n".join(empty)
            question = wx.MessageDialog(
                self, message, _(u"Champs spécifiques"),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
            )
            try:
                if question.ShowModal() != wx.ID_YES:
                    return
            finally:
                question.Destroy()
        self.champs = selected
        self.EndModal(wx.ID_OK)

    def OnAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)
