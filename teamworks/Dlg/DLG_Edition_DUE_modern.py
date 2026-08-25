#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DPAE/DUE compatible avec les contrats modernes Teamworks-CCNS."""

from Dlg import DLG_Edition_DUE as _legacy
from Utils import UTILS_DUE_contrat


class Dialog(_legacy.Dialog):
    """Réutilise le formulaire/PDF historique avec un chargement de données robuste."""

    def Import_Donnees(self):
        self.due_values = UTILS_DUE_contrat.ApplyToLegacyFields(
            self.IDcontrat,
            _legacy.champs,
        )


CreationPDF = _legacy.CreationPDF
champs = _legacy.champs
