#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Panneau wxPython « Protection sociale & organismes ».

Le panneau rend une ``EmployeeProtectionSummary`` déjà construite par la couche
applicative et expose seulement des intentions d'action. Il ne choisit aucun
backend, n'ouvre aucun portail et n'effectue aucun calcul de cotisation ou de
conformité réglementaire.
"""

import wx

from application.services.hr_connections.employee_protection_summary import (
    EmployeeProtectionSummary,
)
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Section
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


_ORGANIZATION_LABELS = {
    "mutuelle": _(u"Mutuelle"),
    "prevoyance": _(u"Prévoyance"),
    "retraite_complementaire": _(u"Retraite complémentaire"),
    "spst": _(u"Santé au travail"),
}

_RELATION_LABELS = {
    "affiliation": _(u"Affiliation"),
    "waiver": _(u"Dispense"),
    "registration": _(u"Enregistrement"),
    "monitoring": _(u"Suivi administratif"),
}

_STATUS_LABELS = {
    "todo": _(u"À faire"),
    "pending": _(u"En attente"),
    "active": _(u"Actif"),
    "ended": _(u"Terminé"),
    "cancelled": _(u"Annulé"),
}


def _date_fr(value):
    if value is None:
        return u"—"
    return value.strftime("%d/%m/%Y")


def _enum_label(mapping, value):
    raw = getattr(value, "value", value)
    return mapping.get(raw, str(raw))


class Panel(wx.Panel):
    """Vue descriptive et frontière d'intentions de la protection sociale salarié."""

    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Panel.__init__(
            self,
            parent,
            id,
            name="page_protection_sociale",
            style=wx.TAB_TRAVERSAL,
        )
        self.IDpersonne = IDpersonne
        self._summary = None
        self._rows = ()
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.section_synthese = CTRL_Section.Section(
            self,
            titre=_(u"Protection sociale & organismes"),
            niveau=2,
        )
        panel_synthese = self.section_synthese.GetContentPanel()

        self.info = wx.StaticText(
            panel_synthese,
            -1,
            _(u"Aucune synthèse n'est chargée pour ce salarié."),
        )
        self.info.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        self.compteurs = wx.StaticText(panel_synthese, -1, u"")
        font = self.compteurs.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.compteurs.SetFont(font)
        self.compteurs.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        self.bouton_ajouter = CTRL_Bouton_image.CTRL(
            panel_synthese,
            texte=_(u"Ajouter"),
        )
        self.bouton_cloturer = CTRL_Bouton_image.CTRL(
            panel_synthese,
            texte=_(u"Clôturer"),
        )
        self.bouton_nouvelle_periode = CTRL_Bouton_image.CTRL(
            panel_synthese,
            texte=_(u"Nouvelle période"),
        )
        self.bouton_ajouter.Bind(wx.EVT_BUTTON, self.OnAjouter)
        self.bouton_cloturer.Bind(wx.EVT_BUTTON, self.OnCloturer)
        self.bouton_nouvelle_periode.Bind(wx.EVT_BUTTON, self.OnNouvellePeriode)

        self.liste = wx.ListCtrl(
            panel_synthese,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
        )
        self.liste.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.liste.SetTextColour(UTILS_Interface.GetToken("on_surface"))
        self.liste.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChanged)
        self.liste.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChanged)

        for index, (label, width) in enumerate(
            (
                (_(u"Organisme"), 190),
                (_(u"Nature"), 150),
                (_(u"Statut"), 105),
                (_(u"Début"), 95),
                (_(u"Fin"), 95),
                (_(u"Échéance"), 95),
                (_(u"Paie"), 70),
                (_(u"Configuration"), 120),
            )
        ):
            self.liste.InsertColumn(
                index,
                label,
                width=UTILS_Styles.Scale(width, minimum=60),
            )

        self._do_layout(panel_synthese)
        self._update_action_state()

    def _do_layout(self, panel_synthese):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_ajouter, 0, wx.RIGHT, gap)
        actions.Add(self.bouton_cloturer, 0, wx.RIGHT, gap)
        actions.Add(self.bouton_nouvelle_periode, 0)

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.info, 0, wx.EXPAND | wx.BOTTOM, gap)
        contenu.Add(self.compteurs, 0, wx.EXPAND | wx.BOTTOM, gap)
        contenu.Add(actions, 0, wx.EXPAND | wx.BOTTOM, gap)
        contenu.Add(self.liste, 1, wx.EXPAND)
        panel_synthese.SetSizer(contenu)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(
            self.section_synthese,
            1,
            wx.EXPAND | wx.ALL,
            page_gap,
        )
        self.SetSizer(sizer)

    def SetUnavailable(self, message=None):
        """Affiche explicitement l'absence de données sans simuler un état métier."""

        self._summary = None
        self._rows = ()
        self.compteurs.SetLabel(u"")
        self.liste.DeleteAllItems()
        self.info.SetLabel(
            message
            or _(u"Le suivi de protection sociale n'est pas encore raccordé pour ce salarié.")
        )
        self._update_action_state()
        self.Layout()

    def SetSummary(self, summary):
        """Rend une synthèse construite par ``EmployeeProtectionSummaryService``."""

        if not isinstance(summary, EmployeeProtectionSummary):
            raise TypeError("La synthèse de protection sociale salarié est invalide.")

        self._summary = summary
        self._rows = tuple(summary.rows)
        self.info.SetLabel(
            _(u"Situation descriptive au %s. Les obligations réglementaires restent contrôlées séparément.")
            % _date_fr(summary.as_of)
        )
        self.compteurs.SetLabel(
            _(u"%d suivi(s) · %d effectif(s) · %d en attente · %d échéance(s) · %d paie-ready · %d organisme(s) non configuré(s)")
            % (
                summary.total_count,
                summary.effective_count,
                summary.pending_count,
                summary.due_count,
                summary.payroll_relevant_count,
                summary.orphan_configuration_count,
            )
        )

        self.liste.Freeze()
        try:
            self.liste.DeleteAllItems()
            for row in self._rows:
                famille = _enum_label(_ORGANIZATION_LABELS, row.organization_kind)
                organisme = row.organization_label or u"%s · %s" % (
                    famille,
                    row.organization_code,
                )
                values = (
                    organisme,
                    _enum_label(_RELATION_LABELS, row.relation_kind),
                    _enum_label(_STATUS_LABELS, row.status),
                    _date_fr(row.effective_start),
                    _date_fr(row.effective_end),
                    _date_fr(row.administrative_deadline),
                    _(u"Oui") if row.payroll_relevant else _(u"Non"),
                    _(u"Configuré") if row.organization_configured else _(u"À reconfigurer"),
                )
                index = self.liste.InsertItem(self.liste.GetItemCount(), values[0])
                for column, value in enumerate(values[1:], 1):
                    self.liste.SetItem(index, column, value)
                if row.due or not row.organization_configured:
                    self.liste.SetItemTextColour(
                        index,
                        UTILS_Interface.GetToken("warning"),
                    )
        finally:
            self.liste.Thaw()

        self._update_action_state()
        self.Layout()

    def GetSummary(self):
        return self._summary

    def GetSelectedSummaryRow(self):
        """Renvoie la ligne sélectionnée sans exposer le contrôle wx à la couche runtime."""
        index = self.liste.GetFirstSelected()
        if index < 0 or index >= len(self._rows):
            return None
        return self._rows[index]

    def _update_action_state(self):
        loaded = self._summary is not None and bool(self.IDpersonne)
        self.bouton_ajouter.Enable(loaded)

        selected = self.GetSelectedSummaryRow() if loaded else None
        status = getattr(getattr(selected, "status", None), "value", None)
        active = status == "active"
        self.bouton_cloturer.Enable(active)
        self.bouton_nouvelle_periode.Enable(active)

    def OnSelectionChanged(self, event):
        self._update_action_state()
        event.Skip()

    def OnAjouter(self, event):
        """Point d'extension : le panneau de présentation n'exécute pas l'action."""
        event.Skip()

    def OnCloturer(self, event):
        """Point d'extension : le panneau de présentation n'exécute pas l'action."""
        event.Skip()

    def OnNouvellePeriode(self, event):
        """Point d'extension : le panneau de présentation n'exécute pas l'action."""
        event.Skip()
