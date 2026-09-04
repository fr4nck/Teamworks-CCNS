#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Raccordement runtime de la page « Protection sociale & organismes ».

La lecture reste chargée à l'ouverture de l'onglet. Le runtime d'écriture et les
boîtes de dialogue CRH-20 ne sont importés et composés qu'au premier clic sur une
action afin de préserver le caractère défensif du raccordement salarié.
"""

import datetime
import logging

import wx

from application.bootstrap.employee_protection_summary_factory import (
    EmployeeProtectionSummaryRuntimeFactory,
)
from Ctrl import CTRL_Page_protection_sociale
from Utils.UTILS_Traduction import _


LOGGER = logging.getLogger(__name__)


class Panel(CTRL_Page_protection_sociale.Panel):
    """Page salarié raccordée à la base Teamworks active avec actions contrôlées."""

    def __init__(
        self,
        parent,
        id=-1,
        IDpersonne=0,
        runtime_factory=None,
        actions_runtime_factory=None,
    ):
        self._runtime_factory = runtime_factory or EmployeeProtectionSummaryRuntimeFactory
        self._actions_runtime_factory = actions_runtime_factory
        self._runtime = None
        self._actions_runtime = None
        super(Panel, self).__init__(parent, id=id, IDpersonne=IDpersonne)
        self.LoadSummary()

    def LoadSummary(self, as_of=None):
        """Recharge la synthèse sans exposer le backend au panneau de présentation."""
        if not self.IDpersonne:
            self.SetUnavailable(
                _(u"Le suivi sera disponible après l'enregistrement de la fiche salarié.")
            )
            return False

        reference_date = as_of or datetime.date.today()
        if not isinstance(reference_date, datetime.date):
            raise TypeError("La date de consultation de la protection sociale est invalide.")

        try:
            if self._runtime is None:
                self._runtime = self._runtime_factory().create()
            summary = self._runtime.build(
                employee_ref=str(self.IDpersonne),
                as_of=reference_date,
            )
        except Exception:
            LOGGER.exception(
                "Chargement du suivi de protection sociale salarié impossible."
            )
            self.SetUnavailable(
                _(
                    u"Le suivi de protection sociale est momentanément indisponible. "
                    u"La fiche salarié reste utilisable."
                )
            )
            return False

        self.SetSummary(summary)
        return True

    def _get_actions_runtime(self):
        """Compose le chemin d'écriture seulement lorsqu'une action est demandée."""
        if self._actions_runtime is not None:
            return self._actions_runtime

        factory = self._actions_runtime_factory
        if factory is None:
            from application.bootstrap.employee_protection_actions_factory import (
                EmployeeProtectionActionsRuntimeFactory,
            )

            factory = EmployeeProtectionActionsRuntimeFactory

        self._actions_runtime = factory().create()
        return self._actions_runtime

    def _selected_active_row(self):
        row = self.GetSelectedSummaryRow()
        if row is None:
            raise ValueError("Sélectionnez un suivi de protection sociale.")
        if getattr(row.status, "value", None) != "active":
            raise ValueError("Cette action est réservée à un suivi actif.")
        return row

    def _reload_after_action(self):
        if not self.LoadSummary():
            raise RuntimeError(
                "L'action a été enregistrée mais la synthèse n'a pas pu être rechargée."
            )

    def _show_action_error(self, message, exc=None):
        if exc is not None:
            LOGGER.exception(message)
            details = str(exc).strip()
            if details:
                message = u"%s\n\n%s" % (message, details)
        wx.MessageBox(
            message,
            _(u"Protection sociale"),
            wx.OK | wx.ICON_ERROR,
            self,
        )

    def OnAjouter(self, event):
        """Crée un suivi via le cas d'usage CRH-18, jamais par écriture UI directe."""
        try:
            runtime = self._get_actions_runtime()
            organizations = runtime.available_organizations()
            if not organizations:
                wx.MessageBox(
                    _(
                        u"Aucun organisme compatible n'est configuré pour la structure. "
                        u"Configurez d'abord la mutuelle, la prévoyance, la retraite "
                        u"complémentaire ou le service de santé au travail."
                    ),
                    _(u"Protection sociale"),
                    wx.OK | wx.ICON_INFORMATION,
                    self,
                )
                return

            from Dlg import DLG_Protection_sociale_action

            dlg = DLG_Protection_sociale_action.Dialog(
                self,
                organizations=organizations,
                succession=False,
            )
            try:
                if dlg.ShowModal() != wx.ID_OK:
                    return
                request = dlg.GetRequest()
            finally:
                dlg.Destroy()

            runtime.register(
                employee_ref=str(self.IDpersonne),
                request=request,
            )
            self._reload_after_action()
        except Exception as exc:
            self._show_action_error(
                _(u"Le suivi de protection sociale n'a pas pu être enregistré."),
                exc,
            )

    def OnCloturer(self, event):
        """Clôture uniquement la période active sélectionnée."""
        try:
            row = self._selected_active_row()
            runtime = self._get_actions_runtime()
            current = runtime.get_record(
                employee_ref=str(self.IDpersonne),
                record_id=row.record_id,
            )

            from Dlg import DLG_Protection_sociale_action

            dlg = DLG_Protection_sociale_action.ClotureDialog(
                self,
                current_record=current,
            )
            try:
                if dlg.ShowModal() != wx.ID_OK:
                    return
                ends_on = dlg.GetEndDate()
            finally:
                dlg.Destroy()

            runtime.end(
                employee_ref=str(self.IDpersonne),
                record_id=row.record_id,
                ends_on=ends_on,
            )
            self._reload_after_action()
        except Exception as exc:
            self._show_action_error(
                _(u"Le suivi de protection sociale n'a pas pu être clôturé."),
                exc,
            )

    def OnNouvellePeriode(self, event):
        """Remplace une période active par sa successeure transactionnelle CRH-19."""
        try:
            row = self._selected_active_row()
            runtime = self._get_actions_runtime()
            current = runtime.get_record(
                employee_ref=str(self.IDpersonne),
                record_id=row.record_id,
            )
            organizations = runtime.available_organizations()
            if not organizations:
                raise ValueError(
                    "Aucun organisme compatible n'est configuré pour la structure."
                )

            from Dlg import DLG_Protection_sociale_action

            dlg = DLG_Protection_sociale_action.Dialog(
                self,
                organizations=organizations,
                current_record=current,
                succession=True,
            )
            try:
                if dlg.ShowModal() != wx.ID_OK:
                    return
                request = dlg.GetRequest()
            finally:
                dlg.Destroy()

            runtime.supersede(
                employee_ref=str(self.IDpersonne),
                record_id=row.record_id,
                request=request,
            )
            self._reload_after_action()
        except Exception as exc:
            self._show_action_error(
                _(u"La nouvelle période de protection sociale n'a pas pu être créée."),
                exc,
            )
