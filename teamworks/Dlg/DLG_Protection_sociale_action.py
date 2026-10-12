#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dialogues CRH-20 pour les actions de protection sociale salarié.

Ces dialogues construisent uniquement des demandes applicatives. Ils ne connaissent
ni ``GestionDB``, ni les repositories, ni la structure active et n'écrivent aucune
donnée directement.
"""

import datetime

import wx

from application.services.hr_connections import EmployeeProtectionCreateRequest
from domain.hr_connections import (
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    OrganizationKind,
)
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


_KIND_LABELS = {
    OrganizationKind.MUTUELLE: _(u"Mutuelle"),
    OrganizationKind.PREVOYANCE: _(u"Prévoyance"),
    OrganizationKind.RETRAITE_COMPLEMENTAIRE: _(u"Retraite complémentaire"),
    OrganizationKind.SPST: _(u"Santé au travail"),
}

_RELATION_LABELS = {
    EmployeeProtectionRelationKind.AFFILIATION: _(u"Affiliation"),
    EmployeeProtectionRelationKind.WAIVER: _(u"Dispense"),
    EmployeeProtectionRelationKind.REGISTRATION: _(u"Enregistrement"),
    EmployeeProtectionRelationKind.MONITORING: _(u"Suivi administratif"),
}

_STATUS_LABELS = {
    EmployeeProtectionStatus.TODO: _(u"À faire"),
    EmployeeProtectionStatus.PENDING: _(u"En attente"),
    EmployeeProtectionStatus.ACTIVE: _(u"Actif"),
}

_RELATIONS_BY_KIND = {
    OrganizationKind.MUTUELLE: (
        EmployeeProtectionRelationKind.AFFILIATION,
        EmployeeProtectionRelationKind.WAIVER,
        EmployeeProtectionRelationKind.REGISTRATION,
    ),
    OrganizationKind.PREVOYANCE: (
        EmployeeProtectionRelationKind.AFFILIATION,
        EmployeeProtectionRelationKind.REGISTRATION,
    ),
    OrganizationKind.RETRAITE_COMPLEMENTAIRE: (
        EmployeeProtectionRelationKind.AFFILIATION,
        EmployeeProtectionRelationKind.REGISTRATION,
    ),
    OrganizationKind.SPST: (
        EmployeeProtectionRelationKind.REGISTRATION,
        EmployeeProtectionRelationKind.MONITORING,
    ),
}


def _optional_text(control):
    value = control.GetValue().strip()
    return value or None


def _format_date(value):
    return value.strftime("%d/%m/%Y") if value is not None else u""


def _parse_date(value, label, required=False):
    text = value.strip()
    if not text:
        if required:
            raise ValueError(u"%s est obligatoire." % label)
        return None

    for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(text, pattern).date()
        except ValueError:
            pass
    raise ValueError(
        u"%s doit utiliser le format JJ/MM/AAAA (ou AAAA-MM-JJ)." % label
    )


class Dialog(wx.Dialog):
    """Création d'un suivi ou préparation d'une période successeure."""

    def __init__(
        self,
        parent,
        *,
        organizations,
        current_record=None,
        succession=False,
    ):
        title = (
            _(u"Nouvelle période de protection sociale")
            if succession
            else _(u"Ajouter un suivi de protection sociale")
        )
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._organizations = tuple(organizations)
        if not self._organizations:
            raise ValueError("Au moins un organisme configuré est nécessaire.")
        self._current_record = current_record
        self._succession = bool(succession)
        self._request = None
        self._relation_values = ()
        self._status_values = (
            (EmployeeProtectionStatus.ACTIVE,)
            if self._succession
            else (
                EmployeeProtectionStatus.ACTIVE,
                EmployeeProtectionStatus.PENDING,
                EmployeeProtectionStatus.TODO,
            )
        )

        self.choice_organization = wx.Choice(
            self,
            choices=[self._organization_label(option) for option in self._organizations],
        )
        self.choice_relation = wx.Choice(self)
        self.choice_status = wx.Choice(
            self,
            choices=[_STATUS_LABELS[value] for value in self._status_values],
        )

        self.ctrl_start = wx.TextCtrl(self)
        self.ctrl_end = wx.TextCtrl(self)
        self.ctrl_scheme = wx.TextCtrl(self)
        self.ctrl_option = wx.TextCtrl(self)
        self.ctrl_contribution = wx.TextCtrl(self)
        self.ctrl_waiver = wx.TextCtrl(self)
        self.ctrl_external = wx.TextCtrl(self)
        self.ctrl_document = wx.TextCtrl(self)
        self.ctrl_deadline = wx.TextCtrl(self)

        self.help_date = wx.StaticText(
            self,
            -1,
            _(u"Dates : JJ/MM/AAAA. Les champs non applicables peuvent rester vides."),
        )

        self.bouton_ok = wx.Button(self, wx.ID_OK, _(u"Enregistrer"))
        self.bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))

        self.choice_organization.Bind(wx.EVT_CHOICE, self.OnOrganizationChanged)
        self.choice_relation.Bind(wx.EVT_CHOICE, self.OnRelationChanged)
        self.bouton_ok.Bind(wx.EVT_BUTTON, self.OnOk)

        self._prefill()
        self._layout()
        self.SetMinSize(
            (
                UTILS_Styles.Scale(560, minimum=480),
                UTILS_Styles.Scale(520, minimum=420),
            )
        )
        self.Fit()
        self.CentreOnParent()

    @staticmethod
    def _organization_label(option):
        family = _KIND_LABELS.get(option.kind, option.kind.value)
        return u"%s — %s" % (family, option.label)

    def _prefill(self):
        organization_index = 0
        current_relation = None
        if self._current_record is not None:
            for index, option in enumerate(self._organizations):
                if option.code == self._current_record.organization_code:
                    organization_index = index
                    break
            current_relation = self._current_record.relation_kind
            self.ctrl_scheme.SetValue(self._current_record.scheme_code or u"")
            self.ctrl_option.SetValue(self._current_record.option_code or u"")
            self.ctrl_contribution.SetValue(
                self._current_record.contribution_profile_code or u""
            )
            self.ctrl_waiver.SetValue(
                self._current_record.waiver_reason_code or u""
            )
            self.ctrl_external.SetValue(
                self._current_record.external_reference or u""
            )
            self.ctrl_document.SetValue(self._current_record.document_ref or u"")
            self.ctrl_deadline.SetValue(
                _format_date(self._current_record.administrative_deadline)
            )

        self.choice_organization.SetSelection(organization_index)
        self._refresh_relations(preferred=current_relation)
        self.choice_status.SetSelection(0)
        self.choice_status.Enable(not self._succession)

        if self._succession and self._current_record is not None:
            start = self._current_record.effective_period.starts_on
            minimum_next = (
                start + datetime.timedelta(days=1)
                if start is not None
                else datetime.date.today()
            )
            self.ctrl_start.SetValue(_format_date(max(datetime.date.today(), minimum_next)))
            self.ctrl_end.SetValue(u"")
        elif self._current_record is not None:
            self.ctrl_start.SetValue(
                _format_date(self._current_record.effective_period.starts_on)
            )
            self.ctrl_end.SetValue(
                _format_date(self._current_record.effective_period.ends_on)
            )
        else:
            self.ctrl_start.SetValue(_format_date(datetime.date.today()))

        self._sync_kind_controls()

    def _layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")

        grid = wx.FlexGridSizer(cols=2, vgap=gap, hgap=gap)
        grid.AddGrowableCol(1, 1)

        fields = (
            (_(u"Organisme"), self.choice_organization),
            (_(u"Nature du lien"), self.choice_relation),
            (_(u"Statut"), self.choice_status),
            (_(u"Date d'effet"), self.ctrl_start),
            (_(u"Date de fin"), self.ctrl_end),
            (_(u"Régime / code"), self.ctrl_scheme),
            (_(u"Option"), self.ctrl_option),
            (_(u"Profil de cotisation"), self.ctrl_contribution),
            (_(u"Motif codifié de dispense"), self.ctrl_waiver),
            (_(u"Référence externe"), self.ctrl_external),
            (_(u"Référence du justificatif"), self.ctrl_document),
            (_(u"Échéance administrative"), self.ctrl_deadline),
        )
        for label, control in fields:
            text = wx.StaticText(self, -1, label)
            grid.Add(text, 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)

        buttons = wx.StdDialogButtonSizer()
        buttons.AddButton(self.bouton_ok)
        buttons.AddButton(self.bouton_annuler)
        buttons.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        if self._succession:
            message = wx.StaticText(
                self,
                -1,
                _(
                    u"La période actuelle sera clôturée la veille de la nouvelle "
                    u"date d'effet. Les deux écritures sont transactionnelles."
                ),
            )
            message.Wrap(UTILS_Styles.Scale(520, minimum=420))
            sizer.Add(message, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, page_gap)
            sizer.AddSpacer(gap)

        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(self.help_date, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(buttons, 0, wx.ALIGN_RIGHT | wx.ALL, page_gap)
        self.SetSizer(sizer)

    def _selected_organization(self):
        index = self.choice_organization.GetSelection()
        if index < 0:
            raise ValueError("Sélectionnez un organisme.")
        return self._organizations[index]

    def _refresh_relations(self, preferred=None):
        organization = self._selected_organization()
        self._relation_values = _RELATIONS_BY_KIND.get(organization.kind, ())
        self.choice_relation.Set(
            [_RELATION_LABELS[value] for value in self._relation_values]
        )
        selection = 0
        if preferred in self._relation_values:
            selection = self._relation_values.index(preferred)
        if self._relation_values:
            self.choice_relation.SetSelection(selection)

    def _selected_relation(self):
        index = self.choice_relation.GetSelection()
        if index < 0 or index >= len(self._relation_values):
            raise ValueError("Sélectionnez la nature du lien.")
        return self._relation_values[index]

    def _selected_status(self):
        index = self.choice_status.GetSelection()
        if index < 0:
            raise ValueError("Sélectionnez le statut.")
        return self._status_values[index]

    def _sync_kind_controls(self):
        organization = self._selected_organization()
        relation = self._selected_relation()
        social_protection = organization.kind is not OrganizationKind.SPST
        self.ctrl_scheme.Enable(social_protection)
        self.ctrl_option.Enable(social_protection)
        self.ctrl_contribution.Enable(social_protection)
        self.ctrl_waiver.Enable(
            organization.kind is OrganizationKind.MUTUELLE
            and relation is EmployeeProtectionRelationKind.WAIVER
        )

    def OnOrganizationChanged(self, event):
        previous = None
        try:
            previous = self._selected_relation()
        except ValueError:
            pass
        self._refresh_relations(preferred=previous)
        self._sync_kind_controls()
        event.Skip()

    def OnRelationChanged(self, event):
        self._sync_kind_controls()
        event.Skip()

    def _build_request(self):
        organization = self._selected_organization()
        relation = self._selected_relation()
        status = self._selected_status()
        starts_on = _parse_date(
            self.ctrl_start.GetValue(),
            _(u"La date d'effet"),
            required=status is EmployeeProtectionStatus.ACTIVE or self._succession,
        )
        ends_on = _parse_date(
            self.ctrl_end.GetValue(),
            _(u"La date de fin"),
        )
        deadline = _parse_date(
            self.ctrl_deadline.GetValue(),
            _(u"L'échéance administrative"),
        )

        spst = organization.kind is OrganizationKind.SPST
        waiver = (
            organization.kind is OrganizationKind.MUTUELLE
            and relation is EmployeeProtectionRelationKind.WAIVER
        )
        return EmployeeProtectionCreateRequest(
            organization_code=organization.code,
            organization_kind=organization.kind,
            relation_kind=relation,
            status=EmployeeProtectionStatus.ACTIVE if self._succession else status,
            starts_on=starts_on,
            ends_on=ends_on,
            scheme_code=None if spst else _optional_text(self.ctrl_scheme),
            option_code=None if spst else _optional_text(self.ctrl_option),
            contribution_profile_code=(
                None if spst else _optional_text(self.ctrl_contribution)
            ),
            waiver_reason_code=(
                _optional_text(self.ctrl_waiver) if waiver else None
            ),
            external_reference=_optional_text(self.ctrl_external),
            document_ref=_optional_text(self.ctrl_document),
            administrative_deadline=deadline,
            source="teamworks-ui",
        )

    def OnOk(self, event):
        try:
            request = self._build_request()
        except (TypeError, ValueError) as exc:
            wx.MessageBox(
                str(exc),
                _(u"Protection sociale"),
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return
        self._request = request
        self.EndModal(wx.ID_OK)

    def GetRequest(self):
        if self._request is None:
            raise RuntimeError("La demande de protection sociale n'a pas été validée.")
        return self._request


class ClotureDialog(wx.Dialog):
    """Saisie limitée à la date de fin d'une période active."""

    def __init__(self, parent, *, current_record):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Clôturer le suivi de protection sociale"),
            style=wx.DEFAULT_DIALOG_STYLE,
        )
        self._current_record = current_record
        self._end_date = None

        start = current_record.effective_period.starts_on
        current_end = current_record.effective_period.ends_on
        today = datetime.date.today()
        if current_end is not None:
            default_date = current_end
        elif start is not None and today < start:
            default_date = start
        else:
            default_date = today

        self.info = wx.StaticText(
            self,
            -1,
            _(u"Date d'effet actuelle : %s") % _format_date(start),
        )
        self.ctrl_end = wx.TextCtrl(self, value=_format_date(default_date))
        self.bouton_ok = wx.Button(self, wx.ID_OK, _(u"Clôturer"))
        self.bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))
        self.bouton_ok.Bind(wx.EVT_BUTTON, self.OnOk)

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, _(u"Date de fin")), 0, wx.ALIGN_CENTER_VERTICAL)
        row.Add(self.ctrl_end, 1, wx.LEFT, gap)

        buttons = wx.StdDialogButtonSizer()
        buttons.AddButton(self.bouton_ok)
        buttons.AddButton(self.bouton_annuler)
        buttons.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.info, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(buttons, 0, wx.ALIGN_RIGHT | wx.ALL, page_gap)
        self.SetSizerAndFit(sizer)
        self.CentreOnParent()

    def OnOk(self, event):
        try:
            ends_on = _parse_date(
                self.ctrl_end.GetValue(),
                _(u"La date de fin"),
                required=True,
            )
            start = self._current_record.effective_period.starts_on
            if start is not None and ends_on < start:
                raise ValueError(
                    _(u"La date de fin ne peut pas précéder la date d'effet.")
                )
            current_end = self._current_record.effective_period.ends_on
            if current_end is not None and ends_on > current_end:
                raise ValueError(
                    _(
                        u"La clôture ne peut pas prolonger une date de fin "
                        u"déjà enregistrée."
                    )
                )
        except (TypeError, ValueError) as exc:
            wx.MessageBox(
                str(exc),
                _(u"Protection sociale"),
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return
        self._end_date = ends_on
        self.EndModal(wx.ID_OK)

    def GetEndDate(self):
        if self._end_date is None:
            raise RuntimeError("La date de clôture n'a pas été validée.")
        return self._end_date
