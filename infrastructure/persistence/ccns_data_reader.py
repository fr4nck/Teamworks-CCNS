#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Callable, Optional

from domain.repositories.ccns_data import (
    CcnsClassificationRecord,
    CcnsContratRecord,
    CcnsGrilleRecord,
    CcnsLigneGrilleRecord,
)
from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance


class CcnsDataReader:
    """Lecteur SQL CCNS au-dessus de GestionDB, sans dépendance wxPython."""

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
    def _limit_clause(limit: Optional[int]) -> str:
        if limit is None:
            return ""
        limit_value = int(limit)
        if limit_value <= 0:
            return ""
        return " LIMIT %d" % limit_value

    def _fetch(self, req: str, nom: str):
        with DiagnosticPerformance.mesurer("sql", "ccns_data_reader.%s.executer" % nom):
            self.db.ExecuterReq(req)
        with DiagnosticPerformance.mesurer("sql_fetch", "ccns_data_reader.%s.resultats" % nom):
            rows = self.db.ResultatReq()
        DiagnosticPerformance.enregistrer_mesure(
            "sql_requetes",
            "ccns_data_reader.%s.nombre" % nom,
            1.0,
            {"lignes": len(rows)},
        )
        return rows

    def lire_contrats(self, limit: Optional[int] = None) -> list[CcnsContratRecord]:
        return self._lire_contrats(where_clause="", limit=limit, nom="contrats")

    def lire_contrats_personne(self, IDpersonne: int, limit: Optional[int] = None) -> list[CcnsContratRecord]:
        where_clause = "WHERE contrats.IDpersonne=%d" % int(IDpersonne)
        return self._lire_contrats(where_clause=where_clause, limit=limit, nom="contrats_personne")

    def _lire_contrats(self, where_clause: str, limit: Optional[int], nom: str) -> list[CcnsContratRecord]:
        req = """
    SELECT
        contrats.IDcontrat,
        contrats.IDpersonne,
        contrats.date_debut,
        contrats.date_fin,
        contrats.salaire_base,
        contrats.temps_hebdo,
        contrats.prime_anciennete,
        individus.prenom,
        individus.nom,
        contrats_class.nom AS classification,
        contrats_types.nom AS type_contrat
    FROM contrats
    LEFT JOIN individus ON individus.IDindividu = contrats.IDpersonne
    LEFT JOIN contrats_class ON contrats_class.IDclassification = contrats.IDclassification
    LEFT JOIN contrats_types ON contrats_types.IDtype = contrats.IDtype
    %s
    ORDER BY contrats.IDcontrat%s;
    """ % (where_clause, self._limit_clause(limit))
        return [CcnsContratRecord(*row) for row in self._fetch(req, nom)]

    def lire_classifications(self) -> list[CcnsClassificationRecord]:
        req = """
    SELECT IDclassification, nom
    FROM contrats_class
    ORDER BY IDclassification;
    """
        return [CcnsClassificationRecord(*row) for row in self._fetch(req, "classifications")]

    def lire_grilles(self, limit: Optional[int] = None) -> list[CcnsGrilleRecord]:
        req = """
    SELECT IDtw_salary_grid, code, label, convention_code, employment_regime_code, effective_date, end_date, source_reference
    FROM tw_salary_grids
    ORDER BY IDtw_salary_grid%s;
    """ % self._limit_clause(limit)
        return [CcnsGrilleRecord(*row) for row in self._fetch(req, "grilles")]

    def lire_lignes_grille(self, IDtw_salary_grid: int) -> list[CcnsLigneGrilleRecord]:
        req = """
    SELECT IDtw_salary_grid_line, IDtw_salary_grid, classification_code, minimum_type, amount, unit,
           age_min, age_max, execution_year_min, execution_year_max, notes
    FROM tw_salary_grid_lines
    WHERE IDtw_salary_grid=%d;
    """ % int(IDtw_salary_grid)
        return [CcnsLigneGrilleRecord(*row) for row in self._fetch(req, "lignes_grille")]

    def close(self) -> None:
        if self._db is not None:
            self._db.Close()
            self._db = None
