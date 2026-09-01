#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Raccordement runtime de la page « Protection sociale & organismes ».

Ce module est le seul point UI qui compose la page CRH-15 avec le runtime
applicatif CRH-17A. Le panneau de présentation reste indépendant du backend.
"""

import datetime
import logging

from application.bootstrap.employee_protection_summary_factory import (
    EmployeeProtectionSummaryRuntimeFactory,
)
from Ctrl import CTRL_Page_protection_sociale
from Utils.UTILS_Traduction import _


LOGGER = logging.getLogger(__name__)


class Panel(CTRL_Page_protection_sociale.Panel):
    """Page salarié en lecture seule, chargée depuis la base Teamworks active."""

    def __init__(self, parent, id=-1, IDpersonne=0, runtime_factory=None):
        super(Panel, self).__init__(parent, id=id, IDpersonne=IDpersonne)
        self._runtime_factory = runtime_factory or EmployeeProtectionSummaryRuntimeFactory
        self._runtime = None
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
