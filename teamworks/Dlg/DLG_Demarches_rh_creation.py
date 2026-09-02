#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Formulaire CRH-30 d'ouverture explicite d'une démarche RH.

Le dialogue ne déduit aucune obligation réglementaire. Il transforme uniquement
les choix confirmés par l'utilisateur en ``HrCaseCreationRequest`` ; la création
transactionnelle reste portée par CRH-29.
"""

from datetime import date, datetime

import wx

from application.services.hr_connections.hr_case_creation import HrCaseCreationRequest
from domain.hr_connections import ExpectedDocument, HrCaseSubjectKind
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


_ACTIVE_STRUCTURE_SUBJECT = "active-structure"
_REQUIRED_MARKERS = {"obligatoire", "oui", "o", "required", "true", "1"}
_OPTIONAL_MARKERS = {"facultative", "facultatif", "non", "n", "optional", "false", "0"}


def _format_input_date(value):
    return value.strftime("%d/%m/%Y") if value is not None else u""


def _parse_input_date(value, *, label, required):
    text = value.strip()
    if not text:
        if required:
            raise ValueError(_(u"%s est obligatoire.") % label)
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError(_(u"%s doit être saisie au format JJ/MM/AAAA.") % label) from exc


def _parse_expected_documents(value):
    documents = []
    seen_codes = set()
    for line_number, raw_line in enumerate(value.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3:
            raise ValueError(
                _(
                    u"Pièce ligne %d : utilisez exactement « code | libellé | obligatoire/facultative »."
                )
                % line_number
            )
        code, label, requirement = parts
        marker = requirement.casefold()
        if marker in _REQUIRED_MARKERS:
            required = True
        elif marker in _OPTIONAL_MARKERS:
            required = False
        else:
            raise ValueError(
                _(
                    u"Pièce ligne %d : indiquez explicitement « obligatoire » ou « facultative »."
                )
                % line_number
            )
        normalized_code = code.strip()
        if normalized_code.casefold() in seen_codes:
            raise ValueError(_(u"Le code de pièce « %s » est présent plusieurs fois.") % code)
        document = ExpectedDocument.create(
            code=code,
            label=label,
            required=required,
        )
        seen_codes.add(normalized_code.casefold())
        documents.append(document)
    return tuple(documents)


def _required_text(value, label):
    text = value.strip()
    if not text:
        raise ValueError(_(u"%s est obligatoire.") % label)
    return text


class Dialog(wx.Dialog):
    """Saisie explicite d'une démarche avant confirmation par le cockpit."""

    def __init__(self, parent, *, people, organizations, opened_on=None):
        self._people = tuple(people)
        self._organizations = tuple(organizations)
        self._subject_kinds = (
            HrCaseSubjectKind.PERSON,
            HrCaseSubjectKind.STRUCTURE,
        )
        self._request = None

        if not self._organizations:
            raise ValueError(
                _(
                    u"Aucun organisme RH n'est configuré. Configurez d'abord un organisme avant d'ouvrir une démarche."
                )
            )
        if opened_on is None:
            opened_on = date.today()
        if not isinstance(opened_on, date):
            raise TypeError("La date d'ouverture proposée est invalide.")

        wx.Dialog.__init__(
            self,
            parent,
            -1,
            _(u"Nouvelle démarche RH"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        title = wx.StaticText(self, -1, _(u"Ouvrir une démarche RH"))
        title_font = title.GetFont()
        title_font.SetPointSize(max(title_font.GetPointSize() + 2, 11))
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        info = wx.StaticText(
            self,
            -1,
            _(
                u"Aucune obligation, échéance ou pièce réglementaire n'est déduite automatiquement. "
                u"Vous confirmez explicitement les données du dossier avant sa création."
            ),
        )
        info.Wrap(UTILS_Styles.Scale(680, minimum=520))
        info.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        self.subject_kind = wx.Choice(
            self,
            choices=[_(u"Salarié"), _(u"Structure")],
        )
        self.person = wx.Choice(
            self,
            choices=[u"%s — #%s" % (item.label, item.identifier) for item in self._people],
        )
        self.organization = wx.Choice(
            self,
            choices=[u"%s — %s" % (item.label, item.code) for item in self._organizations],
        )
        self.case_type_label = wx.TextCtrl(self)
        self.case_type_code = wx.TextCtrl(self)
        self.opened_on = wx.TextCtrl(self, value=_format_input_date(opened_on))
        self.due_on = wx.TextCtrl(self, value=u"")
        self.documents = wx.TextCtrl(
            self,
            value=u"",
            style=wx.TE_MULTILINE | wx.BORDER_SIMPLE,
        )
        self.comment = wx.TextCtrl(
            self,
            value=u"",
            style=wx.TE_MULTILINE | wx.BORDER_SIMPLE,
        )

        if self._people:
            self.subject_kind.SetSelection(0)
            self.person.SetSelection(0)
        else:
            self.subject_kind.SetSelection(1)
            self.person.Enable(False)
        self.organization.SetSelection(0)

        self.subject_kind.Bind(wx.EVT_CHOICE, self.OnSubjectKind)

        grid = wx.FlexGridSizer(cols=2, vgap=10, hgap=12)
        grid.AddGrowableCol(1, 1)
        fields = (
            (_(u"Sujet"), self.subject_kind),
            (_(u"Salarié"), self.person),
            (_(u"Organisme configuré"), self.organization),
            (_(u"Type de démarche"), self.case_type_label),
            (_(u"Code interne du type"), self.case_type_code),
            (_(u"Date d'ouverture (JJ/MM/AAAA)"), self.opened_on),
            (_(u"Échéance facultative (JJ/MM/AAAA)"), self.due_on),
        )
        for label, control in fields:
            label_ctrl = wx.StaticText(self, -1, label)
            label_ctrl.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))
            grid.Add(label_ctrl, 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)

        documents_label = wx.StaticText(
            self,
            -1,
            _(
                u"Pièces attendues, une par ligne :\n"
                u"code | libellé | obligatoire/facultative\n"
                u"Laissez vide si aucune pièce n'est suivie à l'ouverture."
            ),
        )
        documents_label.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        comment_label = wx.StaticText(self, -1, _(u"Commentaire facultatif"))
        comment_label.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        validate = wx.Button(self, wx.ID_OK, _(u"Continuer"))
        cancel = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))
        validate.SetDefault()
        validate.Bind(wx.EVT_BUTTON, self.OnValidate)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.AddStretchSpacer(1)
        buttons.Add(cancel, 0, wx.RIGHT, UTILS_Styles.GetLayoutSpacing("field_gap"))
        buttons.Add(validate, 0)

        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(title, 0, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(info, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        sizer.Add(documents_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(
            self.documents,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        sizer.Add(comment_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, page_gap)
        sizer.Add(
            self.comment,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        sizer.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, page_gap)
        self.SetSizer(sizer)
        self.SetMinSize(
            (
                UTILS_Styles.Scale(760, minimum=620),
                UTILS_Styles.Scale(700, minimum=560),
            )
        )
        self.CentreOnParent()

    def OnSubjectKind(self, event):
        selection = self.subject_kind.GetSelection()
        is_person = selection == 0
        self.person.Enable(is_person and bool(self._people))
        if is_person and not self._people:
            self.subject_kind.SetSelection(1)
            wx.MessageBox(
                _(u"Aucune personne n'est disponible dans la base active."),
                _(u"Nouvelle démarche RH"),
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
        event.Skip()

    def BuildRequest(self):
        subject_selection = self.subject_kind.GetSelection()
        if subject_selection < 0 or subject_selection >= len(self._subject_kinds):
            raise ValueError(_(u"Sélectionnez le sujet de la démarche."))
        subject_kind = self._subject_kinds[subject_selection]

        if subject_kind is HrCaseSubjectKind.PERSON:
            person_selection = self.person.GetSelection()
            if person_selection < 0 or person_selection >= len(self._people):
                raise ValueError(_(u"Sélectionnez un salarié."))
            subject_identifier = self._people[person_selection].identifier
        else:
            subject_identifier = _ACTIVE_STRUCTURE_SUBJECT

        organization_selection = self.organization.GetSelection()
        if organization_selection < 0 or organization_selection >= len(self._organizations):
            raise ValueError(_(u"Sélectionnez un organisme configuré."))
        organization_code = self._organizations[organization_selection].code

        opened_on = _parse_input_date(
            self.opened_on.GetValue(),
            label=_(u"La date d'ouverture"),
            required=True,
        )
        due_on = _parse_input_date(
            self.due_on.GetValue(),
            label=_(u"L'échéance"),
            required=False,
        )
        if due_on is not None and due_on < opened_on:
            raise ValueError(_(u"L'échéance ne peut pas précéder la date d'ouverture."))

        return HrCaseCreationRequest(
            case_type_code=_required_text(
                self.case_type_code.GetValue(),
                _(u"Le code interne du type"),
            ),
            case_type_label=_required_text(
                self.case_type_label.GetValue(),
                _(u"Le type de démarche"),
            ),
            subject_kind=subject_kind,
            subject_identifier=subject_identifier,
            organization_code=organization_code,
            opened_on=opened_on,
            due_on=due_on,
            expected_documents=_parse_expected_documents(self.documents.GetValue()),
            comment=self.comment.GetValue().strip() or None,
        )

    def OnValidate(self, event):
        try:
            self._request = self.BuildRequest()
        except Exception as exc:
            wx.MessageBox(
                str(exc),
                _(u"Nouvelle démarche RH"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return
        self.EndModal(wx.ID_OK)

    def GetRequest(self):
        if self._request is None:
            raise RuntimeError("La démarche RH n'a pas encore été validée.")
        return self._request
