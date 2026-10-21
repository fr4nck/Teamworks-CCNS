"""Adaptation prudente des contrats historiques Teamworks vers les ETP.

Ne modifie pas la base. Les types inconnus et dates ambiguës bloquent la
validation des résultats au lieu d'être reclassés silencieusement.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Protocol

from domain.effectifs import (
    Anomalie, Categorie, ContratETP, Profil, ResultatETP, calculer_etp,
    profils_comparaison,
)
from domain.repositories.ccns_data import CcnsContratRecord
from infrastructure.persistence.teamworks_contract_conversions import as_date


class LecteurContrats(Protocol):
    def lire_contrats(self, limit: int | None = None) -> list[CcnsContratRecord]: ...


_ALIASES = {
    Categorie.CDI: ("CDI", "CONTRAT A DUREE INDETERMINEE"),
    Categorie.CDD: ("CDD", "CONTRAT A DUREE DETERMINEE"),
    Categorie.CDII: ("CDII", "CDI INTERMITTENT", "CONTRAT DE TRAVAIL INTERMITTENT"),
    Categorie.CEE: ("CEE", "CONTRAT D ENGAGEMENT EDUCATIF", "CONTRAT ENGAGEMENT EDUCATIF"),
    Categorie.APPRENTISSAGE: ("APPRENTISSAGE", "APPRENTICESHIP", "CONTRAT D APPRENTISSAGE"),
    Categorie.PROFESSIONNALISATION: ("PROFESSIONNALISATION", "CONTRAT DE PROFESSIONNALISATION", "CONTRAT PRO"),
    Categorie.STAGE: ("STAGE", "INTERNSHIP", "CONVENTION DE STAGE"),
    Categorie.SERVICE_CIVIQUE: ("SERVICE CIVIQUE", "CIVIC SERVICE"),
}
_TYPES = {label: cat for cat, labels in _ALIASES.items() for label in labels}
_FIN_OBLIGATOIRE = frozenset({
    Categorie.CDD, Categorie.CEE, Categorie.APPRENTISSAGE,
    Categorie.PROFESSIONNALISATION, Categorie.STAGE, Categorie.SERVICE_CIVIQUE,
})


def categorie_historique(libelle: str | None) -> Categorie:
    if libelle is None:
        return Categorie.AUTRE
    base = unicodedata.normalize("NFKD", str(libelle))
    sans_accents = "".join(c for c in base if not unicodedata.combining(c))
    canonique = " ".join(re.findall(r"[A-Z0-9]+", sans_accents.upper()))
    return _TYPES.get(canonique, Categorie.AUTRE)


@dataclass(frozen=True)
class ConversionETP:
    contrats: tuple[ContratETP, ...]
    anomalies: tuple[Anomalie, ...]


def convertir_contrats(records: Iterable[CcnsContratRecord]) -> ConversionETP:
    contrats: list[ContratETP] = []
    anomalies: list[Anomalie] = []
    for row in records:
        try:
            numero = int(row.IDcontrat)
            salarie = int(row.IDpersonne)
            if numero <= 0 or salarie <= 0:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            anomalies.append(Anomalie("IDENTIFIANTS_INVALIDES", str(row.IDcontrat), "Identifiants source invalides"))
            continue
        ident = str(numero)
        categorie = categorie_historique(row.type_contrat)
        if categorie is Categorie.AUTRE:
            anomalies.append(Anomalie("TYPE_NON_QUALIFIE", ident, "Type historique inconnu : %r" % row.type_contrat))
            continue
        debut = as_date(row.date_debut)
        if debut is None:
            anomalies.append(Anomalie("DATE_DEBUT_INVALIDE", ident, "Date de début absente ou illisible"))
            continue
        fin = as_date(row.date_fin)
        if row.date_fin not in (None, "") and fin is None:
            anomalies.append(Anomalie("DATE_FIN_INVALIDE", ident, "Date de fin illisible"))
            continue
        if fin is None and categorie in _FIN_OBLIGATOIRE:
            anomalies.append(Anomalie("FIN_CONTRAT_MANQUANTE", ident, "Date de fin manquante pour contrat à durée limitée"))
            continue
        heures: Decimal | None = None
        if row.temps_hebdo is not None and str(row.temps_hebdo).strip():
            try:
                heures = Decimal(str(row.temps_hebdo))
                if not heures.is_finite() or heures <= 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                anomalies.append(Anomalie("HEURES_INVALIDES", ident, "Durée hebdomadaire invalide"))
                continue
        try:
            contrats.append(ContratETP(
                id_contrat=ident, id_salarie=str(salarie), categorie=categorie,
                debut=debut, fin=fin, heures_hebdo=heures,
                # La lecture historique ne contient pas le motif de remplacement.
                remplace_absent=None,
            ))
        except ValueError as exc:
            anomalies.append(Anomalie("CONTRAT_INVALIDE", ident, str(exc)))
    return ConversionETP(tuple(contrats), tuple(anomalies))


def comparer_depuis_teamworks(
    lecteur: LecteurContrats,
    annee: int,
    profils: Iterable[Profil] | None = None,
) -> tuple[ResultatETP, ...]:
    """Lecture unique des contrats; aucune écriture SQL et aucun import wx."""
    conversion = convertir_contrats(lecteur.lire_contrats())
    choix = tuple(profils) if profils is not None else profils_comparaison()
    return tuple(calculer_etp(conversion.contrats, annee, profil, conversion.anomalies) for profil in choix)
