from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioRecord:
    IDscenario: int
    IDpersonne: int
    nom: str | None
    description: str | None
    date_debut: object
    date_fin: object


@dataclass(frozen=True)
class TripRecord:
    IDdeplacement: int
    date: object
    objet: str | None
    ville_depart: str | None
    ville_arrivee: str | None
    distance: object
    aller_retour: object
    tarif_km: object
    IDremboursement: object


@dataclass(frozen=True)
class ReimbursementRecord:
    IDremboursement: int
    date: object
    montant: object
    listeIDdeplacement: object


@dataclass(frozen=True)
class PresenceRecord:
    IDpresence: int
    date: object
    heure_debut: object
    heure_fin: object
    IDcategorie: int
    intitule: str | None


@dataclass(frozen=True)
class PresenceCategoryRecord:
    IDcategorie: int
    nom_categorie: str | None
    couleur: str | None


@dataclass(frozen=True)
class VacationPeriodRecord:
    IDperiode: int
    nom: str | None
    annee: object
    date_debut: object
    date_fin: object
