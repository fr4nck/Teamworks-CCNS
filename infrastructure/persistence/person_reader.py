#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Callable, Optional

from domain.repositories.person_data import PersonIdentityRecord
from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance


class PersonReader:
    """Lecteur SQL des personnes au-dessus de GestionDB, sans dépendance wxPython."""

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

    def _fetch(self, req: str, nom_mesure: str):
        with DiagnosticPerformance.mesurer("sql", nom_mesure, {"reader": "PersonReader"}):
            self.db.ExecuterReq(req)
            return self.db.ResultatReq()

    def lire_identites(self) -> list[PersonIdentityRecord]:
        """Lit les identités minimales des personnes triées comme les écrans historiques."""
        req = """SELECT IDpersonne, nom, prenom FROM personnes ORDER BY nom, prenom;"""
        rows = self._fetch(req, "PersonReader.lire_identites")
        with DiagnosticPerformance.mesurer(
            "python",
            "PersonReader.lire_identites.mapping",
            {"reader": "PersonReader", "lignes": len(rows)},
        ):
            return [PersonIdentityRecord(*row) for row in rows]

    def close(self) -> None:
        if self._db is not None:
            self._db.Close()
            self._db = None
