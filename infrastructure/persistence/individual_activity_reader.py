#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Callable, Optional

from domain.repositories.individual_activity_data import (
    ReimbursementRecord,
    ScenarioRecord,
    TripRecord,
)
from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance


class IndividualActivityReader:
    """Lecteur SQL sans wxPython pour les pages individuelles Scénarios/Frais."""

    def __init__(self, db_factory: Optional[Callable[[], object]] = None):
        self._db_factory = db_factory or self._default_db_factory
        self._db = None

    @staticmethod
    def _default_db_factory():
        import GestionDB

        return GestionDB.DB()

    @property
    def db(self):
        if self._db is None:
            self._db = self._db_factory()
        return self._db

    @staticmethod
    def _person_id(value) -> int:
        if value is None or isinstance(value, bool):
            raise ValueError("IDpersonne historique obligatoire")
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("IDpersonne historique invalide") from exc
        if result <= 0:
            raise ValueError("IDpersonne historique invalide")
        return result

    def _fetch(self, req: str, nom_mesure: str):
        with DiagnosticPerformance.mesurer(
            "sql",
            nom_mesure,
            {"reader": "IndividualActivityReader"},
        ):
            self.db.ExecuterReq(req)
            return self.db.ResultatReq()

    def lire_scenarios_personne(self, IDpersonne) -> list[ScenarioRecord]:
        person_id = self._person_id(IDpersonne)
        req = (
            "SELECT IDscenario, IDpersonne, nom, description, date_debut, date_fin "
            "FROM scenarios WHERE IDpersonne=%d ORDER BY date_debut DESC;" % person_id
        )
        rows = self._fetch(req, "IndividualActivityReader.lire_scenarios_personne")
        return [ScenarioRecord(*row) for row in rows]

    def lire_deplacements_personne(self, IDpersonne) -> list[TripRecord]:
        person_id = self._person_id(IDpersonne)
        req = (
            "SELECT IDdeplacement, date, objet, ville_depart, ville_arrivee, distance, "
            "aller_retour, tarif_km, IDremboursement FROM deplacements "
            "WHERE IDpersonne=%d ORDER BY date;" % person_id
        )
        rows = self._fetch(req, "IndividualActivityReader.lire_deplacements_personne")
        return [TripRecord(*row) for row in rows]

    def lire_remboursements_personne(self, IDpersonne) -> list[ReimbursementRecord]:
        person_id = self._person_id(IDpersonne)
        req = (
            "SELECT IDremboursement, date, montant, listeIDdeplacement FROM remboursements "
            "WHERE IDpersonne=%d ORDER BY date;" % person_id
        )
        rows = self._fetch(req, "IndividualActivityReader.lire_remboursements_personne")
        return [ReimbursementRecord(*row) for row in rows]

    def close(self) -> None:
        if self._db is not None:
            self._db.Close()
            self._db = None
