#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class CcnsContratRecord:
    IDcontrat: int
    IDpersonne: int
    date_debut: object
    date_fin: object
    salaire_base: Optional[float]
    temps_hebdo: Optional[float]
    prime_anciennete: Optional[float]
    prenom: Optional[str]
    nom: Optional[str]
    classification: Optional[str]
    type_contrat: Optional[str]


@dataclass(frozen=True)
class CcnsClassificationRecord:
    IDclassification: int
    nom: Optional[str]


@dataclass(frozen=True)
class CcnsGrilleRecord:
    IDtw_salary_grid: int
    code: str
    label: str
    convention_code: Optional[str]
    employment_regime_code: Optional[str]
    effective_date: object
    end_date: object
    source_reference: Optional[str]


@dataclass(frozen=True)
class CcnsLigneGrilleRecord:
    IDtw_salary_grid_line: int
    IDtw_salary_grid: int
    classification_code: str
    minimum_type: Optional[str]
    amount: float
    unit: Optional[str]
    age_min: Optional[int]
    age_max: Optional[int]
    execution_year_min: Optional[int]
    execution_year_max: Optional[int]
    notes: Optional[str]


class CcnsDataReaderProtocol(Protocol):
    def lire_contrats(self, limit: Optional[int] = None) -> list[CcnsContratRecord]: ...
    def lire_contrats_personne(self, IDpersonne: int, limit: Optional[int] = None) -> list[CcnsContratRecord]: ...
    def lire_classifications(self) -> list[CcnsClassificationRecord]: ...
    def lire_grilles(self, limit: Optional[int] = None) -> list[CcnsGrilleRecord]: ...
    def lire_lignes_grille(self, IDtw_salary_grid: int) -> list[CcnsLigneGrilleRecord]: ...
    def close(self) -> None: ...
