#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Paramétrage CRH-10B des organismes et connexions RH d'une structure.

L'écran manipule uniquement les demandes applicatives et les objets de domaine
non secrets. Il ne connaît ni GestionDB, ni les repositories, ni l'identité de
structure et n'ouvre aucun navigateur.
"""

import datetime

import wx

import Chemins
from application.bootstrap.hr_connections_structure_factory import (
    StructureHrConnectionsRuntimeFactory,
)
from application.services.hr_connections import StructureConnectionProfileRequest
from domain.hr_connections import OrganizationKind, OrganizationReference, PortalLink
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


_KIND_VALUES = tuple(OrganizationKind)
_KIND_LABELS = {
    OrganizationKind.URSSAF: _(u"URSSAF"),
    OrganizationKind.NET_ENTREPRISES: _(u"Net-entreprises"),
    OrganizationKind.MUTUELLE: _(u"Mutuelle"),
    OrganizationKind.PREVOYANCE: _(u"Prévoyance"),
    OrganizationKind.RETRAITE_COMPLEMENTAIRE: _(u"Retraite complémentaire"),
    OrganizationKind.OPCO: _(u"OPCO"),
    OrganizationKind.SPST: _(u"SPST / santé au travail"),
    OrganizationKind.FRANCE_TRAVAIL: _(u"France Travail"),
    OrganizationKind.OTHER: _(u"Autre organisme"),
}


def _format_date(value):
    return value.strftime("%d/%m/%Y") if value is not None else u""


def _parse_date(value, label):
    text = value.strip()
    if not text:
        return None
    for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(text, pattern).date()
        except ValueError:
            pass
    raise ValueError(
        u"%s doit utiliser le format JJ/MM/AAAA (ou AAAA-MM-JJ)." % label
    )


def _message(parent, text, title=_(u"Organismes & connexions RH"), warning=True):
    style = wx.OK | (wx.ICON_WARNING if warning else wx.ICON_INFORMATION)
    wx.MessageBox(text, title, style, parent)


class ReferenceDialog(wx.Dialog):
    """Saisie d'une référence administrative explicitement non secrète."""

    def __init__(self, parent, current=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Référence administrative"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._value = None
        self.ctrl_type = wx.TextCtrl(
            self, value=current.reference_type if current is not None else u""
        )
        self.ctrl_label = wx.TextCtrl(
            self, value=(current.label or u"") if current is not None else u""
        )
        self.ctrl_value = wx.TextCtrl(
            self, value=current.value if current is not None else u""
        )
        self.info = wx.StaticText(
            self,
            -1,
            _(
                u"Exemples : numéro de contrat, numéro d'adhérent, établissement. "
                u"Les mots de passe, jetons et clés ne sont jamais enregistrés ici."
            ),
        )
        self.info.Wrap(UTILS_Styles.Scale(470, minimum=380))
        self.ok = wx.Button(self, wx.ID_OK, _(u"Valider"))
        self.cancel = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))
        self.ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self._layout()
        self.Fit()
        self.CentreOnParent()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        grid = wx.FlexGridSizer(cols=2, vgap=gap, hgap=gap)
        grid.AddGrowableCol(1, 1)
        for label, control in (
            (_(u"Type de référence"), self.ctrl_type),
            (_(u"Libellé"), self.ctrl_label),
            (_(u"Valeur"), self.ctrl_value),
        ):
            grid.Add(wx.StaticText(self, -1, label), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)
        buttons = wx.StdDialogButtonSizer()
        buttons.AddButton(self.ok)
        buttons.AddButton(self.cancel)
        buttons.Realize()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.info, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(buttons, 0, wx.ALIGN_RIGHT | wx.ALL, page_gap)
        self.SetSizer(sizer)

    def OnOk(self, event):
        try:
            self._value = OrganizationReference.create(
                reference_type=self.ctrl_type.GetValue(),
                value=self.ctrl_value.GetValue(),
                label=self.ctrl_label.GetValue() or None,
            )
        except (TypeError, ValueError) as exc:
            _message(self, str(exc))
            return
        self.EndModal(wx.ID_OK)

    def GetValue(self):
        if self._value is None:
            raise RuntimeError("La référence administrative n'a pas été validée.")
        return self._value


class PortalDialog(wx.Dialog):
    """Saisie d'un lien de portail HTTP/HTTPS sans identifiant intégré."""

    def __init__(self, parent, current=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Portail de l'organisme"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._value = None
        self.ctrl_label = wx.TextCtrl(
            self, value=current.label if current is not None else u""
        )
        self.ctrl_url = wx.TextCtrl(
            self, value=current.url if current is not None else u"https://"
        )
        self.info = wx.StaticText(
            self,
            -1,
            _(
                u"Le lien sert uniquement de référence. L'ouverture du navigateur "
                u"reste une action utilisateur distincte et explicite."
            ),
        )
        self.info.Wrap(UTILS_Styles.Scale(470, minimum=380))
        self.ok = wx.Button(self, wx.ID_OK, _(u"Valider"))
        self.cancel = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))
        self.ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self._layout()
        self.Fit()
        self.CentreOnParent()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        grid = wx.FlexGridSizer(cols=2, vgap=gap, hgap=gap)
        grid.AddGrowableCol(1, 1)
        for label, control in (
            (_(u"Libellé"), self.ctrl_label),
            (_(u"URL"), self.ctrl_url),
        ):
            grid.Add(wx.StaticText(self, -1, label), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)
        buttons = wx.StdDialogButtonSizer()
        buttons.AddButton(self.ok)
        buttons.AddButton(self.cancel)
        buttons.Realize()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.info, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(buttons, 0, wx.ALIGN_RIGHT | wx.ALL, page_gap)
        self.SetSizer(sizer)

    def OnOk(self, event):
        try:
            self._value = PortalLink.create(
                url=self.ctrl_url.GetValue(), label=self.ctrl_label.GetValue()
            )
        except (TypeError, ValueError) as exc:
            _message(self, str(exc))
            return
        self.EndModal(wx.ID_OK)

    def GetValue(self):
        if self._value is None:
            raise RuntimeError("Le portail n'a pas été validé.")
        return self._value


class ProfileDialog(wx.Dialog):
    """Création ou modification contrôlée d'un profil d'organisme."""

    def __init__(self, parent, current=None):
        title = (
            _(u"Modifier un organisme RH")
            if current is not None
            else _(u"Ajouter un organisme RH")
        )
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._current = current
        self._request = None
        profile = current.profile if current is not None else None
        period = profile.effective_period if profile is not None else None
        self._references = list(profile.references if profile is not None else ())
        self._portals = list(profile.portal_links if profile is not None else ())

        self.ctrl_code = wx.TextCtrl(
            self, value=profile.organization.code if profile is not None else u""
        )
        self.ctrl_label = wx.TextCtrl(
            self, value=profile.organization.label if profile is not None else u""
        )
        self.choice_kind = wx.Choice(
            self, choices=[_KIND_LABELS[value] for value in _KIND_VALUES]
        )
        kind = profile.organization.kind if profile is not None else OrganizationKind.OTHER
        self.choice_kind.SetSelection(_KIND_VALUES.index(kind))
        self.ctrl_start = wx.TextCtrl(
            self, value=_format_date(period.starts_on if period is not None else None)
        )
        self.ctrl_end = wx.TextCtrl(
            self, value=_format_date(period.ends_on if period is not None else None)
        )

        if profile is not None:
            self.ctrl_code.Enable(False)
            self.choice_kind.Enable(False)

        # Les contrôles contenus dans un StaticBoxSizer doivent appartenir au
        # StaticBox lui-même et non au dialogue. Ce parentage est requis par
        # wxWidgets/Phoenix et vérifié par le ratissage RC.
        self.references_static_box = wx.StaticBox(
            self, -1, _(u"Références administratives")
        )
        self.portals_static_box = wx.StaticBox(self, -1, _(u"Portails"))

        self.list_references = wx.ListCtrl(
            self.references_static_box,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
        )
        for index, (label, width) in enumerate(
            (
                (_(u"Type"), 145),
                (_(u"Libellé"), 180),
                (_(u"Valeur"), 230),
            )
        ):
            self.list_references.InsertColumn(
                index, label, width=UTILS_Styles.Scale(width, minimum=75)
            )

        self.list_portals = wx.ListCtrl(
            self.portals_static_box,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
        )
        for index, (label, width) in enumerate(
            (
                (_(u"Libellé"), 190),
                (_(u"URL"), 365),
            )
        ):
            self.list_portals.InsertColumn(
                index, label, width=UTILS_Styles.Scale(width, minimum=90)
            )

        self.ref_add = wx.Button(self.references_static_box, -1, _(u"Ajouter"))
        self.ref_edit = wx.Button(self.references_static_box, -1, _(u"Modifier"))
        self.ref_remove = wx.Button(self.references_static_box, -1, _(u"Retirer"))
        self.portal_add = wx.Button(self.portals_static_box, -1, _(u"Ajouter"))
        self.portal_edit = wx.Button(self.portals_static_box, -1, _(u"Modifier"))
        self.portal_remove = wx.Button(self.portals_static_box, -1, _(u"Retirer"))
        self.ok = wx.Button(self, wx.ID_OK, _(u"Enregistrer"))
        self.cancel = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))

        self.ref_add.Bind(wx.EVT_BUTTON, self.OnAddReference)
        self.ref_edit.Bind(wx.EVT_BUTTON, self.OnEditReference)
        self.ref_remove.Bind(wx.EVT_BUTTON, self.OnRemoveReference)
        self.portal_add.Bind(wx.EVT_BUTTON, self.OnAddPortal)
        self.portal_edit.Bind(wx.EVT_BUTTON, self.OnEditPortal)
        self.portal_remove.Bind(wx.EVT_BUTTON, self.OnRemovePortal)
        self.list_references.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnEditReference)
        self.list_portals.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnEditPortal)
        self.ok.Bind(wx.EVT_BUTTON, self.OnOk)

        self._refresh_references()
        self._refresh_portals()
        self._layout()
        self.SetMinSize(
            (
                UTILS_Styles.Scale(700, minimum=600),
                UTILS_Styles.Scale(650, minimum=520),
            )
        )
        self.CentreOnParent()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        grid = wx.FlexGridSizer(cols=2, vgap=gap, hgap=gap)
        grid.AddGrowableCol(1, 1)
        for label, control in (
            (_(u"Code stable"), self.ctrl_code),
            (_(u"Nom de l'organisme"), self.ctrl_label),
            (_(u"Famille"), self.choice_kind),
            (_(u"Date d'effet"), self.ctrl_start),
            (_(u"Date de fin"), self.ctrl_end),
        ):
            grid.Add(wx.StaticText(self, -1, label), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)

        info = wx.StaticText(
            self,
            -1,
            _(
                u"Le code et la famille deviennent stables après création. Les capacités "
                u"(API, dépôt, synchronisation…) restent déterminées par les connecteurs "
                u"réellement implémentés et ne sont pas activables manuellement ici."
            ),
        )
        info.Wrap(UTILS_Styles.Scale(650, minimum=540))

        references_box = wx.StaticBoxSizer(self.references_static_box, wx.VERTICAL)
        references_box.Add(self.list_references, 1, wx.EXPAND | wx.ALL, gap)
        ref_buttons = wx.BoxSizer(wx.HORIZONTAL)
        ref_buttons.Add(self.ref_add, 0, wx.RIGHT, gap)
        ref_buttons.Add(self.ref_edit, 0, wx.RIGHT, gap)
        ref_buttons.Add(self.ref_remove, 0)
        references_box.Add(ref_buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, gap)

        portals_box = wx.StaticBoxSizer(self.portals_static_box, wx.VERTICAL)
        portals_box.Add(self.list_portals, 1, wx.EXPAND | wx.ALL, gap)
        portal_buttons = wx.BoxSizer(wx.HORIZONTAL)
        portal_buttons.Add(self.portal_add, 0, wx.RIGHT, gap)
        portal_buttons.Add(self.portal_edit, 0, wx.RIGHT, gap)
        portal_buttons.Add(self.portal_remove, 0)
        portals_box.Add(portal_buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, gap)

        buttons = wx.StdDialogButtonSizer()
        buttons.AddButton(self.ok)
        buttons.AddButton(self.cancel)
        buttons.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(info, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(references_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(portals_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(buttons, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        self.SetSizer(sizer)

    def _refresh_references(self):
        self.list_references.DeleteAllItems()
        for item in self._references:
            index = self.list_references.InsertItem(
                self.list_references.GetItemCount(), item.reference_type
            )
            self.list_references.SetItem(index, 1, item.label or u"")
            self.list_references.SetItem(index, 2, item.value)

    def _refresh_portals(self):
        self.list_portals.DeleteAllItems()
        for item in self._portals:
            index = self.list_portals.InsertItem(
                self.list_portals.GetItemCount(), item.label
            )
            self.list_portals.SetItem(index, 1, item.url)

    @staticmethod
    def _selected_index(control, message):
        index = control.GetFirstSelected()
        if index < 0:
            raise ValueError(message)
        return index

    def OnAddReference(self, event):
        dlg = ReferenceDialog(self)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self._references.append(dlg.GetValue())
                self._refresh_references()
        finally:
            dlg.Destroy()

    def OnEditReference(self, event):
        try:
            index = self._selected_index(
                self.list_references, _(u"Sélectionnez une référence à modifier.")
            )
        except ValueError as exc:
            _message(self, str(exc))
            return
        dlg = ReferenceDialog(self, current=self._references[index])
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self._references[index] = dlg.GetValue()
                self._refresh_references()
                self.list_references.Select(index)
        finally:
            dlg.Destroy()

    def OnRemoveReference(self, event):
        try:
            index = self._selected_index(
                self.list_references, _(u"Sélectionnez une référence à retirer.")
            )
        except ValueError as exc:
            _message(self, str(exc))
            return
        del self._references[index]
        self._refresh_references()

    def OnAddPortal(self, event):
        dlg = PortalDialog(self)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self._portals.append(dlg.GetValue())
                self._refresh_portals()
        finally:
            dlg.Destroy()

    def OnEditPortal(self, event):
        try:
            index = self._selected_index(
                self.list_portals, _(u"Sélectionnez un portail à modifier.")
            )
        except ValueError as exc:
            _message(self, str(exc))
            return
        dlg = PortalDialog(self, current=self._portals[index])
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self._portals[index] = dlg.GetValue()
                self._refresh_portals()
                self.list_portals.Select(index)
        finally:
            dlg.Destroy()

    def OnRemovePortal(self, event):
        try:
            index = self._selected_index(
                self.list_portals, _(u"Sélectionnez un portail à retirer.")
            )
        except ValueError as exc:
            _message(self, str(exc))
            return
        del self._portals[index]
        self._refresh_portals()

    def OnOk(self, event):
        kind_index = self.choice_kind.GetSelection()
        if kind_index < 0:
            _message(self, _(u"Sélectionnez une famille d'organisme."))
            return
        try:
            self._request = StructureConnectionProfileRequest.create(
                organization_code=self.ctrl_code.GetValue(),
                organization_label=self.ctrl_label.GetValue(),
                organization_kind=_KIND_VALUES[kind_index],
                references=self._references,
                portal_links=self._portals,
                starts_on=_parse_date(self.ctrl_start.GetValue(), _(u"La date d'effet")),
                ends_on=_parse_date(self.ctrl_end.GetValue(), _(u"La date de fin")),
            )
        except (TypeError, ValueError) as exc:
            _message(self, str(exc))
            return
        self.EndModal(wx.ID_OK)

    def GetRequest(self):
        if self._request is None:
            raise RuntimeError("La configuration de l'organisme n'a pas été validée.")
        return self._request


class Dialog(wx.Dialog):
    """Gestion des profils d'organismes de la base Teamworks active."""

    def __init__(self, parent, runtime_factory=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Organismes & connexions RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        factory = runtime_factory or StructureHrConnectionsRuntimeFactory
        self._runtime = factory().create()
        self._row_codes = []
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.info = wx.StaticText(
            self,
            -1,
            _(
                u"Configurez ici les organismes, références administratives et portails "
                u"de la structure. Aucun mot de passe n'est stocké dans ces données."
            ),
        )
        self.info.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        self.list = wx.ListCtrl(
            self,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
        )
        self.list.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.list.SetTextColour(UTILS_Interface.GetToken("on_surface"))
        for index, (label, width) in enumerate(
            (
                (_(u"Organisme"), 220),
                (_(u"Famille"), 160),
                (_(u"Références"), 90),
                (_(u"Portails"), 80),
                (_(u"Connecteur"), 220),
                (_(u"État"), 125),
            )
        ):
            self.list.InsertColumn(
                index, label, width=UTILS_Styles.Scale(width, minimum=70)
            )

        self.add = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Ajouter"),
            cheminImage=Chemins.GetStaticPath("Images/16x16/Ajouter.png"),
            tailleImage=(16, 16),
        )
        self.edit = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Modifier"),
            cheminImage=Chemins.GetStaticPath("Images/16x16/Modifier.png"),
            tailleImage=(16, 16),
        )
        self.close = wx.Button(self, wx.ID_CLOSE, _(u"Fermer"))
        self.edit.Enable(False)

        self.add.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.edit.Bind(wx.EVT_BUTTON, self.OnEdit)
        self.close.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE))
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnEdit)

        self._layout()
        self.RefreshData()
        self.SetMinSize(
            (
                UTILS_Styles.Scale(980, minimum=780),
                UTILS_Styles.Scale(520, minimum=420),
            )
        )
        self.CentreOnParent()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(self.add, 0, wx.RIGHT, gap)
        buttons.Add(self.edit, 0, wx.RIGHT, gap)
        buttons.AddStretchSpacer(1)
        buttons.Add(self.close, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.info, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)

    def RefreshData(self):
        configurations = self._runtime.list_configurations()
        self.list.Freeze()
        try:
            self.list.DeleteAllItems()
            self._row_codes = []
            for configuration in configurations:
                profile = configuration.profile
                connectors = configuration.connectors
                connector_text = u", ".join(item.connector_id for item in connectors)
                if not connector_text:
                    connector_text = _(u"Aucun connecteur de référence")
                state = (
                    _(u"Configuré")
                    if configuration.has_configured_connector
                    else _(u"À configurer")
                )
                values = (
                    profile.organization.label,
                    _KIND_LABELS.get(profile.organization.kind, profile.organization.kind.value),
                    str(len(profile.references)),
                    str(len(profile.portal_links)),
                    connector_text,
                    state,
                )
                row = self.list.InsertItem(self.list.GetItemCount(), values[0])
                for column, value in enumerate(values[1:], 1):
                    self.list.SetItem(row, column, value)
                if not configuration.has_configured_connector:
                    self.list.SetItemTextColour(row, UTILS_Interface.GetToken("warning"))
                self._row_codes.append(profile.organization.code)
        finally:
            self.list.Thaw()
        self.edit.Enable(False)

    def OnSelection(self, event):
        self.edit.Enable(self.list.GetFirstSelected() >= 0)
        event.Skip()

    def _selected_configuration(self):
        index = self.list.GetFirstSelected()
        if index < 0 or index >= len(self._row_codes):
            raise ValueError(_(u"Sélectionnez un organisme à modifier."))
        configuration = self._runtime.get_configuration(self._row_codes[index])
        if configuration is None:
            raise LookupError(_(u"L'organisme sélectionné n'existe plus."))
        return configuration

    def _save_from_dialog(self, dlg):
        if dlg.ShowModal() != wx.ID_OK:
            return False
        self._runtime.save_profile(dlg.GetRequest())
        self.RefreshData()
        return True

    def OnAdd(self, event):
        dlg = ProfileDialog(self)
        try:
            try:
                self._save_from_dialog(dlg)
            except (TypeError, ValueError, LookupError, RuntimeError) as exc:
                _message(self, str(exc))
        finally:
            dlg.Destroy()

    def OnEdit(self, event):
        try:
            current = self._selected_configuration()
        except (ValueError, LookupError) as exc:
            _message(self, str(exc))
            return
        dlg = ProfileDialog(self, current=current)
        try:
            try:
                self._save_from_dialog(dlg)
            except (TypeError, ValueError, LookupError, RuntimeError) as exc:
                _message(self, str(exc))
        finally:
            dlg.Destroy()
