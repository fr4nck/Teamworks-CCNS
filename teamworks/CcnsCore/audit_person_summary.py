#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts
from teamworks.CcnsCore.audit_sorting import compute_row_severity
from infrastructure.persistence.ccns_data_reader import CcnsDataReader


class _PersonScopedCcnsReader:
    """Adaptateur limitant l'audit CCNS aux contrats d'une personne."""

    def __init__(self, reader, IDpersonne):
        self._reader = reader
        self._IDpersonne = IDpersonne

    def lire_contrats(self, limit=None):
        if hasattr(self._reader, "lire_contrats_personne"):
            return self._reader.lire_contrats_personne(self._IDpersonne, limit=limit)
        return self._reader.lire_contrats(limit=limit)

    def lire_grilles(self, limit=None):
        return self._reader.lire_grilles(limit=limit)

    def lire_lignes_grille(self, IDtw_salary_grid):
        return self._reader.lire_lignes_grille(IDtw_salary_grid)


def build_person_ccns_summary(IDpersonne, data_reader=None, reference_date=None):
    """Construit la synthèse CCNS d'une personne sans dépendance wxPython.

    La lecture des contrats est déléguée au Reader CCNS afin de conserver les
    requêtes SQL hors des helpers d'interface. Les lignes retournées restent des
    dictionnaires simples pour les intégrations historiques des dossiers
    incomplets et de la fiche individuelle.
    """
    reader = data_reader or CcnsDataReader()
    close_reader = data_reader is None
    try:
        rows = audit_contracts(
            data_reader=_PersonScopedCcnsReader(reader, IDpersonne),
            reference_date=reference_date,
        )
        prepared = []
        nb_blocking = 0
        nb_warning = 0
        nb_ok = 0
        nb_anomalies = 0

        for row in rows:
            severity_label, severity_rank = compute_row_severity({"anomalies": row.anomalies})
            nb_anomalies += len(row.anomalies)
            if severity_label == "blocking":
                nb_blocking += 1
            elif severity_label == "warning":
                nb_warning += 1
            else:
                nb_ok += 1
            prepared.append({
                "IDcontrat": row.IDcontrat,
                "nom_complet": row.nom_complet,
                "classification": row.classification or "",
                "type_contrat": row.type_contrat or "",
                "salaire_base": row.salaire_base,
                "anomalies": row.anomalies,
                "messages": row.messages,
                "severity_label": severity_label,
                "severity_rank": severity_rank,
            })

        prepared.sort(key=lambda item: (item["severity_rank"], item["IDcontrat"]))
        global_status = _compute_global_status(len(prepared), nb_blocking, nb_warning)
        return {
            "IDpersonne": IDpersonne,
            "global_status": global_status,
            "nb_contracts": len(prepared),
            "nb_anomalies": nb_anomalies,
            "nb_blocking": nb_blocking,
            "nb_warning": nb_warning,
            "nb_ok": nb_ok,
            "rows": prepared,
        }
    finally:
        if close_reader:
            reader.close()


def _compute_global_status(nb_contracts, nb_blocking, nb_warning):
    if nb_contracts == 0:
        return "AUCUN_CONTRAT"
    if nb_blocking > 0:
        return "BLOQUANT"
    if nb_warning > 0:
        return "A_REVOIR"
    return "OK"
