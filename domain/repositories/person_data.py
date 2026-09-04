#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PersonIdentityRecord:
    """Identité minimale utilisée par les listes de sélection historiques."""

    IDpersonne: int
    nom: str
    prenom: str

    def __iter__(self):
        # Compatibilité avec les écrans historiques qui dépaquettent les tuples SQL.
        yield self.IDpersonne
        yield self.nom
        yield self.prenom


@dataclass(frozen=True)
class PersonGeneralitiesRecord:
    """Projection de lecture de la page Généralités, sans donnée NIR."""

    IDpersonne: int
    civilite: str | None
    nom: str | None
    nom_jfille: str | None
    prenom: str | None
    date_naiss: object | None
    cp_naiss: object | None
    ville_naiss: str | None
    pays_naiss: str | None
    nationalite: str | None
    adresse_resid: str | None
    cp_resid: object | None
    ville_resid: str | None
    memo: str | None
    situation: str | None


@dataclass(frozen=True)
class PersonCoordinateRecord:
    """Coordonnée historique visible dans la liste de la fiche individuelle."""

    IDcoord: int
    categorie: str | None
    texte: str | None
    intitule: str | None


class PersonReaderProtocol(Protocol):
    def lire_identites(self) -> list[PersonIdentityRecord]:
        ...

    def lire_generalites(self, IDpersonne) -> PersonGeneralitiesRecord | None:
        ...

    def lire_coordonnees(self, IDpersonne) -> list[PersonCoordinateRecord]:
        ...
