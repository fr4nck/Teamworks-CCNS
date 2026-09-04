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
