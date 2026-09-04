#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Callable, Optional

from domain.repositories.person_data import (
    PersonCoordinateRecord,
    PersonGeneralitiesRecord,
    PersonIdentityRecord,
)
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

    def lire_generalites(self, IDpersonne) -> PersonGeneralitiesRecord | None:
        """Lit les champs visibles de Généralités sans sélectionner ``num_secu``."""
        person_id = self._person_id(IDpersonne)
        req = (
            "SELECT personnes.IDpersonne, personnes.civilite, personnes.nom, "
            "personnes.nom_jfille, personnes.prenom, personnes.date_naiss, "
            "personnes.cp_naiss, personnes.ville_naiss, pays_naiss.nom, "
            "pays_nation.nationalite, personnes.adresse_resid, personnes.cp_resid, "
            "personnes.ville_resid, personnes.memo, situations.situation "
            "FROM personnes "
            "LEFT JOIN pays AS pays_naiss ON pays_naiss.IDpays=personnes.pays_naiss "
            "LEFT JOIN pays AS pays_nation ON pays_nation.IDpays=personnes.nationalite "
            "LEFT JOIN situations ON situations.IDsituation=personnes.IDsituation "
            "WHERE personnes.IDpersonne=%d;" % person_id
        )
        rows = self._fetch(req, "PersonReader.lire_generalites")
        if not rows:
            return None
        return PersonGeneralitiesRecord(*rows[0])

    def lire_coordonnees(self, IDpersonne) -> list[PersonCoordinateRecord]:
        """Lit la liste historique Fixe/Mobile/Fax/Email de la personne."""
        person_id = self._person_id(IDpersonne)
        req = (
            "SELECT IDcoord, categorie, texte, intitule FROM coordonnees "
            "WHERE IDpersonne=%d ORDER BY IDcoord;" % person_id
        )
        rows = self._fetch(req, "PersonReader.lire_coordonnees")
        return [PersonCoordinateRecord(*row) for row in rows]

    def close(self) -> None:
        if self._db is not None:
            self._db.Close()
            self._db = None
