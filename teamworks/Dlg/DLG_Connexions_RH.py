#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Configuration non secrète des organismes et portails RH de la structure."""

import datetime

import wx

from application.bootstrap.structure_hr_connections_factory import (
    StructureHrConnectionsRuntimeFactory,
    StructureOrganizationProfileRequest,
)
from domain.hr_connections import OrganizationKind, OrganizationReference, PortalLink
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


_KIND_LABELS = {
    OrganizationKind.URSSAF: _(u"URSSAF"),
    OrganizationKind.NET_ENTREPRISES: _(u"Net-entreprises"),
    OrganizationKind.MUTUELLE: _(u"Mutuelle"),
    OrganizationKind.PREVOYANCE: _(u"Prévoyance"),
    OrganizationKind.RETRAITE_COMPLEMENTAIRE: _(u"Retraite complémentaire"),
    OrganizationKind.OPCO: _(u"OPCO"),
    OrganizationKind.SPST: _(u"Santé au travail / SPST"),
    OrganizationKind.FRANCE_TRAVAIL: _(u"France Travail"),
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


def _parse_references(text):
    result = []
    for number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) not in (2, 3):
            raise ValueError(
                u"Référence ligne %d : utilisez type | valeur | libellé optionnel." % number
            )
        result.append(
            OrganizationReference.create(
                reference_type=parts[0],
                value=parts[1],
                label=parts[2] if len(parts) == 3 else None,
            )
        )
    return tuple(result)


def _format_references(references):
    lines = []
    for reference in references:
        parts = [reference.reference_type, reference.value]
        if reference.label:
            parts.append(reference.label)
        lines.append(u" | ".join(parts))
    return u"\n".join(lines)


def _parse_portals(text):
    result = []
    for number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|", 1)]
        if len(parts) != 2:
            raise ValueError(
                u"Portail ligne %d : utilisez libellé | https://adresse-du-portail." % number
            )
        result.append(PortalLink.create(label=parts[0], url=parts[1]))
    return tuple(result)


def _format_portals(portals):
    return u"\n".join(u"%s | %s" % (item.label, item.url) for item in portals)


class ProfileDialog(wx.Dialog):
    """Saisie d'un profil d'organisme sans identifiant d'authentification."""

    def __init__(self, parent, *, supported_kinds, configuration=None):
        title = _(u"Modifier un organisme RH") if configuration else _(u"Ajouter un organisme RH")
        wx.Dialog.__init__(
            self,
            -1,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._supported_kinds = tuple(supported_kinds)
        self._configuration = configuration
        self._request = None

        self.choice_kind = wx.Choice(
            self,
            choices=[_KIND_LABELS.get(kind, kind.value) for kind in self._supported_kinds],
        )
        self.ctrl_code = wx.TextCtrl(self)
        self.ctrl_label = wx.TextCtrl(self)
        self.ctrl_start = wx.TextCtrl(self)
        self.ctrl_end = wx.TextCtrl(self)
        self.ctrl_references = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.ctrl_portals = wx.TextCtrl(self, style=wx.TE_MULTILINE)

        for ctrl in (self.ctrl_code, self.ctrl_label):
            UTILS_Styles.ApplyFieldRole(ctrl, UTILS_Styles.FIELD_TEXT)
        for ctrl in (self.ctrl_start, self.ctrl_end):
            UTILS_Styles.ApplyFieldRole(ctrl, UTILS_Styles.FIELD_DATE)

        self.bouton_ok = wx.Button(self, wx.ID_OK, _(u"Enregistrer"))
        self.bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))
        self.bouton_ok.Bind(wx.EVT_BUTTON, self.OnOk)

        self._prefill()
        self._layout()
        self.SetMinSize(
            (
                UTILS_Styles.Scale(680, minimum=560),
                UTILS_Styles.Scale(620, minimum=500),
            )
        )
        self.CentreOnParent()

    def _prefill(self):
        if self._configuration is None:
            if self._supported_kinds:
                self.choice_kind.SetSelection(0)
            self.ctrl_start.SetValue(_format_date(datetime.date.today()))
            return

        profile = self._configuration.profile
        try:
            index = self._supported_kinds.index(profile.organization.kind)
        except ValueError:
            index = 0
        self.choice_kind.SetSelection(index)
        self.choice_kind.Enable(False)
        self.ctrl_code.SetValue(profile.organization.code)
        self.ctrl_code.Enable(False)
        self.ctrl_label.SetValue(profile.organization.label)
        period = profile.effective_period
        self.ctrl_start.SetValue(_format_date(period.starts_on if period else None))
        self.ctrl_end.SetValue(_format_date(period.ends_on if period else None))
        self.ctrl_references.SetValue(_format_references(profile.references))
        self.ctrl_portals.SetValue(_format_portals(profile.portal_links))

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")

        grid = wx.FlexGridSizer(cols=2, vgap=gap, hgap=gap)
        grid.AddGrowableCol(1, 1)
        for label, control in (
            (_(u"Famille"), self.choice_kind),
            (_(u"Code interne stable"), self.ctrl_code),
            (_(u"Nom de l'organisme"), self.ctrl_label),
            (_(u"Date d'effet"), self.ctrl_start),
            (_(u"Date de fin"), self.ctrl_end),
        ):
            grid.Add(wx.StaticText(self, -1, label), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)

        refs_box = wx.StaticBoxSizer(wx.VERTICAL, self, _(u"Références administratives"))
        refs_box.Add(
            wx.StaticText(
                refs_box.GetStaticBox(),
                -1,
                _(u"Une ligne par référence : type | valeur | libellé optionnel"),
            ),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            gap,
        )
        refs_box.Add(self.ctrl_references, 1, wx.EXPAND | wx.ALL, gap)

        portals_box = wx.StaticBoxSizer(wx.VERTICAL, self, _(u"Portails"))
        portals_box.Add(
            wx.StaticText(
                portals_box.GetStaticBox(),
                -1,
                _(u"Une ligne par portail : libellé | https://adresse"),
            ),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            gap,
        )
        portals_box.Add(self.ctrl_portals, 1, wx.EXPAND | wx.ALL, gap)

        note = wx.StaticText(
            self,
            -1,
            _(
                u"Cette fiche conserve uniquement des références administratives et des liens. "
                u"Les informations d'authentification ne sont pas saisies ici."
            ),
        )
        note.Wrap(UTILS_Styles.Scale(620, minimum=500))

        buttons = wx.StdDialogButtonSizer()
        buttons.AddButton(self.bouton_ok)
        buttons.AddButton(self.bouton_annuler)
        buttons.Realize()

        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(grid, 0, wx.EXPAND | wx.ALL, page_gap)
        main.Add(refs_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        main.Add(portals_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        main.Add(note, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        main.Add(buttons, 0, wx.ALIGN_RIGHT | wx.ALL, page_gap)
        self.SetSizer(main)

    def _build_request(self):
        index = self.choice_kind.GetSelection()
        if index < 0 or index >= len(self._supported_kinds):
            raise ValueError("Sélectionnez une famille d'organisme.")
        return StructureOrganizationProfileRequest(
            code=self.ctrl_code.GetValue(),
            label=self.ctrl_label.GetValue(),
            kind=self._supported_kinds[index],
            references=_parse_references(self.ctrl_references.GetValue()),
            portal_links=_parse_portals(self.ctrl_portals.GetValue()),
            starts_on=_parse_date(self.ctrl_start.GetValue(), _(u"La date d'effet")),
            ends_on=_parse_date(self.ctrl_end.GetValue(), _(u"La date de fin")),
        )

    def OnOk(self, event):
        try:
            request = self._build_request()
        except (TypeError, ValueError) as exc:
            wx.MessageBox(
                str(exc),
                _(u"Organisme RH à vérifier"),
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return
        self._request = request
        self.EndModal(wx.ID_OK)

    def GetRequest(self):
        if self._request is None:
            raise RuntimeError("La configuration de l'organisme n'a pas été validée.")
        return self._request


class Dialog(wx.Dialog):
    """Catalogue des organismes RH configurés pour la structure active."""

    def __init__(self, parent, *, runtime_factory=None):
        wx.Dialog.__init__(
            self,
            -1,
            _(u"Organismes & connexions RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        factory = runtime_factory or StructureHrConnectionsRuntimeFactory
        self._runtime = factory().create()
        self._configurations = ()

        self.info = wx.StaticText(
            self,
            -1,
            _(
                u"Centralisez les organismes RH de la structure, leurs références administratives "
                u"et leurs portails. Les connecteurs restent manuels tant qu'aucune intégration "
                u"officielle n'est activée."
            ),
        )
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        for index, (label, width) in enumerate(
            (
                (_(u"Famille"), 160),
                (_(u"Organisme"), 220),
                (_(u"Code"), 140),
                (_(u"Connexion"), 120),
                (_(u"Portails"), 70),
                (_(u"Références"), 80),
            )
        ):
            self.list.InsertColumn(index, label, width=UTILS_Styles.Scale(width, minimum=60))

        self.bouton_ajouter = wx.Button(self, label=_(u"Ajouter"))
        self.bouton_modifier = wx.Button(self, label=_(u"Modifier"))
        self.bouton_modifier.Enable(False)
        self.bouton_fermer = wx.Button(self, wx.ID_CLOSE, _(u"Fermer"))

        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelection)
        self.list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnModifier)
        self.bouton_ajouter.Bind(wx.EVT_BUTTON, self.OnAjouter)
        self.bouton_modifier.Bind(wx.EVT_BUTTON, self.OnModifier)
        self.bouton_fermer.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE))

        self._layout()
        self.Reload()
        self.SetMinSize(
            (
                UTILS_Styles.Scale(900, minimum=720),
                UTILS_Styles.Scale(520, minimum=420),
            )
        )
        self.CentreOnParent()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        self.info.Wrap(UTILS_Styles.Scale(820, minimum=660))

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_ajouter, 0, wx.RIGHT, gap)
        actions.Add(self.bouton_modifier, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_fermer, 0)

        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(self.info, 0, wx.EXPAND | wx.ALL, page_gap)
        main.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        main.Add(actions, 0, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(main)

    def Reload(self):
        self._configurations = self._runtime.list_configurations()
        self.list.DeleteAllItems()
        for configuration in self._configurations:
            profile = configuration.profile
            values = (
                _KIND_LABELS.get(profile.organization.kind, profile.organization.kind.value),
                profile.organization.label,
                profile.organization.code,
                _(u"Configuré") if configuration.has_configured_connector else _(u"À compléter"),
                str(len(profile.portal_links)),
                str(len(profile.references)),
            )
            row = self.list.InsertItem(self.list.GetItemCount(), values[0])
            for column, value in enumerate(values[1:], 1):
                self.list.SetItem(row, column, value)
        self.bouton_modifier.Enable(False)

    def _selected_configuration(self):
        index = self.list.GetFirstSelected()
        if index < 0 or index >= len(self._configurations):
            return None
        return self._configurations[index]

    def OnSelection(self, event):
        self.bouton_modifier.Enable(self._selected_configuration() is not None)
        event.Skip()

    def OnAjouter(self, event):
        dlg = ProfileDialog(
            self,
            supported_kinds=self._runtime.supported_kinds(),
        )
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self._runtime.save_configuration(dlg.GetRequest())
        except Exception as exc:
            wx.MessageBox(
                str(exc),
                _(u"Organisme RH non enregistré"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return
        finally:
            dlg.Destroy()
        self.Reload()

    def OnModifier(self, event):
        configuration = self._selected_configuration()
        if configuration is None:
            return
        dlg = ProfileDialog(
            self,
            supported_kinds=self._runtime.supported_kinds(),
            configuration=configuration,
        )
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self._runtime.save_configuration(dlg.GetRequest())
        except Exception as exc:
            wx.MessageBox(
                str(exc),
                _(u"Organisme RH non enregistré"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return
        finally:
            dlg.Destroy()
        self.Reload()
