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

    def _fetch(self, req: str):
        self.db.ExecuterReq(req)
        return self.db.ResultatReq()

    def lire_contrats(self, limit: Optional[int] = None) -> list[CcnsContratRecord]:
        req = """
    SELECT
        contrats.IDcontrat,
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
    ORDER BY contrats.IDcontrat;
    """
        if limit:
            req = req.replace("ORDER BY contrats.IDcontrat;", "ORDER BY contrats.IDcontrat LIMIT %d;" % int(limit))
        return [CcnsContratRecord(*row) for row in self._fetch(req)]

    def lire_classifications(self) -> list[CcnsClassificationRecord]:
        req = """
    SELECT IDclassification, nom
    FROM contrats_class
    ORDER BY IDclassification;
    """
        return [CcnsClassificationRecord(*row) for row in self._fetch(req)]

    def lire_grilles(self, limit: Optional[int] = None) -> list[CcnsGrilleRecord]:
        req = """
    SELECT IDtw_salary_grid, code, label, convention_code, employment_regime_code, effective_date, end_date, source_reference
    FROM tw_salary_grids
    ORDER BY IDtw_salary_grid%s;
    """ % (" LIMIT %d" % int(limit) if limit else "")
        return [CcnsGrilleRecord(*row) for row in self._fetch(req)]

    def lire_lignes_grille(self, IDtw_salary_grid: int) -> list[CcnsLigneGrilleRecord]:
        req = """
    SELECT IDtw_salary_grid_line, IDtw_salary_grid, classification_code, minimum_type, amount, unit,
           age_min, age_max, execution_year_min, execution_year_max, notes
    FROM tw_salary_grid_lines
    WHERE IDtw_salary_grid=%d;
    """ % int(IDtw_salary_grid)
        return [CcnsLigneGrilleRecord(*row) for row in self._fetch(req)]

    def close(self) -> None:
        if self._db is not None:
            self._db.Close()
            self._db = None
